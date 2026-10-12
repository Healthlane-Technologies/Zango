// Contract between the Agent workspace (AgentPage) and the build side.
// AgentPage renders <RunsPanel> for the selected requirement; this module owns everything
// about runs: starting one, the live event stream, usage/cost, the app-ready card, and
// deploy/share. Keep the props stable; add optional ones only.
import { useCallback, useMemo, useState } from 'react';
import { isRunActive, useRequirement, type RunRef, type RunStatus } from '@/api/agentMode';
import { useQueryClient } from '@tanstack/react-query';
import { agentKeys } from '@/api/agentMode';
import {
	checksOf,
	useInvalidateRuns,
	useResumeRun,
	useRunSummaries,
	useStartRun,
	type RunDetail,
} from '@/api/agentRuns';
import { formatDateTime, timeAgo } from '@/format/time';
import { Badge, Button, Card, cx, EmptyState, ErrorState, Skeleton } from '@/ui';
import { fmtCost, fmtDuration, runStatus } from './format';
import { ChecksChip } from './RunChecks';
import { RunView } from './RunView';
import './runs.css';

export interface RunsPanelProps {
	appId: string;
	/** The requirement (AgentRequirement uuid) whose runs to show. */
	requirementId: string;
	/** Whether the requirement can be built now (AgentRequirement.can_build). */
	canBuild: boolean;
	/** Called when a run starts or finishes, so the page can refetch the requirement. */
	onRunChange?: () => void;
	/** App name for the share/deploy text. Defaults to the requirement's title. */
	appName?: string;
}

export function RunsPanel({
	appId,
	requirementId,
	canBuild,
	onRunChange,
	appName,
}: RunsPanelProps) {
	const { data: requirement, isLoading, error, refetch } = useRequirement(appId, requirementId);
	const { data: summaries } = useRunSummaries(appId);
	const invalidate = useInvalidateRuns(appId, requirementId);
	const qc = useQueryClient();
	const [selected, setSelected] = useState<string | null>(null);
	// Live statuses reported by the run being watched; fresher than the requirement's refs.
	const [live, setLive] = useState<Record<string, RunStatus>>({});

	const refs: RunRef[] = useMemo(() => requirement?.runs ?? [], [requirement?.runs]);
	const byId = useMemo(() => new Map((summaries ?? []).map((s) => [s.uuid, s])), [summaries]);
	// A run just started may not be in the requirement's refs until the refetch lands.
	const current = selected ?? refs[0]?.uuid ?? null;
	const statusOf = (r: RunRef) => live[r.uuid] ?? byId.get(r.uuid)?.status ?? r.status;
	const inFlight = refs.some((r) => isRunActive(statusOf(r)));
	const paused = refs.some((r) => statusOf(r) === 'waiting');
	// The list's own counts when it has them, else the report of a build already opened here.
	const checksFor = (id: string) =>
		checksOf(byId.get(id)?.checks ?? qc.getQueryData<RunDetail>(agentKeys.run(appId, id))?.report);

	const changed = useCallback(() => {
		invalidate();
		onRunChange?.();
	}, [invalidate, onRunChange]);
	const started = (runId: string) => {
		setSelected(runId);
		onRunChange?.();
	};
	const start = useStartRun(appId, requirementId, started);
	const resume = useResumeRun(appId, requirementId, started);
	const reportStatus = useCallback(
		(id: string, s: RunStatus) => setLive((m) => (m[id] === s ? m : { ...m, [id]: s })),
		[],
	);

	const name = appName ?? requirement?.title ?? 'this app';
	const buildLabel = paused
		? 'Waiting for you'
		: inFlight
			? 'Building…'
			: refs.length
				? 'Build again'
				: 'Start build';
	const buildButton = (
		<Button
			size="sm"
			variant="primary"
			icon="rocket"
			disabled={!canBuild || inFlight}
			loading={start.isPending}
			title={
				!canBuild
					? "This requirement can't be built right now"
					: paused
						? 'A build is paused and waiting for you'
						: inFlight
							? 'A build is already running'
							: undefined
			}
			onClick={() => start.mutate()}
		>
			{buildLabel}
		</Button>
	);

	if (isLoading)
		return (
			<div className="grid gap-3">
				<Skeleton height={46} />
				<Skeleton height={200} />
			</div>
		);

	if (error)
		return (
			<Card>
				<ErrorState error={error} onRetry={() => refetch()} />
			</Card>
		);

	if (!current)
		return (
			<Card>
				<EmptyState title="No builds yet" action={canBuild ? buildButton : undefined}>
					{canBuild
						? 'Ready to build. Start a build to create the app on this server.'
						: 'Approve (or commit) the requirements to start the first build.'}
				</EmptyState>
			</Card>
		);

	return (
		<div className="grid gap-4">
			<div className="flex items-center gap-2">
				<h3 className="text-[13.5px]">Builds</h3>
				<span className="text-[12px] text-t4">{Math.max(refs.length, 1)}</span>
				<div className="ml-auto">{buildButton}</div>
			</div>

			{current && (
				<RunView
					key={current}
					appId={appId}
					runId={current}
					appName={name}
					onFinished={changed}
					onStatus={reportStatus}
					onResume={(id) => resume.mutate(id)}
					resuming={resume.isPending}
				/>
			)}

			{refs.length > 1 && (
				<Card>
					<div className="card-h">
						<h3>History</h3>
						<span className="ct text-t4">{refs.length === 10 ? 'Latest 10' : refs.length}</span>
					</div>
					<div role="list">
						{refs.map((r, i) => {
							const s = byId.get(r.uuid);
							const st = runStatus(statusOf(r));
							return (
								<button
									key={r.uuid}
									type="button"
									role="listitem"
									aria-current={r.uuid === current}
									className={cx('rp-hist', r.uuid === current && 'on')}
									onClick={() => setSelected(r.uuid)}
								>
									<span className="w-[62px] shrink-0 text-t3">Build {refs.length - i}</span>
									<Badge
										tone={st.tone}
										dot
										busy={isRunActive(statusOf(r)) && statusOf(r) !== 'waiting'}
									>
										{st.label}
									</Badge>
									{!isRunActive(statusOf(r)) && <ChecksChip checks={checksFor(r.uuid)} />}
									{s?.trigger_kind === 'resume' && (
										<span className="text-[12px] text-t3">resumed</span>
									)}
									<span className="r">
										<span title={formatDateTime(s?.started_at ?? r.queued_at)}>
											{timeAgo(s?.started_at ?? r.queued_at)}
										</span>
										<span className="w-[56px] text-right">{fmtDuration(s?.duration_ms)}</span>
										<span className="w-[52px] text-right">{fmtCost(s?.total_cost_usd)}</span>
									</span>
								</button>
							);
						})}
					</div>
				</Card>
			)}
		</div>
	);
}
