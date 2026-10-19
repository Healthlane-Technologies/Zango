import { useEffect, useState } from 'react';
import { isRunActive, type RunStatus } from '@/api/agentMode';
import { useAbortRun, useRunDetail, type RunDetail } from '@/api/agentRuns';
import { Button, cx, ErrorState, Icon, Skeleton, Tabs } from '@/ui';
import { checksOf } from '@/api/agentRuns';
import { AppReady } from './AppReady';
import { filesWritten, latestActivity, relativePath } from './events';
import { clock, PHASES, runCost, runStatus, timeOfDay } from './format';
import { ActionNeeded, ChecksChip, ChecksReport } from './RunChecks';
import { RunLog } from './RunLog';
import { RunUsage } from './RunUsage';
import { useRunTail, type RunTail } from './useRunTail';

type Tab = 'progress' | 'checks' | 'log' | 'usage';

/** Re-render every second while `on`, for the elapsed clock. */
function useTicker(on: boolean) {
	const [, setN] = useState(0);
	useEffect(() => {
		if (!on) return;
		const id = setInterval(() => setN((n) => n + 1), 1000);
		return () => clearInterval(id);
	}, [on]);
}

function StatusIcon({ status }: { status: RunStatus | undefined }) {
	// Paused for the user: not working, not finished.
	if (status === 'waiting')
		return (
			<span className="rp-okc wait">
				<Icon name="alert" size={11} weight={2.4} />
			</span>
		);
	if (!status || isRunActive(status)) return <span className="spin" />;
	const cls =
		status === 'success'
			? ''
			: status === 'partial'
				? 'warn'
				: status === 'aborted'
					? 'off'
					: 'bad';
	return (
		<span className={cx('rp-okc', cls)}>
			<Icon
				name={status === 'success' || status === 'partial' ? 'check' : 'x'}
				size={11}
				weight={3}
			/>
		</span>
	);
}

function Phases({
	tail,
	live,
	status,
}: {
	tail: RunTail;
	live: boolean;
	status: RunStatus | undefined;
}) {
	const activity = latestActivity(tail.events);
	const failed = !live && status !== 'success' && status !== 'partial';
	// A terminal tail always reports phase "done"; for a run that didn't succeed, show how far it
	// actually got: the furthest phase any of its events reached.
	const reached = failed
		? Math.max(0, ...tail.events.map((e) => PHASES.findIndex((p) => p.id === e.phase)))
		: PHASES.findIndex((p) => p.id === tail.phase);
	// Phases are not always entered in order: a build can go from building straight to applying.
	// A phase the run passed without a single event was skipped, not done. Without any events
	// (not loaded yet, or pruned) there is nothing to tell them apart, so passed counts as done.
	const seen = new Set(tail.events.map((e) => e.phase));
	return (
		<ol className="rp-steps">
			{PHASES.map((p, i) => {
				const state =
					i < reached
						? seen.size && !seen.has(p.id)
							? 'skipped'
							: 'done'
						: i > reached
							? 'todo'
							: failed
								? 'failed'
								: live
									? 'active'
									: 'done';
				return (
					<li
						key={p.id}
						className={cx(state, state === 'active' && status === 'waiting' && 'wait')}
					>
						<span className="n">
							{state === 'done' ? (
								<Icon name="check" size={11} weight={3} />
							) : state === 'failed' ? (
								<Icon name="x" size={11} weight={3} />
							) : state === 'active' && status === 'waiting' ? (
								<Icon name="alert" size={11} weight={2.4} />
							) : state === 'active' ? (
								<span className="spin" style={{ width: 10, height: 10 }} />
							) : state === 'skipped' ? (
								'–'
							) : (
								i + 1
							)}
						</span>
						<div className="min-w-0 flex-1">
							<b>{p.label}</b>
							{state === 'active' && status === 'waiting' ? (
								<small>Paused — waiting for you</small>
							) : state === 'active' && activity ? (
								<small title={activity.message}>{activity.message}</small>
							) : state === 'failed' ? (
								<small>Stopped here</small>
							) : state === 'skipped' ? (
								<small>Skipped</small>
							) : (
								p.hint && state !== 'todo' && <small>{p.hint}</small>
							)}
						</div>
					</li>
				);
			})}
		</ol>
	);
}

