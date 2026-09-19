/**
 * A development run, shown as progress rather than tool calls.
 *
 * Embeddable, because the build is part of the conversation — the user asked
 * for something and this is it happening, so it belongs in the chat next to
 * the requirement they just approved rather than on a screen they have to
 * navigate to and back from. The standalone route mounts the same component.
 *
 * The raw event stream stays one click away: it is the only way to debug a
 * failure, so it is hidden rather than discarded.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import toast from 'react-hot-toast';
import Toast from '../../../components/Notifications/Toast';
import useApi from '../../../hooks/useApi';
import RunEventRow from './RunEventRow';
import RunUsage from './RunUsage';

const POLL_RUNNING_MS = 1200;
const POLL_QUEUED_MS = 3000;

const PHASES = [
	{ id: 'preparing', label: 'Preparing', hint: 'packages, snapshot' },
	{ id: 'planning', label: 'Planning', hint: 'reading the app' },
	{ id: 'building', label: 'Building', hint: 'models, views, forms' },
	{ id: 'wiring', label: 'Wiring up', hint: 'routes, menus, app module' },
	{ id: 'applying', label: 'Applying', hint: 'migrations and sync' },
	{ id: 'users', label: 'Roles & users', hint: '' },
	{ id: 'done', label: 'Finished', hint: '' },
];

export const TERMINAL = ['success', 'partial', 'failed', 'timeout', 'aborted'];

const STATUS_META = {
	queued: { label: 'Queued', accent: '#6B7280' },
	running: { label: 'Building your app', accent: '#5048ED' },
	syncing: { label: 'Applying changes', accent: '#B45309' },
	success: { label: 'Built', accent: '#047857' },
	partial: { label: 'Built with sync errors', accent: '#B45309' },
	failed: { label: 'Build failed', accent: '#DC2626' },
	timeout: { label: 'Timed out', accent: '#DC2626' },
	aborted: { label: 'Stopped', accent: '#6B7280' },
};

function notify(type, title, description) {
	toast.custom(
		(t) => <Toast type={type} toastRef={t} title={title} description={description} />,
		{ duration: 5000, position: 'bottom-left' }
	);
}

function Elapsed({ startedAt, endedAt }) {
	const [, tick] = useState(0);
	useEffect(() => {
		if (endedAt) return undefined;
		const id = setInterval(() => tick((v) => v + 1), 1000);
		return () => clearInterval(id);
	}, [endedAt]);
	if (!startedAt) return null;
	const secs = Math.max(
		0,
		Math.floor(((endedAt ? new Date(endedAt) : new Date()) - new Date(startedAt)) / 1000)
	);
	return (
		<span>
			{String(Math.floor(secs / 60)).padStart(2, '0')}:
			{String(secs % 60).padStart(2, '0')}
		</span>
	);
}

function PhaseIcon({ state }) {
	if (state === 'done')
		return <span className="font-mono text-[13px] text-[#047857]">✔</span>;
	if (state === 'active')
		return <span className="h-[8px] w-[8px] animate-pulse rounded-full bg-[#5048ED]" />;
	return <span className="h-[8px] w-[8px] rounded-full border border-[#D1D5DB]" />;
}

/**
 * `onRun` reports the run upward on every poll — the panel around this one
 * needs the finished run's URL and test users, and re-fetching them there
 * would mean two clients polling the same endpoint.
 *
 * `onSwitchRun` is how a resume re-points the host at the new run; in the
 * chat there is nowhere to navigate to.
 */
