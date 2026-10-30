import { Fragment, useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { useQueries, useQueryClient } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { parse as parseYaml } from 'yaml';
import {
	agentKeys,
	requirementQuery,
	documentUrl,
	useApproveRequirement,
	useAvailability,
	useCommitRequirement,
	useCreateRequirement,
	useRequirements,
	useRequirementSpec,
	useSaveSpec,
	useSendMessage,
	useTemplateBuilder,
	type NewRoundInput,
	type PreviewFocus,
} from '@/api/agentMode';
import { useStartRun } from '@/api/agentRuns';
import { useAppId } from '@/api/hooks';
import { ApiError } from '@/api/client';
import {
	Badge,
	Button,
	ConfirmModal,
	cx,
	ErrorState,
	Icon,
	Skeleton,
	Tabs,
	TemplateBadge,
	toast,
} from '@/ui';
import { NewChangeModal } from './agent/NewChangeModal';
import { RequirementsPanel } from './agent/RequirementsPanel';
import { humanPath } from './agent/builder/labels';
import { starterIsPlaceholder, usePreviewStage } from './agent/builder/generating';
import { Decisions } from './agent/builder/ReviewPanel';
import type { Schema } from './agent/builder/schema';
import { TemplateBuilderHost } from './agent/builder/TemplateBuilderHost';
import { PREVIEW_CHANNEL } from './agent/previewChannel';
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

// Preview-first apps: you preview the app, then commit it for build.
const PREVIEW_STAGE_LABEL: Record<string, string> = {
	requirements: 'Preview',
	approved: 'Committed',
};

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

	// A template with a preview page (its own, or the generic App Studio) gets the preview-first
	// layout: the app's live preview takes the width, the chat a column that can fold to a rail.
	const viewedTemplate = viewed?.detail?.template ?? active?.template ?? null;
	const builderDef = useTemplateBuilder(viewedTemplate?.slug, viewedTemplate?.version_uuid);
	const builderFirst = !!(builderDef.data?.preview_url ?? builderDef.data?.builder_url);
	const [chatCollapsed, setChatCollapsed] = useState(readCollapsed);
	const toggleChat = () =>
		setChatCollapsed((on) => {
			writeCollapsed(!on);
			return !on;
		});
	const folded = builderFirst && chatCollapsed;

	const create = useCreateRequirement(appId, () => setView({ round: null, tab: 'requirements' }));
	// Template apps start a change from a brief and/or documents (one-pass draft).
	const [changeOpen, setChangeOpen] = useState(false);
	const activeBuilder = useTemplateBuilder(active?.template?.slug, active?.template?.version_uuid);
	// Shares the panel's cache (same key), so this costs no extra request.
	const activeSpec = useRequirementSpec(appId, active?.template ? activeId : undefined, {
		draft: active?.draft_revision,
		version: active?.spec_version,
		status: active?.status,
		turns: active?.turns,
		thinking: active?.is_thinking,
	});
	const decisions = activeSpec.data?.open_decisions ?? [];
	const openDecisions = decisions.length;
	// With a preview pane the agent's open decisions are asked in the chat, not in the pane.
	const decisionsInChat = !!(activeBuilder.data?.preview_url ?? activeBuilder.data?.builder_url);
	const activeDoc = useMemo(() => {
		if (!decisionsInChat || !openDecisions) return undefined;
		try {
			return parseYaml(activeSpec.data?.text ?? '') as unknown;
		} catch {
			return undefined;
		}
	}, [decisionsInChat, openDecisions, activeSpec.data?.text]);
	// "Show me" on a decision: the pane opens the spec at that place.
	const [specJump, setSpecJump] = useState<{ pointer: string; nonce: number } | null>(null);
	const sendMessage = useSendMessage(appId, activeId);
	// Where the user is in the preview goes with each message; after "Point", what they clicked
	// (shown above the composer until it is sent or dismissed). The full-page preview, in another
	// tab, points through a BroadcastChannel.
	const place = useRef<PreviewFocus | null>(null);
	const [pointer, setPointer] = useState<PreviewFocus | null>(null);
	useEffect(() => {
		place.current = null;
		setPointer(null);
	}, [activeId]);
	const onPreviewFocus = useCallback((focus: PreviewFocus) => {
		if (focus.pointed) setPointer(focus);
		else place.current = focus;
	}, []);
	useEffect(() => {
		if (!activeId || typeof BroadcastChannel === 'undefined') return;
		const channel = new BroadcastChannel(PREVIEW_CHANNEL);
		channel.onmessage = (e: MessageEvent<{ reqId?: string; focus?: PreviewFocus }>) => {
			if (e.data?.reqId === activeId && e.data.focus?.pointed) setPointer(e.data.focus);
		};
		return () => channel.close();
	}, [activeId]);
	const sendReply = async (content: string, documents: File[] = []) => {
		const ok = await attempt(
			sendMessage.mutateAsync({ content, focus: pointer ?? place.current, documents }),
		);
		if (ok) setPointer(null);
		return ok;
	};
	const saveSpec = useSaveSpec(appId, activeId);
	const approve = useApproveRequirement(appId, activeId);
	const commit = useCommitRequirement(appId, activeId);
	// Preview-first apps commit the previewed app and start its build in one step
	// (finalize + approve, then a run). The Builds tab picks the new run up on refetch.
	const startBuild = useStartRun(appId, activeId, () => {
		qc.invalidateQueries({ queryKey: agentKeys.requirements(appId) });
		qc.invalidateQueries({ queryKey: agentKeys.availability(appId) });
	});
	const previewFlow = decisionsInChat;
	const [confirmCommit, setConfirmCommit] = useState(false);
	const [sheetSignal, setSheetSignal] = useState<{ sheet: 'checks'; nonce: number } | null>(null);
	const pvStage = usePreviewStage({
		thinking: !!active?.is_thinking,
		text: activeSpec.data?.text ?? active?.spec_markdown ?? '',
		starter: activeBuilder.data?.starter_yaml,
		draftRevision: activeSpec.data?.draft_revision ?? active?.draft_revision ?? 0,
		yamlBroken: (activeSpec.data?.issues ?? []).some((i) => i.code === 'yaml'),
		placeholderStarter: !!active && starterIsPlaceholder(activeBuilder.data),
		isDraft: activeSpec.data?.is_draft ?? active?.spec_is_draft,
	});
	const generating = pvStage === 'generating';
	const awaitingAnswers = pvStage === 'awaiting';

	const blocked = availability ? !availability.available : false;
	const open = active?.status === 'gathering' || active?.status === 'ready';
	const { stage, failed, waiting: buildWaiting } = stageOf(active);
	const stageIdx = activeRound ? STAGES.findIndex(([k]) => k === stage) : -1;
	const lastAssistant = [...(active?.messages ?? [])].reverse().find((m) => m.role === 'assistant');
	const openQuestions = open && !active?.is_thinking ? (lastAssistant?.questions.length ?? 0) : 0;
	const spec = draft ?? active?.spec_markdown ?? '';
	// A template spec can't be approved while the agent is still filling it in, or with errors;
	// the server refuses both, so say why up front.
	const templateBlock = active?.template
		? openDecisions > 0
			? `Answer the ${openDecisions} open decision${openDecisions > 1 ? 's' : ''} ${decisionsInChat ? 'in the chat' : 'in Review'} first`
			: active.spec_is_draft
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
	const commitBlocked = !active
		? 'Nothing to commit yet'
		: blocked
			? 'Build with AI isn’t ready for this app'
			: generating
				? 'The agent is still generating the preview'
				: awaitingAnswers
					? 'Answer the agent’s questions first: there is no preview to commit yet'
					: active.is_thinking
						? 'The agent is updating the preview'
						: openDecisions > 0
							? `Answer the ${openDecisions} open decision${openDecisions > 1 ? 's' : ''} in the chat first`
							: !(activeSpec.data?.text ?? active.spec_markdown ?? '').trim()
								? 'The agent hasn’t generated a preview yet'
								: null;
	const showDecisionsCard = () => {
		const el = document.getElementById('agent-decisions');
		if (!el) return;
		el.scrollIntoView({ block: 'center', behavior: 'smooth' });
		el.classList.remove('bv-flash');
		void el.offsetWidth;
		el.classList.add('bv-flash');
		window.setTimeout(() => el.classList.remove('bv-flash'), 1600);
	};
	// Commit for build is one click: it commits and starts the build. When the server finds
	// unfinished custom work, the agent finishes it and the commit runs again by itself once
	// the agent's turn ends (once).
	const commitAfterTurn = useRef<'off' | 'waiting' | 'running'>('off');
	const autoCommitted = useRef(false);
	useEffect(() => {
		commitAfterTurn.current = 'off';
		autoCommitted.current = false;
	}, [activeId]);
	const onCommit = async () => {
		if (!(await flushTemplate())) return;
		// Saving edits moves the revision on; commit against what the server now holds.
		const fresh = await qc.fetchQuery({ ...requirementQuery(appId, activeId), staleTime: 0 });
		try {
			await commit.mutateAsync(fresh.draft_revision ?? 0);
		} catch (err) {
			setConfirmCommit(false);
			const status = err instanceof ApiError ? err.status : 0;
			const raw = (err instanceof ApiError ? err.body : null) as Record<string, unknown> | null;
			const detail = ((raw?.response as Record<string, unknown> | undefined) ?? raw ?? {}) as {
				open_decisions?: unknown[];
				issues?: unknown[];
				agent_prompt?: string;
				message?: string;
			};
			const unfinished = status === 409 && !detail.open_decisions?.length && !!detail.issues?.length;
			if (unfinished && !autoCommitted.current) {
				// Unfinished custom work (no sketch, no contract), or what the approved prototype shows and
				// the spec leaves out: the agent finishes it, not the user.
				const items = (detail.issues as { path?: string; message?: string }[])
					.map((i) => `- ${i.path}: ${i.message}`)
					.join('\n');
				autoCommitted.current = true;
				const brief = detail.agent_prompt ?? 'Before building, finish these custom parts:';
				if (await sendReply(`${brief}\n${items}`)) {
					commitAfterTurn.current = 'waiting';
					toast.success(
						detail.agent_prompt
							? 'The agent is adding what the spec leaves out of the prototype. The build will start when it is done.'
							: 'The agent is finishing a few custom parts. The build will start when it is done.',
					);
				}
				return;
			}
			toast.error((err as Error).message);
			if (status === 400 && detail.issues?.length) {
				setView({ round: null, tab: 'requirements' });
				setSheetSignal({ sheet: 'checks', nonce: Date.now() });
			} else if (status === 409 && detail.open_decisions?.length) {
				window.setTimeout(showDecisionsCard, 60);
			}
			return;
		}
		setConfirmCommit(false);
		setView({ round: null, tab: 'builds' });
		// The commit stands even if the build can't start (another build running): useStartRun
		// says so and the Builds tab keeps its Start build button.
		startBuild.mutate();
	};
	const thinking = !!active?.is_thinking;
	useEffect(() => {
		if (commitAfterTurn.current === 'waiting' && thinking) commitAfterTurn.current = 'running';
		else if (commitAfterTurn.current === 'running' && !thinking) {
			commitAfterTurn.current = 'off';
			void onCommit();
		}
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [thinking]);
	const commitAction = previewFlow
		? {
				onClick: () => setConfirmCommit(true),
				blocked: commitBlocked,
				loading: commit.isPending || startBuild.isPending,
			}
		: undefined;

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
	if (active && open && previewFlow) {
		actions = (
			<Button
				variant="primary"
				icon="rocket"
				disabled={!!commitBlocked}
				loading={commit.isPending || startBuild.isPending}
				onClick={() => setConfirmCommit(true)}
				title={commitBlocked ?? 'Build the app exactly as previewed'}
			>
				Commit for build
			</Button>
		);
	} else if (active && open) {
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
				<Button
					icon="plus"
					onClick={() => (active.template ? setChangeOpen(true) : setFocusSignal((n) => n + 1))}
					disabled={blocked}
				>
					New change
				</Button>
				{tab !== 'builds' && active.status === 'approved' && (
					<Button
						variant="primary"
						icon="rocket"
						onClick={() => setView({ round: null, tab: 'builds' })}
					>
						{stage === 'approved'
							? previewFlow
								? 'Start the build'
								: 'Go to build'
							: 'View builds'}
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

	// A new change carries what the user pointed at (or where they were) in the preview, like a reply.
	const newChange = async (input: NewRoundInput) => {
		const focus = pointer ?? place.current;
		const ok = await attempt(
			create.mutateAsync(typeof input === 'string' ? { prompt: input, focus } : { ...input, focus }),
		);
		if (ok) setPointer(null);
		return ok;
	};

	const decisionsCard =
		decisionsInChat && open && openDecisions > 0 && active ? (
			<Decisions
				inChat
				appId={appId}
				reqId={activeId}
				decisions={decisions}
				canAct={!blocked && !active.is_thinking}
				thinking={active.is_thinking}
				flush={async () => !!(await flushTemplate())}
				whereOf={(p) => {
					if (!p) return 'The whole spec';
					const schema = activeBuilder.data?.json_schema as Schema | undefined;
					try {
						return schema && activeDoc !== undefined ? humanPath(schema, activeDoc, p) : p;
					} catch {
						return p;
					}
				}}
				onShowInYaml={(pointer) => {
					setView({ round: null, tab: 'requirements' });
					setSpecJump({ pointer, nonce: Date.now() });
				}}
			/>
		) : null;

	return (
		<div className="ws">
			<ConfirmModal
				open={confirmCommit}
				onOpenChange={setConfirmCommit}
				title="Commit this preview for build?"
				confirmLabel="Commit for build"
				loading={commit.isPending || startBuild.isPending}
				onConfirm={onCommit}
			>
				<p className="text-[13px] leading-[1.55] text-t2">
					The build starts right away and the app is built exactly as previewed. You can still
					change it later with a new change request.
				</p>
			</ConfirmModal>
			<NewChangeModal
				open={changeOpen}
				onOpenChange={setChangeOpen}
				references={activeBuilder.data?.references}
				onSubmit={newChange}
			/>
			<div className="wsh">
				<h2>Agent</h2>
				{activeRound && (
					<Badge tone="line" className="!font-medium">
						{roundLabel(activeRound.index)}
					</Badge>
				)}
				{active?.template && <TemplateBadge template={active.template} />}
				<div className="stepline" aria-label="Progress">
					{STAGES.map(([k, classic], i) => {
						const label = previewFlow ? (PREVIEW_STAGE_LABEL[k] ?? classic) : classic;
						return (
							<Fragment key={k}>
								{i > 0 && <span className="ar">›</span>}
								<span
									className={cx(
										i < stageIdx && 'done',
										i === stageIdx && 'cur',
										i === stageIdx && failed && 'bad',
										i === stageIdx && k === 'build' && buildWaiting && 'wait',
									)}
									aria-current={i === stageIdx ? 'step' : undefined}
								>
									{i < stageIdx ? (
										<Icon name="check" size={13} weight={2.6} />
									) : i === stageIdx ? (
										<i className="cd" />
									) : null}
									{k === 'build' && failed
										? 'Build failed'
										: k === 'build' && buildWaiting && i === stageIdx
											? 'Waiting for you'
											: label}
								</span>
							</Fragment>
						);
					})}
				</div>
				<div className="r">{actions}</div>
			</div>

			{buildWaiting && tab !== 'builds' && (
				<div className="ws-alert" role="status">
					<Icon name="alert" className="mt-[2px]" />
					<div className="flex flex-1 flex-wrap items-center gap-x-3 gap-y-1">
						<span>
							<b className="font-[550]">The build is waiting for you.</b> It paused for something
							only you can do, and continues once that is done.
						</span>
						<Button size="xs" onClick={() => setView({ round: null, tab: 'builds' })}>
							See what's needed
						</Button>
					</div>
				</div>
			)}

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
						onSend={async (c, files) =>
							(!active?.template || (await flushTemplate())) && sendReply(c, files)
						}
						onNewRound={(prompt, files) =>
							newChange(files.length ? { prompt, documents: files } : prompt)
						}
						documentUrl={(reqUuid, id) => documentUrl(appId, reqUuid, id)}
						onOpenBuild={(uuid) => setView({ round: uuid, tab: 'builds' })}
						focusSignal={focusSignal}
						pointer={pointer}
						onClearPointer={() => setPointer(null)}
						agentCard={
							decisionsCard && (
								<div id="agent-decisions" className="rounded-[12px]">
									{decisionsCard}
								</div>
							)
						}
						idlePlaceholder={
							previewFlow && !generating && !awaitingAnswers
								? 'Ask for changes to the preview…'
								: undefined
						}
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
								{
									value: 'requirements',
									label: builderFirst ? 'Preview' : 'Requirements',
									count: reqCount || undefined,
								},
								{
									value: 'builds',
									label: 'Builds',
									count: viewed?.summary.run_count || undefined,
									disabled: !viewed,
									attention: viewed?.detail?.runs[0]?.status === 'waiting',
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
											jump={viewingActive ? specJump : null}
											commit={viewingActive && open ? commitAction : undefined}
											sheet={viewingActive ? sheetSignal : null}
											// Once approved, what the user points at starts the next change.
											onPreviewFocus={viewingActive ? onPreviewFocus : undefined}
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