function Files({ detail, live, tail }: { detail?: RunDetail; live: boolean; tail: RunTail }) {
	const ws = detail?.workspace_path;
	if (live || !detail?.files_changed) {
		const files = filesWritten(tail.events);
		if (!files.length) return null;
		return (
			<div>
				<div className="rp-sec">Files written ({files.length})</div>
				<div className="grid gap-0.5">
					{files.slice(-10).map((f) => (
						<span key={f} className="mono truncate text-t2" title={f}>
							{relativePath(f, ws)}
						</span>
					))}
				</div>
			</div>
		);
	}
	const fc = detail.files_changed;
	const groups: Array<[string, string[] | undefined, string]> = [
		['Added', fc.added, 'text-green-t'],
		['Modified', fc.modified, 'text-accent-t'],
		['Deleted', fc.deleted, 'text-red-t'],
	];
	const count = groups.reduce((n, [, l]) => n + (l?.length ?? 0), 0);
	if (!count) return null;
	return (
		<details>
			<summary className="rp-sec cursor-pointer">
				Files changed ({count}) ·{' '}
				{groups
					.filter(([, l]) => l?.length)
					.map(([k, l]) => `${l!.length} ${k.toLowerCase()}`)
					.join(', ')}
			</summary>
			<div className="mt-1 grid gap-0.5">
				{groups.flatMap(([k, list, color]) =>
					(list ?? []).map((f) => (
						<span key={k + f} className="mono flex gap-2 truncate text-t2" title={f}>
							<span className={cx('w-3 shrink-0', color)}>{k[0]}</span>
							{relativePath(f, ws)}
						</span>
					)),
				)}
			</div>
		</details>
	);
}

function Notes({ detail }: { detail: RunDetail }) {
	const failedSteps = (detail.post_steps ?? []).filter(
		(s) => s.returncode !== 0 && s.returncode !== null,
	);
	return (
		<>
			{detail.requires_restart && (
				<p className="rp-note warn">
					{detail.restart_hint ||
						'Models, tasks or settings changed — restart the app server and Celery workers to load the new code.'}
				</p>
			)}
			{detail.error_message && (
				<div className="rp-note err">
					<b>{detail.error_type || 'Error'}</b> — {detail.error_message}
					{detail.can_resume && (
						<div className="mt-1">
							The work already written is still on disk. Resuming continues from there instead of
							starting again.
						</div>
					)}
				</div>
			)}
			{failedSteps.length > 0 && (
				<div className="rp-note warn">
					{failedSteps.length === 1 ? 'A finishing step' : `${failedSteps.length} finishing steps`}{' '}
					reported errors:{' '}
					{failedSteps.map((s) => (
						<span key={s.step} className="mono">
							{s.step}{' '}
						</span>
					))}
				</div>
			)}
		</>
	);
}

export interface RunViewProps {
	appId: string;
	runId: string;
	appName: string;
	/** Fired once when a run this view watched live reaches a terminal status. */
	onFinished: () => void;
	onStatus?: (runId: string, status: RunStatus) => void;
	onResume: (runId: string) => void;
	resuming?: boolean;
}