export default function RunLive({ appId, runId, onRun, onSwitchRun, embedded = false }) {
	const triggerApi = useApi();

	const [run, setRun] = useState(null);
	const [events, setEvents] = useState([]);
	const [phase, setPhase] = useState('preparing');
	const [showDetail, setShowDetail] = useState(false);
	// A finished build's timeline is seven ticks — it says nothing. One
	// that finished before you arrived starts folded; one that finishes
	// while you watch does not suddenly collapse under you.
	const [showSteps, setShowSteps] = useState(true);

	const seqRef = useRef(0);
	const pollRef = useRef(null);
	const detailRef = useRef(null);
	const arrivedRef = useRef(true);
	const onRunRef = useRef(onRun);
	onRunRef.current = onRun;

	const base = `/api/v1/apps/${appId}/agent-mode`;

	// Report upward on any change rather than at each call site: the poll
	// updates `run` from two places, and a missed notification would leave the
	// panel next door showing a finished build as still running.
	useEffect(() => {
		if (run && onRunRef.current) onRunRef.current(run);
	}, [run]);

	const pollOnce = useCallback(async () => {
		const { response, success } = await triggerApi({
			url: `${base}/runs/${runId}/event-tail/?after_seq=${seqRef.current}`,
			type: 'GET',
			loader: false,
			showErrorModal: false,
		});
		if (!success || !response) return;
		if (arrivedRef.current) {
			arrivedRef.current = false;
			if (embedded && response.is_terminal) setShowSteps(false);
		}
		if (response.events?.length) {
			seqRef.current = response.next_seq ?? seqRef.current;
			setEvents((prev) => [...prev, ...response.events]);
		}
		if (response.phase) setPhase(response.phase);
		// Functional update: pollOnce must not close over `run`, or it would
		// rebuild every tick and restart the interval below.
		setRun((prev) => ({
			...(prev || {}),
			uuid: runId,
			status: response.status,
			progress: response.progress,
		}));

		if (response.is_terminal) {
			clearInterval(pollRef.current);
			pollRef.current = null;
			const { response: detail } = await triggerApi({
				url: `${base}/runs/${runId}/`,
				type: 'GET',
				loader: false,
				showErrorModal: false,
			});
			if (detail) setRun(detail);
		}
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [base, runId]);

	useEffect(() => {
		seqRef.current = 0;
		arrivedRef.current = true;
		setEvents([]);
		setPhase('preparing');
		pollOnce();
		pollRef.current = setInterval(pollOnce, POLL_QUEUED_MS);
		return () => {
			if (pollRef.current) clearInterval(pollRef.current);
			pollRef.current = null;
		};
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [runId]);

	// Tighten the poll once it is actually running; a queued run changes
	// nothing worth a request every 1.2s.
	useEffect(() => {
		if (!pollRef.current || !run?.status) return;
		if (run.status !== 'running' && run.status !== 'syncing') return;
		clearInterval(pollRef.current);
		pollRef.current = setInterval(pollOnce, POLL_RUNNING_MS);
	}, [run?.status, pollOnce]);

	useEffect(() => {
		if (showDetail && detailRef.current)
			detailRef.current.scrollTop = detailRef.current.scrollHeight;
	}, [events.length, showDetail]);

	const resume = async () => {
		const { success, response } = await triggerApi({
			url: `${base}/runs/${runId}/resume/`,
			type: 'POST',
			loader: false,
			payload: {},
			showErrorModal: false,
		});
		if (success && response?.uuid) {
			notify('info', 'Resuming', 'Continuing from where the last run stopped.');
			if (onSwitchRun) onSwitchRun(response.uuid);
		} else {
			notify('error', 'Could not resume', response?.message);
		}
	};

	const abort = async () => {
		const { success } = await triggerApi({
			url: `${base}/runs/${runId}/abort/`,
			type: 'POST',
			loader: false,
			payload: {},
		});
		if (success) notify('info', 'Stopping', 'Finishing the current step, then stopping.');
	};

	const inFlight = run && !TERMINAL.includes(run.status);
	const phaseIndex = PHASES.findIndex((p) => p.id === phase);
	const meta = STATUS_META[run?.status] || STATUS_META.queued;

	const lastMeaningful = [...events]
		.reverse()
		.find((e) => ['assistant', 'tool_use', 'post_step', 'sys', 'skill'].includes(e.kind));

	const files = [];
	events.forEach((e) => {
		if (e.kind === 'tool_use' && ['Write', 'Edit', 'MultiEdit'].includes(e.tool_name)) {
			const path = e.data?.file_path || e.data?.path;
			if (path && !files.includes(path)) files.push(path);
		}
	});

	return (
		<div
			className={
				embedded
					? 'overflow-hidden rounded-[10px] border border-[#E5E7EB] bg-white'
					: 'flex min-h-0 grow flex-col rounded-[12px] border border-[#DDE2E5] bg-white'
			}
		>
			<div className="flex items-center justify-between gap-[8px] border-b border-[#F1F3F5] px-[14px] py-[9px]">
				<div className="flex min-w-0 flex-wrap items-center gap-[10px]">
					<span
						className="font-lato text-[13px] font-semibold"
						style={{ color: meta.accent }}
					>
						{meta.label}
					</span>
					<span className="font-lato text-[12px] text-[#6B7280]">
						<Elapsed startedAt={run?.started_at} endedAt={run?.ended_at} />
					</span>
					{run?.progress?.cost_usd ? (
						<span className="font-lato text-[12px] text-[#6B7280]">
							${run.progress.cost_usd}
						</span>
					) : null}
				</div>
				<div className="flex shrink-0 items-center gap-[8px]">
					{inFlight ? (
						<button
							onClick={abort}
							className="rounded-[6px] border border-[#FCA5A5] px-[10px] py-[4px] font-lato text-[12px] font-medium text-[#DC2626] hover:bg-[#FEF2F2]"
						>
							Stop
						</button>
					) : null}
					{!showSteps ? (
						<button
							onClick={() => setShowSteps(true)}
							className="rounded-[6px] border border-[#DDE2E5] px-[10px] py-[4px] font-lato text-[12px] text-[#6B7280] hover:bg-[#F0F3F4]"
						>
							Steps
						</button>
					) : null}
					<button
						onClick={() => setShowDetail((v) => !v)}
						className="rounded-[6px] border border-[#DDE2E5] px-[10px] py-[4px] font-lato text-[12px] text-[#6B7280] hover:bg-[#F0F3F4]"
					>
						{showDetail ? 'Hide detail' : 'Detail'}
					</button>
				</div>
			</div>

			<div className={embedded ? '' : 'min-h-0 grow overflow-y-auto'}>
				{showSteps ? (
					<>
				<div className="px-[16px] py-[12px]">
					{PHASES.map((p, i) => {
						const state = i < phaseIndex ? 'done' : i === phaseIndex ? 'active' : 'todo';
						return (
							<div key={p.id} className="flex items-start gap-[10px] py-[4px]">
								<span className="mt-[5px] flex h-[14px] w-[14px] items-center justify-center">
									<PhaseIcon state={state} />
								</span>
								<div className="min-w-0 grow">
									<span
										className={`font-lato text-[13px] ${
											state === 'todo' ? 'text-[#9CA3AF]' : 'font-medium text-[#111827]'
										}`}
									>
										{p.label}
									</span>
									{state === 'active' && lastMeaningful ? (
										<div className="truncate font-lato text-[12px] text-[#6B7280]">
											{lastMeaningful.message}
										</div>
									) : p.hint && state !== 'todo' ? (
										<div className="font-lato text-[12px] text-[#9CA3AF]">{p.hint}</div>
									) : null}
								</div>
							</div>
						);
					})}
				</div>

				{files.length ? (
					<div className="border-t border-[#F1F3F5] px-[16px] py-[10px]">
						<div className="mb-[6px] font-lato text-[11px] font-bold uppercase tracking-[0.06em] text-[#6B7280]">
							Files written ({files.length})
						</div>
						<div className="flex flex-col gap-[2px]">
							{files.slice(-8).map((f) => (
								<span key={f} className="truncate font-mono text-[11px] text-[#374151]">
									{f}
								</span>
							))}
						</div>
					</div>
				) : null}

						</>
				) : null}

			{run?.requires_restart ? (
					<div className="border-t border-[#FDE68A] bg-[#FFFBEB] px-[16px] py-[9px] font-lato text-[12px] text-[#92400E]">
						Models, tasks or settings changed — restart the app server and Celery
						workers to load the new code.
					</div>
				) : null}

				{run?.error_message ? (
					<div className="border-t border-[#FECACA] bg-[#FEF2F2] px-[16px] py-[9px]">
						<div className="font-lato text-[12px] text-[#B91C1C]">
							<strong>{run.error_type}</strong> — {run.error_message}
						</div>
						{run.can_resume ? (
							<div className="mt-[6px] font-lato text-[12px] text-[#7F1D1D]">
								The work already written is still on disk. Resuming continues
								from there instead of starting again.
							</div>
						) : null}
					</div>
				) : null}

				{/* The link and credentials live in the right-hand panel when
				    embedded; repeating them here would be two sources of truth. */}
				{!embedded && (run?.app_access?.url || run?.test_users?.length) ? (
					<div className="border-t border-[#F1F3F5] px-[16px] py-[10px]">
						<div className="mb-[6px] font-lato text-[11px] font-bold uppercase tracking-[0.06em] text-[#6B7280]">
							Open the app
						</div>
						{run?.app_access?.url ? (
							<a
								href={run.app_access.url}
								target="_blank"
								rel="noreferrer"
								className="break-all font-mono text-[12px] text-[#346BD4] hover:underline"
							>
								{run.app_access.url}
							</a>
						) : (
							<div className="font-lato text-[12px] text-[#B45309]">
								This app has no domain set up yet, so it cannot be opened in a
								browser.
							</div>
						)}
					</div>
				) : null}

				{showDetail ? (
					<>
						<RunUsage run={run} />
						<div
							ref={detailRef}
							className="max-h-[320px] overflow-y-auto border-t border-[#E5E7EB]"
						>
							{events.map((e) => (
								<RunEventRow key={e.seq} event={e} />
							))}
						</div>
					</>
				) : null}
			</div>

			{run?.can_resume ? (
				<div className="flex justify-end border-t border-[#F1F3F5] p-[10px]">
					<button
						onClick={resume}
						className="rounded-[8px] bg-gradient-to-br from-[#5048ED] to-[#346BD4] px-[16px] py-[7px] font-lato text-[13px] font-medium text-white hover:opacity-90"
					>
						Resume build
					</button>
				</div>
			) : null}
		</div>
	);
}
