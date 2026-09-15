/**
 * Landing view: start a new requirement, or resume an existing one.
 *
 * Requirements persist and are versioned, so a failed build can be re-run
 * without re-gathering what was already agreed.
 */
import { useCallback, useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { useNavigate, useParams } from 'react-router-dom';
import Toast from '../../../components/Notifications/Toast';
import useApi from '../../../hooks/useApi';

const RUN_META = {
	queued: { label: 'queued', accent: '#6B7280' },
	running: { label: 'building', accent: '#5048ED' },
	syncing: { label: 'syncing', accent: '#B45309' },
	success: { label: 'built', accent: '#047857' },
	partial: { label: 'sync errors', accent: '#B45309' },
	failed: { label: 'build failed', accent: '#DC2626' },
	timeout: { label: 'timed out', accent: '#DC2626' },
	aborted: { label: 'aborted', accent: '#6B7280' },
};

const STATUS_META = {
	gathering: { label: 'Gathering', bg: '#EEF2FF', accent: '#5048ED' },
	ready: { label: 'Ready for review', bg: '#FEF3C7', accent: '#B45309' },
	approved: { label: 'Approved', bg: '#ECFDF5', accent: '#047857' },
	abandoned: { label: 'Abandoned', bg: '#F3F4F6', accent: '#6B7280' },
};

function notify(type, title, description) {
	toast.custom(
		(t) => <Toast type={type} toastRef={t} title={title} description={description} />,
		{ duration: 5000, position: 'bottom-left' }
	);
}

export default function RequirementList({ availability }) {
	const { appId } = useParams();
	const navigate = useNavigate();
	const triggerApi = useApi();

	const [prompt, setPrompt] = useState('');
	const [items, setItems] = useState([]);
	const [busy, setBusy] = useState(false);
	const base = `/api/v1/apps/${appId}/agent-mode`;

	const load = useCallback(async () => {
		const { response, success } = await triggerApi({
			url: `${base}/requirements/`, type: 'GET', loader: false, showErrorModal: false,
		});
		if (success && response) setItems(response?.requirements?.records || []);
	}, [base]);

	useEffect(() => { load(); }, []);

	const start = async () => {
		if (!prompt.trim()) return;
		setBusy(true);
		const { success, response } = await triggerApi({
			url: `${base}/requirements/`, type: 'POST', loader: false,
			payload: { prompt: prompt.trim() }, showErrorModal: false,
		});
		setBusy(false);
		if (success && response?.uuid) navigate(`requirements/${response.uuid}`);
		else notify('error', 'Could not start', response?.message);
	};

	const blocked = availability && !availability.available;

	return (
		<div className="flex min-h-0 grow flex-col gap-[16px]">
			<div className="rounded-[12px] border border-[#DDE2E5] bg-white p-[20px]">
				<h2 className="font-source-sans-pro text-[16px] font-semibold text-[#111827]">
					What do you want to build?
				</h2>
				<p className="mt-[2px] font-lato text-[13px] text-[#6B7280]">
					Describe it roughly. The agent will ask what it needs to know, then
					write a requirement for you to approve before anything is built.
				</p>
				<textarea
					value={prompt}
					onChange={(e) => setPrompt(e.target.value)}
					rows={4}
					disabled={blocked || busy}
					placeholder="e.g. a way for staff to book patient appointments and track whether they were attended"
					className="mt-[10px] w-full resize-none rounded-[8px] border border-[#DDE2E5] p-[10px] font-lato text-[13px] leading-[19px] focus:border-primary focus:outline-none disabled:bg-[#F8FAFC]"
				/>
				<div className="mt-[8px] flex justify-end">
					<button
						onClick={start}
						disabled={blocked || busy || !prompt.trim()}
						className="rounded-[8px] bg-gradient-to-br from-[#5048ED] to-[#346BD4] px-[16px] py-[9px] font-lato text-[14px] font-medium text-white hover:opacity-90 disabled:opacity-40"
					>
						{busy ? 'Starting…' : 'Start'}
					</button>
				</div>
			</div>

			<div className="flex min-h-0 grow flex-col rounded-[12px] border border-[#DDE2E5] bg-white">
				<div className="border-b border-[#F1F3F5] px-[16px] py-[10px] font-lato text-[12px] font-bold uppercase tracking-[0.06em] text-[#6B7280]">
					Requirements
				</div>
				<div className="min-h-0 grow overflow-y-auto">
					{items.length === 0 ? (
						<p className="px-[16px] py-[14px] font-lato text-[13px] text-[#9CA3AF]">
							Nothing yet.
						</p>
					) : (
						items.map((r) => {
							const meta = STATUS_META[r.status] || STATUS_META.gathering;
							return (
								<button
									key={r.uuid}
									onClick={() => navigate(`requirements/${r.uuid}`)}
									className="flex w-full items-center gap-[12px] border-b border-[#F1F3F5] px-[16px] py-[11px] text-left hover:bg-[#F8FAFC]"
								>
									<span className="min-w-0 grow truncate font-lato text-[13px] text-[#212429]">
										{r.title || '(untitled)'}
									</span>
									{r.latest_run ? (
										<span
											className="shrink-0 font-lato text-[11px]"
											style={{ color: (RUN_META[r.latest_run.status] || RUN_META.queued).accent }}
										>
											{r.run_count} build{r.run_count > 1 ? 's' : ''} ·{' '}
											{(RUN_META[r.latest_run.status] || RUN_META.queued).label}
										</span>
									) : null}
									<span
										className="shrink-0 rounded-full px-[8px] py-[2px] font-lato text-[10px] font-bold uppercase tracking-[0.05em]"
										style={{ backgroundColor: meta.bg, color: meta.accent }}
									>
										{meta.label}
									</span>
								</button>
							);
						})
					)}
				</div>
			</div>
		</div>
	);
}
