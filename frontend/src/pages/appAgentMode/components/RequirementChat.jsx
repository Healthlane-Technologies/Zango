/**
 * Phase 1 — gather the requirement, then approve it.
 *
 * Two panes: the conversation on the left, the live specification on the
 * right. The spec is directly editable because a one-word correction should
 * not cost a full agent turn; every edit is versioned server-side.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import toast from 'react-hot-toast';
import { useNavigate, useParams } from 'react-router-dom';
import Toast from '../../../components/Notifications/Toast';
import useApi from '../../../hooks/useApi';

const POLL_MS = 1500;

function notify(type, title, description) {
	toast.custom(
		(t) => <Toast type={type} toastRef={t} title={title} description={description} />,
		{ duration: 5000, position: 'bottom-left' }
	);
}

const RUN_META = {
	queued: { label: 'Queued', bg: '#F3F4F6', accent: '#6B7280' },
	running: { label: 'Running', bg: '#EEF2FF', accent: '#5048ED' },
	syncing: { label: 'Syncing', bg: '#FEF3C7', accent: '#B45309' },
	success: { label: 'Success', bg: '#ECFDF5', accent: '#047857' },
	partial: { label: 'Sync errors', bg: '#FEF3C7', accent: '#B45309' },
	failed: { label: 'Failed', bg: '#FEF2F2', accent: '#DC2626' },
	timeout: { label: 'Timed out', bg: '#FEF2F2', accent: '#DC2626' },
	aborted: { label: 'Aborted', bg: '#F3F4F6', accent: '#6B7280' },
};

const STATUS_META = {
	gathering: { label: 'Gathering', bg: '#EEF2FF', accent: '#5048ED' },
	ready: { label: 'Ready for review', bg: '#FEF3C7', accent: '#B45309' },
	approved: { label: 'Approved', bg: '#ECFDF5', accent: '#047857' },
	abandoned: { label: 'Abandoned', bg: '#F3F4F6', accent: '#6B7280' },
};

function Bubble({ message }) {
	const isUser = message.role === 'user';
	return (
		<div className={`flex ${isUser ? 'justify-end' : 'justify-start'} px-[16px] py-[6px]`}>
			<div
				className={`max-w-[85%] whitespace-pre-wrap rounded-[10px] px-[12px] py-[8px] font-lato text-[13px] leading-[19px] ${
					isUser ? 'bg-[#5048ED] text-white' : 'bg-[#F3F4F6] text-[#111827]'
				}`}
			>
				{message.content}
			</div>
		</div>
	);
}

export default function RequirementChat() {
	const { appId, requirementId } = useParams();
	const navigate = useNavigate();
	const triggerApi = useApi();

	const [req, setReq] = useState(null);
	const [reply, setReply] = useState('');
	const [spec, setSpec] = useState('');
	const [specDirty, setSpecDirty] = useState(false);
	const [busy, setBusy] = useState(false);
	// Set the moment we send, cleared only when the server reports a reply.
	// Without it an in-flight poll can clear is_thinking and re-enable Send.
	const pendingRef = useRef(false);

	const scrollRef = useRef(null);
	const pollRef = useRef(null);
	const base = `/api/v1/apps/${appId}/agent-mode`;

	const load = useCallback(async () => {
		const { response, success } = await triggerApi({
			url: `${base}/requirements/${requirementId}/`,
			type: 'GET', loader: false, showErrorModal: false,
		});
		if (!success || !response) return null;
		// A newly-arrived reply means the turn really is over.
		if (response.is_thinking === false && (response.messages || []).length) {
			const last = response.messages[response.messages.length - 1];
			if (last.role === 'assistant') pendingRef.current = false;
		}
		setReq({ ...response, is_thinking: response.is_thinking || pendingRef.current });
		// Never clobber unsaved edits with the server copy.
		setSpec((cur) => (specDirty ? cur : response.spec_markdown || ''));
		return response;
	}, [base, requirementId, specDirty]);

	useEffect(() => { load(); }, [requirementId]);

	// Poll only while the agent is composing a reply.
	useEffect(() => {
		if (!req?.is_thinking) {
			if (pollRef.current) clearInterval(pollRef.current);
			pollRef.current = null;
			return undefined;
		}
		pollRef.current = setInterval(load, POLL_MS);
		return () => {
			if (pollRef.current) clearInterval(pollRef.current);
			pollRef.current = null;
		};
	}, [req?.is_thinking, load]);

	useEffect(() => {
		if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
	}, [req?.messages?.length, req?.is_thinking]);

	const send = async () => {
		if (!reply.trim() || req?.is_thinking) return;
		setBusy(true);
		const { success, response, responseStatus } = await triggerApi({
			url: `${base}/requirements/${requirementId}/messages/`,
			type: 'POST', loader: false, payload: { content: reply.trim() },
			showErrorModal: false,
		});
		setBusy(false);
		if (success) {
			pendingRef.current = true;
			setReply('');
			setReq((r) => ({
				...r,
				is_thinking: true,
				messages: [
					...(r?.messages || []),
					{ seq: (r?.messages?.length || 0) + 1, role: 'user', content: reply.trim() },
				],
			}));
		} else if (responseStatus === 409) {
			// The agent was still replying. Keep the text so nothing is lost
			// and reflect the real state instead of reporting a failure.
			pendingRef.current = true;
			setReq((r) => ({ ...r, is_thinking: true }));
			notify(
				'info',
				'Still replying',
				'Your message was not sent — the agent is finishing its previous answer.'
			);
		} else {
			notify('error', 'Could not send', response?.message);
		}
	};

	const saveSpec = async () => {
		setBusy(true);
		const { success, response } = await triggerApi({
			url: `${base}/requirements/${requirementId}/spec/`,
			type: 'POST', loader: false, payload: { spec_markdown: spec },
			showErrorModal: false,
		});
		setBusy(false);
		if (success) {
			setSpecDirty(false);
			notify('success', 'Requirement saved', `Version ${response?.spec_version}`);
			load();
		} else {
			notify('error', 'Could not save', response?.message);
		}
	};

	const startRun = async () => {
		const { success, response } = await triggerApi({
			url: `${base}/runs/`, type: 'POST', loader: false,
			payload: { requirement_uuid: requirementId }, showErrorModal: false,
		});
		if (success && response?.uuid) {
			navigate(`../runs/${response.uuid}`);
			return true;
		}
		// 409 means a run is already going — send them to it rather than erroring.
		if (response?.run_uuid) {
			navigate(`../runs/${response.run_uuid}`);
			return true;
		}
		notify('error', 'Could not start the build', response?.message);
		return false;
	};

	const build = async () => {
		setBusy(true);
		await startRun();
		setBusy(false);
	};

	const approveAndBuild = async () => {
		setBusy(true);
		if (specDirty) await saveSpec();
		const { success, response } = await triggerApi({
			url: `${base}/requirements/${requirementId}/approve/`,
			type: 'POST', loader: false, payload: {}, showErrorModal: false,
		});
		if (!success) {
			setBusy(false);
			notify('error', 'Could not approve', response?.message);
			return;
		}
		const ok = await startRun();
		setBusy(false);
		if (!ok) load();
	};

	if (!req) return null;
	const meta = STATUS_META[req.status] || STATUS_META.gathering;
	const locked = req.status === 'approved';

	return (
		<div className="flex min-h-0 grow gap-[20px]">
			{/* Conversation */}
			<div className="flex w-[46%] min-w-[360px] flex-col rounded-[12px] border border-[#DDE2E5] bg-white">
				<div className="flex items-center justify-between border-b border-[#F1F3F5] px-[16px] py-[10px]">
					<span className="font-lato text-[13px] font-semibold text-[#212429]">
						{req.title || 'New requirement'}
					</span>
					<span
						className="rounded-full px-[8px] py-[2px] font-lato text-[10px] font-bold uppercase tracking-[0.05em]"
						style={{ backgroundColor: meta.bg, color: meta.accent }}
					>
						{meta.label}
					</span>
				</div>

				<div ref={scrollRef} className="min-h-0 grow overflow-y-auto py-[8px]">
					{(req.messages || []).map((m) => <Bubble key={m.seq} message={m} />)}
					{req.is_thinking ? (
						<div className="px-[16px] py-[6px] font-lato text-[12px] italic text-[#9CA3AF]">
							Thinking…
						</div>
					) : null}
					{req.error_message ? (
						<div className="mx-[16px] my-[8px] rounded-[6px] bg-[#FEF2F2] px-[10px] py-[8px] font-lato text-[12px] text-[#B91C1C]">
							{req.error_message}
						</div>
					) : null}
				</div>

				{!locked ? (
					<div className="border-t border-[#F1F3F5] p-[10px]">
						<textarea
							value={reply}
							onChange={(e) => setReply(e.target.value)}
							onKeyDown={(e) => {
								if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) send();
							}}
							rows={3}
							disabled={req.is_thinking || busy}
							placeholder={
								req.is_thinking
									? 'The agent is replying…'
									: 'Answer the questions, or ask for changes…'
							}
							className="w-full resize-none rounded-[8px] border border-[#DDE2E5] p-[8px] font-lato text-[13px] focus:border-primary focus:outline-none disabled:bg-[#F8FAFC]"
						/>
						<div className="mt-[6px] flex items-center justify-between">
							<span className="font-lato text-[11px] text-[#9CA3AF]">
								{req.is_thinking ? 'Waiting for the agent…' : '⌘/Ctrl + Enter'}
							</span>
							<button
								onClick={send}
								disabled={req.is_thinking || busy || !reply.trim()}
								className="rounded-[6px] bg-[#346BD4] px-[14px] py-[6px] font-lato text-[13px] font-medium text-white hover:bg-[#2556B0] disabled:opacity-40"
							>
								{req.is_thinking ? 'Replying…' : 'Send'}
							</button>
						</div>
					</div>
				) : null}
			</div>

			{/* Specification */}
			<div className="flex min-w-0 grow flex-col rounded-[12px] border border-[#DDE2E5] bg-white">
				<div className="flex items-center justify-between border-b border-[#F1F3F5] px-[16px] py-[10px]">
					<span className="font-lato text-[13px] font-semibold text-[#212429]">
						Requirement{req.spec_version ? ` · v${req.spec_version}` : ''}
					</span>
					{specDirty ? (
						<span className="font-lato text-[11px] text-[#B45309]">unsaved edits</span>
					) : null}
				</div>

				{req.spec_markdown || spec ? (
					<>
						<textarea
							value={spec}
							onChange={(e) => { setSpec(e.target.value); setSpecDirty(true); }}
							readOnly={locked}
							className="min-h-0 grow resize-none p-[16px] font-mono text-[12px] leading-[18px] text-[#111827] focus:outline-none"
						/>
						<div className="flex items-center justify-end gap-[8px] border-t border-[#F1F3F5] p-[10px]">
							{!locked ? (
								<>
									<button
										onClick={saveSpec}
										disabled={!specDirty || busy}
										className="rounded-[6px] border border-[#DDE2E5] px-[14px] py-[7px] font-lato text-[13px] font-medium text-[#212429] hover:bg-[#F0F3F4] disabled:opacity-40"
									>
										Save edits
									</button>
									<button
										onClick={approveAndBuild}
										disabled={busy || req.is_thinking}
										className="rounded-[8px] bg-gradient-to-br from-[#5048ED] to-[#346BD4] px-[16px] py-[8px] font-lato text-[13px] font-medium text-white hover:opacity-90 disabled:opacity-40"
									>
										Approve &amp; build →
									</button>
								</>
							) : (
								<>
									<span className="mr-auto font-lato text-[12px] text-[#047857]">
										Approved{req.approved_by ? ` by ${req.approved_by}` : ''}
									</span>
									<button
										onClick={build}
										disabled={busy}
										className="rounded-[8px] bg-gradient-to-br from-[#5048ED] to-[#346BD4] px-[16px] py-[8px] font-lato text-[13px] font-medium text-white hover:opacity-90 disabled:opacity-40"
									>
										{req.runs?.length ? 'Build again' : 'Start build'}
									</button>
								</>
							)}
						</div>
					</>
				) : (
					<div className="flex grow items-center justify-center px-[24px] text-center">
						<p className="font-lato text-[13px] leading-[20px] text-[#9CA3AF]">
							The agent is working out what you need.
							<br />
							Once the requirement is clear it will appear here for review.
						</p>
					</div>
				)}
				{req.runs?.length ? (
					<div className="border-t border-[#F1F3F5]">
						<div className="px-[16px] pb-[4px] pt-[10px] font-lato text-[11px] font-bold uppercase tracking-[0.06em] text-[#6B7280]">
							Builds from this requirement
						</div>
						<div className="max-h-[180px] overflow-y-auto pb-[6px]">
							{req.runs.map((run) => {
								const rm = RUN_META[run.status] || RUN_META.queued;
								return (
									<button
										key={run.uuid}
										onClick={() => navigate(`../runs/${run.uuid}`)}
										className="flex w-full items-center gap-[10px] px-[16px] py-[7px] text-left hover:bg-[#F8FAFC]"
									>
										<span className="font-mono text-[11px] text-[#6B7280]">
											{run.uuid.slice(0, 8)}
										</span>
										<span className="grow font-lato text-[12px] text-[#9CA3AF]">
											{run.queued_at ? new Date(run.queued_at).toLocaleString() : ''}
										</span>
										<span
											className="rounded-full px-[8px] py-[2px] font-lato text-[10px] font-bold uppercase tracking-[0.05em]"
											style={{ backgroundColor: rm.bg, color: rm.accent }}
										>
											{rm.label}
										</span>
									</button>
								);
							})}
						</div>
					</div>
				) : null}
			</div>
		</div>
	);
}
