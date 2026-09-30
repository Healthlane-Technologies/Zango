import { Fragment, useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { useQueries, useQueryClient } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import {
	agentKeys,
	requirementQuery,
	useApproveRequirement,
	useAvailability,
	useCreateRequirement,
	useRequirements,
	useSaveSpec,
	useSendMessage,
	useTemplateBuilder,
} from '@/api/agentMode';
import { useAppId } from '@/api/hooks';
import { Badge, Button, cx, ErrorState, Icon, Skeleton, Tabs, TemplateBadge } from '@/ui';
import { RequirementsPanel } from './agent/RequirementsPanel';
import { TemplateBuilderHost } from './agent/builder/TemplateBuilderHost';
import type { SpecDraftController } from './agent/builder/useSpecDraft';
import { RunsPanel } from './agent/runs/RunsPanel';
import { Thread } from './agent/Thread';
import { STAGES, roundLabel, stageOf, type Round } from './agent/rounds';
import { specHighlights } from './agent/specHighlights';
import './agent/agent.css';

// Why Agent Mode can't run for this app (availability.py reasons), in the classic panel's words.
const REASON_TEXT: Record<string, string> = {
	feature_disabled: 'Build with AI is disabled. Set AGENT_MODE_ENABLED=True.',
	sdk_not_installed: 'The Claude Agent SDK is not installed on the server.',
	cli_not_found: 'The Claude Code binary could not be found.',
	no_credentials: 'No Anthropic API key is configured for the platform.',
	skill_plugin_missing: 'The Zango skill plugin is missing from the install.',
	workspace_missing: 'This app has no workspace directory on disk.',
	app_suspended: 'This app is suspended.',
	no_worker: 'No Celery worker is consuming the agent_mode queue.',
};

type PanelTab = 'requirements' | 'builds';

const CHAT_COLLAPSED_KEY = 'console.agent.chatCollapsed';

function readCollapsed(): boolean {
	try {
		return window.localStorage.getItem(CHAT_COLLAPSED_KEY) === '1';
	} catch {
		return false;
	}
}

function writeCollapsed(on: boolean) {
	try {
		window.localStorage.setItem(CHAT_COLLAPSED_KEY, on ? '1' : '0');
	} catch {
		// Private windows and blocked storage: the choice just isn't remembered.
	}
}

/** Resolve true when the mutation succeeded; useApiMutation has already toasted any error. */
async function attempt(p: Promise<unknown>): Promise<boolean> {
	try {
		await p;
		return true;
	} catch {
		return false;
	}
}

export function AgentPage() {
	const appId = useAppId();
	const qc = useQueryClient();
	const [params, setParams] = useSearchParams();
	const { data: availability } = useAvailability(appId);
	const list = useRequirements(appId);

	// Every round lives in one thread, oldest first, like any conversation.
	const summaries = useMemo(
		() =>
			[...(list.data ?? [])].sort((a, b) => Date.parse(a.created_at) - Date.parse(b.created_at)),
		[list.data],
	);
	const details = useQueries({ queries: summaries.map((s) => requirementQuery(appId, s.uuid)) });
	const rounds: Round[] = summaries.map((summary, index) => ({
		index,
		summary,
		detail: details[index]?.data,
	}));
	const activeRound = rounds[rounds.length - 1] as Round | undefined;
	const active = activeRound?.detail;
	const activeId = activeRound?.summary.uuid ?? '';

	// The panel shows ?round= if set, else the newest, so starting a round never leaves a stale spec on screen.
	const viewed = rounds.find((r) => r.summary.uuid === params.get('round')) ?? activeRound;
	const viewingActive = !!viewed && viewed.summary.uuid === activeId;
	const tab: PanelTab = params.get('tab') === 'builds' ? 'builds' : 'requirements';
	const setView = (next: { round?: string | null; tab?: PanelTab }) =>
		setParams(
			(p) => {
				const out = new URLSearchParams(p);
				if (next.round !== undefined) {
					if (next.round && next.round !== activeId) out.set('round', next.round);
					else out.delete('round');
				}
				if (next.tab === 'builds') out.set('tab', 'builds');
				else if (next.tab === 'requirements') out.delete('tab');
				return out;
			},
			{ replace: true },
		);

	// Unsaved spec edits belong to the active round; drop them when a new round starts.
	const [draft, setDraft] = useState<string | null>(null);
	useEffect(() => setDraft(null), [activeId]);
	const [focusSignal, setFocusSignal] = useState(0);
	// The template builder's unsaved edits: saved before a message goes out or the spec is approved,
	// so the agent (and the approval) always see what's on screen.
	const templateDraft = useRef<SpecDraftController | null>(null);
	const onController = useCallback((c: SpecDraftController) => {
		templateDraft.current = c;
	}, []);
	const flushTemplate = async () =>
		templateDraft.current?.dirty ? templateDraft.current.flush() : true;

	// A template that ships its own builder (Journey Studio…) gets the builder-first layout:
	// the builder takes the width, the chat a narrow column that can fold to a rail.
	const viewedTemplate = viewed?.detail?.template ?? active?.template ?? null;
	const builderDef = useTemplateBuilder(viewedTemplate?.slug, viewedTemplate?.version_uuid);
	const builderFirst = !!builderDef.data?.builder_url;
	const [chatCollapsed, setChatCollapsed] = useState(readCollapsed);
	const toggleChat = () =>
		setChatCollapsed((on) => {
			writeCollapsed(!on);
			return !on;
		});
	const folded = builderFirst && chatCollapsed;

	const create = useCreateRequirement(appId, () => setView({ round: null, tab: 'requirements' }));
	const sendMessage = useSendMessage(appId, activeId);
	const saveSpec = useSaveSpec(appId, activeId);
	const approve = useApproveRequirement(appId, activeId);

	const blocked = availability ? !availability.available : false;
	const open = active?.status === 'gathering' || active?.status === 'ready';
	const { stage, failed } = stageOf(active);
	const stageIdx = activeRound ? STAGES.findIndex(([k]) => k === stage) : -1;
	const lastAssistant = [...(active?.messages ?? [])].reverse().find((m) => m.role === 'assistant');
	const openQuestions = open && !active?.is_thinking ? (lastAssistant?.questions.length ?? 0) : 0;
	const spec = draft ?? active?.spec_markdown ?? '';
	// A template spec can't be approved while the agent is still filling it in, or with errors;
	// the server refuses both, so say why up front.
	const templateBlock = active?.template
		? active.spec_is_draft
			? 'Mark the spec as ready (or let the agent finish) first'
			: (active.validation_issues ?? []).some((i) => i.level === 'error')
				? 'Fix the problems in Checks first'
				: null
		: null;

	// Approving locks the spec; the build itself starts from the Builds tab (RunsPanel owns runs).
	const onApprove = async () => {
		if (active?.template && !(await flushTemplate())) return;
		if (
			draft !== null &&
			draft !== active?.spec_markdown &&
			!(await attempt(saveSpec.mutateAsync(draft)))
		)
			return;
		if (await attempt(approve.mutateAsync())) {
			setDraft(null);
			setView({ round: null, tab: 'builds' });
		}
	};
	const onRunChange = () => {
		qc.invalidateQueries({ queryKey: agentKeys.requirements(appId) });
		qc.invalidateQueries({ queryKey: agentKeys.availability(appId) });
	};

	if (list.error) {
		return (
			<div className="page">
				<div className="card">
					<ErrorState error={list.error} onRetry={() => list.refetch()} />
				</div>
			</div>
		);
	}

	let actions: ReactNode = null;
	if (active && open) {
		actions = (
			<>
				{openQuestions > 0 && (
					<span className="text-[12px] text-t3">
						{openQuestions} open question{openQuestions > 1 ? 's' : ''}
					</span>
				)}
				<Button
					variant="primary"
					icon="check"
					disabled={blocked || active.is_thinking || !spec.trim() || !!templateBlock}
					loading={approve.isPending || saveSpec.isPending}
					onClick={onApprove}
					title={
						templateBlock ??
						(spec.trim() ? undefined : 'The agent hasn’t written a spec to approve yet')
					}
				>
					Approve requirements
				</Button>
			</>
		);
	} else if (active) {
		actions = (
			<>
				<Button icon="plus" onClick={() => setFocusSignal((n) => n + 1)} disabled={blocked}>
					New change
				</Button>
				{tab !== 'builds' && active.status === 'approved' && (
					<Button
						variant="primary"
						icon="rocket"
						onClick={() => setView({ round: null, tab: 'builds' })}
					>
						{stage === 'approved' ? 'Go to build' : 'View builds'}
					</Button>
				)}
			</>
		);
	}

	// A template spec is YAML; the Markdown highlight count means nothing for it.
	const reqCount =
		viewed?.detail && !viewed.detail.template
			? specHighlights(viewed.detail.spec_markdown).groups.reduce((n, g) => n + g.items.length, 0)
			: 0;

	return (
		<div className="ws">
			<div className="wsh">
				<h2>Agent</h2>
				{activeRound && (
					<Badge tone="line" className="!font-medium">
						{roundLabel(activeRound.index)}
					</Badge>
				)}
				{active?.template && <TemplateBadge template={active.template} />}
				<div className="stepline" aria-label="Progress">
					{STAGES.map(([k, label], i) => (
						<Fragment key={k}>
							{i > 0 && <span className="ar">›</span>}
							<span
								className={cx(
									i < stageIdx && 'done',
									i === stageIdx && 'cur',
									i === stageIdx && failed && 'bad',
								)}
								aria-current={i === stageIdx ? 'step' : undefined}
							>
								{i < stageIdx ? (
									<Icon name="check" size={13} weight={2.6} />
								) : i === stageIdx ? (
									<i className="cd" />
								) : null}
								{k === 'build' && failed ? 'Build failed' : label}
							</span>
						</Fragment>
					))}
				</div>
				<div className="r">{actions}</div>
			</div>

			{blocked && availability && (
				<div className="ws-alert" role="status">
					<Icon name="alert" className="mt-[2px]" />
					<div>
						<b className="font-[550]">Build with AI isn’t ready for this app</b>
						<ul className="mt-0.5 list-disc pl-4">
							{availability.reasons.map((r) => (
								<li key={r}>{REASON_TEXT[r] ?? r}</li>
							))}
						</ul>
					</div>
				</div>
			)}

			<div className={cx('split', builderFirst && 'builder-first', folded && 'chat-folded')}>
				{folded && (
					<aside className="chat-rail" aria-label="Conversation (hidden)">
						<button
							type="button"
							className="ib"
							onClick={toggleChat}
							aria-label="Show chat"
							title="Show chat"
						>
							<Icon name="back" className="rotate-180" />
						</button>
						<span className="chat-rail-label">Chat</span>
						{active?.is_thinking && <span className="spin" aria-label="Agent is replying" />}
					</aside>
				)}
				{list.isLoading ? (
					<section className="chat">
						<div className="thread">
							{[70, 45, 80].map((w, i) => (
								<Skeleton key={i} width={`${w}%`} height={14} />
							))}
						</div>
					</section>
				) : (
					<Thread
						rounds={rounds}
						active={active}
						enabled={!blocked}
						sending={sendMessage.isPending || create.isPending}
						onSend={async (c) =>
							(!active?.template || (await flushTemplate())) && attempt(sendMessage.mutateAsync(c))
						}
						onNewRound={(p) => attempt(create.mutateAsync(p))}
						onOpenBuild={(uuid) => setView({ round: uuid, tab: 'builds' })}
						focusSignal={focusSignal}
					/>
				)}

				<section className="panel" aria-label="Requirements and builds">
					<div className="tabs items-center">
						{builderFirst && !folded && (
							<button
								type="button"
								className="ib mr-1"
								onClick={toggleChat}
								aria-label="Hide chat"
								title="Hide chat"
							>
								<Icon name="back" />
							</button>
						)}
						<Tabs<PanelTab>
							className="!border-0 !p-0"
							value={tab}
							onChange={(t) => setView({ tab: t })}
							items={[
								{ value: 'requirements', label: 'Requirements', count: reqCount || undefined },
								{
									value: 'builds',
									label: 'Builds',
									count: viewed?.summary.run_count || undefined,
									disabled: !viewed,
								},
							]}
						/>
						{rounds.length > 1 && viewed && (
							<div className="rounds">
								<select
									className="select h-7 w-auto max-w-[320px] py-0 text-[12px]"
									aria-label="Round"
									value={viewed.summary.uuid}
									onChange={(e) => setView({ round: e.target.value })}
								>
									{[...rounds].reverse().map((r) => (
										<option key={r.summary.uuid} value={r.summary.uuid}>
											{roundLabel(r.index)} — {r.summary.title.slice(0, 48)}
										</option>
									))}
								</select>
							</div>
						)}
					</div>
					<div className={cx('pbody', builderFirst && tab === 'requirements' && 'fill')}>
						<div className="pbody-in">
							{!viewed ? (
								<div className="card">
									<div className="empty">
										<b>Nothing agreed yet</b>
										Describe what you want in the chat. The agent writes it up here for you to
										approve before anything is built.
									</div>
								</div>
							) : !viewed.detail ? (
								<div className="grid gap-3">
									<Skeleton width="40%" height={18} />
									<Skeleton height={64} />
									<Skeleton height={140} />
								</div>
							) : tab === 'builds' ? (
								<RunsPanel
									appId={appId}
									requirementId={viewed.summary.uuid}
									canBuild={viewingActive && viewed.detail.can_build && !blocked}
									onRunChange={onRunChange}
								/>
							) : (
								(() => {
									const detail = viewed.detail;
									const markdown = () => (
										<RequirementsPanel
											key={viewed.summary.uuid}
											requirement={detail}
											editable={viewingActive && open}
											draft={viewingActive ? draft : null}
											onDraft={setDraft}
											onSave={() =>
												draft !== null &&
												saveSpec.mutate(draft, { onSuccess: () => setDraft(null) })
											}
											saving={saveSpec.isPending}
										/>
									);
									return detail.template ? (
										<TemplateBuilderHost
											key={viewed.summary.uuid}
											appId={appId}
											requirement={detail}
											fallback={markdown}
											editable={viewingActive && open && !blocked}
											onController={viewingActive ? onController : undefined}
										/>
									) : (
										markdown()
									);
								})()
							)}
						</div>
					</div>
				</section>
			</div>
		</div>
	);
}