/** One run: status bar, progress, app-ready card, log and usage. */
export function RunView({
	appId,
	runId,
	appName,
	onFinished,
	onStatus,
	onResume,
	resuming,
}: RunViewProps) {
	const detail = useRunDetail(appId, runId);
	const tail = useRunTail(appId, runId, () => {
		detail.refetch();
		onFinished();
	});
	const abort = useAbortRun(appId);
	const [tab, setTab] = useState<Tab>('progress');
	// Continue was accepted; the tail catches up with the new status on its next poll.
	const [continuing, setContinuing] = useState(false);

	const status = tail.status ?? detail.data?.status;
	const live = isRunActive(status);
	const waiting = status === 'waiting' && !continuing;
	useEffect(() => {
		if (continuing && status !== 'waiting') setContinuing(false);
	}, [continuing, status]);
	// Working right now: the clock runs and Stop makes sense. A paused build is neither.
	const working = live && !waiting;
	useTicker(working);

	useEffect(() => {
		if (status) onStatus?.(runId, status);
	}, [runId, status, onStatus]);

	// The detail can be read mid-run (no usage, no app link yet); read it again once it ends.
	const { data: d, refetch } = detail;
	useEffect(() => {
		if (tail.isTerminal && d && !d.is_terminal) refetch();
	}, [tail.isTerminal, d, refetch]);
	// Pausing and continuing change what the detail holds (the actions needed, the report so far).
	const tailStatus = tail.status;
	const detailStatus = d?.status;
	useEffect(() => {
		if (!tailStatus || !detailStatus || tailStatus === detailStatus) return;
		if (tailStatus === 'waiting' || detailStatus === 'waiting') refetch();
	}, [tailStatus, detailStatus, refetch]);

	if (detail.error) return <ErrorState error={detail.error} onRetry={() => detail.refetch()} />;
	if (!d && !tail.ready)
		return (
			<div className="grid gap-3">
				<Skeleton height={46} />
				<Skeleton height={160} />
			</div>
		);

	const meta = runStatus(status ?? 'queued');
	const cost = tail.progress?.cost_usd ?? d?.total_cost_usd;
	const costShown = runCost(cost, d?.auth_source);
	const ready =
		d &&
		!live &&
		(status === 'success' || status === 'partial') &&
		(d.app_access?.url || d.test_users?.length);
	const summary = d?.result_text?.trim();
	const report = d?.report ?? null;
	const checks = checksOf(report);
	const actions = waiting ? (d?.pending_actions ?? []) : [];

	return (
		<div className="grid gap-3">
			<div className="rp-stat">
				<StatusIcon status={status} />
				<div className="min-w-0">
					<b>
						{waiting
							? 'Waiting for you'
							: continuing
								? 'Continuing the build'
								: live
									? status === 'queued'
										? 'Waiting to start'
										: status === 'syncing'
											? 'Applying changes'
											: 'Building your app'
									: status === 'partial' && report && checks?.failed
										? 'Built, with failing checks'
										: status === 'partial' && report?.frontend === false
											? 'Built without a frontend'
											: meta.label}
					</b>
					<div className="text-[12px] text-t3">
						{d?.trigger_kind === 'resume' ? 'Resumed' : 'Started'}{' '}
						{timeOfDay(d?.started_at ?? d?.queued_at) || '—'}
						{d?.abort_requested && working && ' · stopping after this step'}
						{waiting && ' · paused until you act'}
					</div>
				</div>
				<div className="r">
					{/* While a build is live or paused the report is partial: a count would mislead. */}
					{checks && !live && <ChecksChip checks={checks} onClick={() => setTab('checks')} />}
					{!waiting && (
						<span className="num">{clock(d?.started_at, live ? null : d?.ended_at)}</span>
					)}
					{cost != null && (
						<span className="num" title={costShown.title}>
							{costShown.text}
						</span>
					)}
					{working && (
						<Button
							size="xs"
							variant="danger"
							loading={abort.isPending}
							disabled={d?.abort_requested}
							onClick={() => abort.mutate(runId, { onSuccess: () => detail.refetch() })}
						>
							Stop
						</Button>
					)}
					{!live && d?.can_resume && (
						<Button size="xs" variant="primary" loading={resuming} onClick={() => onResume(runId)}>
							Resume
						</Button>
					)}
				</div>
			</div>

			{waiting && actions.length > 0 && (
				<ActionNeeded
					appId={appId}
					runId={runId}
					actions={actions}
					onContinued={() => {
						setContinuing(true);
						detail.refetch();
					}}
				/>
			)}
			{continuing && (
				<p className="rp-note warn" role="status">
					Continuing… the build picks up from where it paused.
				</p>
			)}
			{waiting && d && !actions.length && (
				<p className="rp-note warn">
					The build is paused and waiting for you, but it did not say what for. Check the build log.
				</p>
			)}

			{ready && <AppReady appName={appName} run={d} />}

			<div className="card">
				<Tabs
					value={tab}
					onChange={setTab}
					items={[
						{ value: 'progress', label: 'Progress' },
						...(report
							? [
									{
										value: 'checks' as const,
										label: 'Checks',
										count: checks?.total,
										attention: !!checks?.failed,
									},
								]
							: []),
						{ value: 'log', label: 'Build log', count: tail.events.length || undefined },
						{ value: 'usage', label: 'Usage', disabled: !d },
					]}
				/>
				<div className="grid gap-4 p-4">
					{tab === 'progress' && (
						<>
							<Phases tail={tail} live={live} status={status} />
							{d && <Notes detail={d} />}
							<Files detail={d} live={live} tail={tail} />
							{summary && !live && (
								<details>
									<summary className="rp-sec cursor-pointer">Agent's summary</summary>
									<div className="mt-1 max-h-[280px] overflow-auto whitespace-pre-wrap rounded-lg border border-border bg-bg p-3 text-[12.5px] leading-[1.6] text-t1">
										{summary}
									</div>
								</details>
							)}
						</>
					)}
					{tab === 'checks' && report && <ChecksReport report={report} />}
					{tab === 'log' && <RunLog events={tail.events} live={working} />}
					{tab === 'usage' && d && <RunUsage run={d} />}
				</div>
			</div>
			{tail.error && live && (
				<p className="text-[12px] text-amber-t">
					Lost contact with the run ({tail.error.message}); retrying.
				</p>
			)}
		</div>
	);
}
