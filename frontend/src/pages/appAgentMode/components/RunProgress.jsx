/**
 * Phase 2 — the development run, shown as progress rather than tool calls.
 *
 * Named phases with a plain-language current action, and the files the agent
 * has touched. The raw event stream is still one click away: it is the only
 * way to debug a failure, so it is hidden rather than discarded.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import toast from 'react-hot-toast';
import { useNavigate, useParams } from 'react-router-dom';
import Toast from '../../../components/Notifications/Toast';
import useApi from '../../../hooks/useApi';
import RunEventRow from './RunEventRow';

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

const TERMINAL = ['success', 'partial', 'failed', 'timeout', 'aborted'];

const STATUS_META = {
	queued: { label: 'Queued', accent: '#6B7280' },
	running: { label: 'Running', accent: '#5048ED' },
	syncing: { label: 'Syncing', accent: '#B45309' },
	success: { label: 'Success', accent: '#047857' },
	partial: { label: 'Completed with sync errors', accent: '#B45309' },
	failed: { label: 'Failed', accent: '#DC2626' },
	timeout: { label: 'Timed out', accent: '#DC2626' },
	aborted: { label: 'Aborted', accent: '#6B7280' },
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
	const secs = Math.max(0, Math.floor(((endedAt ? new Date(endedAt) : new Date()) - new Date(startedAt)) / 1000));
	return <span>{String(Math.floor(secs / 60)).padStart(2, '0')}:{String(secs % 60).padStart(2, '0')}</span>;
}

function PhaseIcon({ state }) {
	if (state === 'done')
		return <span className="font-mono text-[13px] text-[#047857]">✔</span>;
	if (state === 'active')
		return <span className="h-[8px] w-[8px] animate-pulse rounded-full bg-[#5048ED]" />;
	return <span className="h-[8px] w-[8px] rounded-full border border-[#D1D5DB]" />;
}

export default function RunProgress() {
	const { appId, runId } = useParams();
	const navigate = useNavigate();
	const triggerApi = useApi();

	const [run, setRun] = useState(null);
	const [events, setEvents] = useState([]);
	const [phase, setPhase] = useState('preparing');
	const [showDetail, setShowDetail] = useState(false);

	const seqRef = useRef(0);
	const pollRef = useRef(null);
	const detailRef = useRef(null);
	const base = `/api/v1/apps/${appId}/agent-mode`;

	const pollOnce = useCallback(async () => {
		const { response, success } = await triggerApi({
			url: `${base}/runs/${runId}/event-tail/?after_seq=${seqRef.current}`,
			type: 'GET', loader: false, showErrorModal: false,
		});
		if (!success || !response) return;
		if (response.events?.length) {
			seqRef.current = response.next_seq ?? seqRef.current;
			setEvents((prev) => [...prev, ...response.events]);
		}
		if (response.phase) setPhase(response.phase);
		setRun((prev) => ({ ...(prev || {}), status: response.status, progress: response.progress }));

		if (response.is_terminal) {
			clearInterval(pollRef.current);
			pollRef.current = null;
			const { response: detail } = await triggerApi({
				url: `${base}/runs/${runId}/`, type: 'GET', loader: false,
			});
			if (detail) setRun(detail);
		}
	}, [base, runId]);

	useEffect(() => {
		seqRef.current = 0;
		setEvents([]);
		pollOnce();
		pollRef.current = setInterval(pollOnce, run?.status === 'queued' ? POLL_QUEUED_MS : POLL_RUNNING_MS);
		return () => {
			if (pollRef.current) clearInterval(pollRef.current);
			pollRef.current = null;
		};
	}, [runId]);

	useEffect(() => {
		if (showDetail && detailRef.current)
			detailRef.current.scrollTop = detailRef.current.scrollHeight;
	}, [events.length, showDetail]);

	const resume = async () => {
		const { success, response } = await triggerApi({
			url: `${base}/runs/${runId}/resume/`,
			type: 'POST', loader: false, payload: {}, showErrorModal: false,
		});
		if (success && response?.uuid) {
			notify('info', 'Resuming', 'Continuing from where the last run stopped.');
			navigate(`../runs/${response.uuid}`);
		} else {
			notify('error', 'Could not resume', response?.message);
		}
	};

	const abort = async () => {
		const { success } = await triggerApi({
			url: `${base}/runs/${runId}/abort/`, type: 'POST', loader: false, payload: {},
		});
		if (success) notify('info', 'Stopping', 'Finishing the current step, then stopping.');
	};

	const inFlight = run && !TERMINAL.includes(run.status);
	const phaseIndex = PHASES.findIndex((p) => p.id === phase);
	const meta = STATUS_META[run?.status] || STATUS_META.queued;

	// Latest human-readable line, and the files written so far.
	const lastMeaningful = [...events].reverse().find((e) =>
		['assistant', 'tool_use', 'post_step', 'sys', 'skill'].includes(e.kind)
	);
	const files = [];
	events.forEach((e) => {
		if (e.kind === 'tool_use' && ['Write', 'Edit', 'MultiEdit'].includes(e.tool_name)) {
			const path = e.data?.file_path || e.data?.path;
			if (path && !files.includes(path)) files.push(path);
		}
	});

	return (
		<div className="flex min-h-0 grow flex-col rounded-[12px] border border-[#DDE2E5] bg-white">
			<div className="flex items-center justify-between border-b border-[#F1F3F5] px-[16px] py-[10px]">
				<div className="flex items-center gap-[10px]">
					<span className="font-lato text-[13px] font-semibold" style={{ color: meta.accent }}>
						{meta.label}
					</span>
					<span className="font-lato text-[12px] text-[#6B7280]">
						<Elapsed startedAt={run?.started_at} endedAt={run?.ended_at} />
					</span>
					{run?.progress?.cost_usd ? (
						<span className="font-lato text-[12px] text-[#6B7280]">${run.progress.cost_usd}</span>
					) : null}
					{run?.progress?.turns ? (
						<span className="font-lato text-[12px] text-[#6B7280]">{run.progress.turns} turns</span>
					) : null}
				</div>
				<div className="flex items-center gap-[8px]">
					{inFlight ? (
						<button
							onClick={abort}
							className="rounded-[6px] border border-[#FCA5A5] px-[12px] py-[5px] font-lato text-[12px] font-medium text-[#DC2626] hover:bg-[#FEF2F2]"
						>
							Stop
						</button>
					) : null}
					<button
						onClick={() => setShowDetail((v) => !v)}
						className="rounded-[6px] border border-[#DDE2E5] px-[12px] py-[5px] font-lato text-[12px] text-[#6B7280] hover:bg-[#F0F3F4]"
					>
						{showDetail ? 'Hide detail' : 'Show detail'}
					</button>
				</div>
			</div>

			<div className="min-h-0 grow overflow-y-auto">
				{/* Phase timeline */}
				<div className="px-[20px] py-[16px]">
					{PHASES.map((p, i) => {
						const state = i < phaseIndex ? 'done' : i === phaseIndex ? 'active' : 'todo';
						return (
							<div key={p.id} className="flex items-start gap-[10px] py-[5px]">
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
					<div className="border-t border-[#F1F3F5] px-[20px] py-[12px]">
						<div className="mb-[6px] font-lato text-[11px] font-bold uppercase tracking-[0.06em] text-[#6B7280]">
							Files written ({files.length})
						</div>
						<div className="flex flex-col gap-[2px]">
							{files.slice(-14).map((f) => (
								<span key={f} className="truncate font-mono text-[11px] text-[#374151]">{f}</span>
							))}
						</div>
					</div>
				) : null}

				{run?.requires_restart ? (
					<div className="border-t border-[#FDE68A] bg-[#FFFBEB] px-[20px] py-[10px] font-lato text-[12px] text-[#92400E]">
						Models, tasks or settings changed — restart the app server and Celery
						workers to load the new code.
					</div>
				) : null}

				{run?.error_message ? (
					<div className="border-t border-[#FECACA] bg-[#FEF2F2] px-[20px] py-[10px]">
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

				{run?.test_users?.length ? (
					<div className="border-t border-[#F1F3F5] px-[20px] py-[12px]">
						<div className="mb-[6px] font-lato text-[11px] font-bold uppercase tracking-[0.06em] text-[#6B7280]">
							Test users — temporary passwords, change at first login
						</div>
						<table className="w-full font-mono text-[11px]">
							<tbody>
								{run.test_users.map((u) => (
									<tr key={u.email} className="border-b border-[#F8FAFC]">
										<td className="py-[3px] pr-[10px] text-[#374151]">{u.email}</td>
										<td className="py-[3px] pr-[10px] text-[#6B7280]">{u.role}</td>
										<td className="py-[3px] text-[#111827]">{u.password || u.status}</td>
									</tr>
								))}
							</tbody>
						</table>
					</div>
				) : null}

				{showDetail ? (
					<div ref={detailRef} className="max-h-[380px] overflow-y-auto border-t border-[#E5E7EB]">
						{events.map((e) => <RunEventRow key={e.seq} event={e} />)}
					</div>
				) : null}
			</div>

			{!inFlight && run ? (
				<div className="flex justify-end gap-[8px] border-t border-[#F1F3F5] p-[10px]">
					{run.can_resume ? (
						<button
							onClick={resume}
							className="rounded-[8px] bg-gradient-to-br from-[#5048ED] to-[#346BD4] px-[16px] py-[8px] font-lato text-[13px] font-medium text-white hover:opacity-90"
						>
							Resume build
						</button>
					) : null}
					<button
						onClick={() => navigate('..')}
						className="rounded-[6px] border border-[#DDE2E5] px-[14px] py-[7px] font-lato text-[13px] font-medium text-[#212429] hover:bg-[#F0F3F4]"
					>
						Back to requirements
					</button>
				</div>
			) : null}
		</div>
	);
}
