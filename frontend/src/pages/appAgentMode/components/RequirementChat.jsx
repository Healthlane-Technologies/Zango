/**
 * The whole of Agent Mode for one requirement: agree it, build it, open it.
 *
 * Left is the conversation, and the build runs *inside* it — the user asked
 * for something and this is it happening, so sending them to a separate
 * progress screen would break the one thread they are following.
 *
 * Right is what they are getting: highlights of the requirement while it is
 * being agreed and built, replaced at the top by the live app's address the
 * moment there is one, with Share and Deploy next to it. The full spec stays
 * a tab away — it is what gets approved, and a one-word correction should not
 * cost a full agent turn, so it is directly editable and versioned.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import toast from 'react-hot-toast';
import { useNavigate, useParams } from 'react-router-dom';
import Toast from '../../../components/Notifications/Toast';
import useApi from '../../../hooks/useApi';
import AppReadyCard from './AppReadyCard';
import Markdown from './Markdown';
import QuestionAnswers, { composeAnswer, isAnswered } from './QuestionAnswers';
import RunLive, { TERMINAL } from './RunLive';
import SpecHighlights from './SpecHighlights';

const POLL_MS = 1500;

const BASE_TABS = [
	{ id: 'highlights', label: 'My Build' },
	{ id: 'requirement', label: 'Requirement' },
];

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
				className={`max-w-[85%] rounded-[10px] border px-[12px] py-[8px] font-lato text-[13px] leading-[19px] ${
					isUser
						? 'whitespace-pre-wrap border-[#C7D2FE] bg-[#EEF2FF] text-[#312E81]'
						: 'border-[#EDEFF1] bg-[#F7F8FA] text-[#111827]'
				}`}
			>
				{/* The user typed plain text; the agent replies in markdown. */}
				{isUser ? message.content : <Markdown text={message.content} />}
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
	const [editingSpec, setEditingSpec] = useState(false);
	const [busy, setBusy] = useState(false);
	const [answers, setAnswers] = useState({});
	// The build the chat is currently showing, and its detail once RunLive
	// has it — the app's address and test users ride on that object.
	const [activeRunId, setActiveRunId] = useState(null);
	const [activeRun, setActiveRun] = useState(null);
	const [rightTab, setRightTab] = useState('highlights');
	// An approved requirement is locked, so its composer is hidden. This
	// reopens it to take the ask for the next version.
	const [continuing, setContinuing] = useState(false);
	// Set the moment we send, cleared only when the server reports a reply.
	// Without it an in-flight poll can clear is_thinking and re-enable Send.
	const pendingRef = useRef(false);

	const replyRef = useRef(null);
	const scrollRef = useRef(null);
	const pollRef = useRef(null);
	const base = `/api/v1/apps/${appId}/agent-mode`;

	const openRun = useCallback((uuid) => {
		setActiveRunId(uuid);
		// A run belonging to a different build must not leave the previous
		// one's URL and credentials on screen.
		setActiveRun(null);
	}, []);

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
		// Reopening the page picks the conversation back up mid-build: runs
		// come back newest first.
		if (response.runs?.length) {
			setActiveRunId((cur) => cur || response.runs[0].uuid);
		}
		return response;
	}, [base, requirementId, specDirty]);

	useEffect(() => {
		setActiveRunId(null);
		setActiveRun(null);
		setContinuing(false);
		load();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [requirementId]);

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
	}, [req?.messages?.length, req?.is_thinking, activeRunId, continuing]);

	useEffect(() => {
		if (continuing && replyRef.current) replyRef.current.focus();
	}, [continuing]);

	// A finished build changes the requirement's run history, which is only
	// otherwise refetched while the analyst is replying.
	const finishedRef = useRef('');
	useEffect(() => {
		if (!activeRun?.status || !TERMINAL.includes(activeRun.status)) return;
		if (finishedRef.current === activeRunId) return;
		finishedRef.current = activeRunId;
		load();
	}, [activeRun?.status, activeRunId, load]);

// The next version is a new requirement: the approved one has already
	// been built, and what was agreed and what was built must keep matching.
	const startFollowUp = async () => {
		const content = reply.trim();
		if (!content || busy) return;
		setBusy(true);
		const { success, response } = await triggerApi({
			url: `${base}/requirements/`,
			type: 'POST', loader: false, payload: { prompt: content },
			showErrorModal: false,
		});
		setBusy(false);
		if (success && response?.uuid) {
			setReply('');
			setContinuing(false);
			navigate(`../requirements/${response.uuid}`);
			return;
		}
		notify('error', 'Could not start', response?.message);
	};

	const send = async (override) => {
		const content = (override ?? reply).trim();
		if (!content || req?.is_thinking) return;
		setBusy(true);
		const { success, response, responseStatus } = await triggerApi({
			url: `${base}/requirements/${requirementId}/messages/`,
			type: 'POST', loader: false, payload: { content },
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
					{ seq: (r?.messages?.length || 0) + 1, role: 'user', content },
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
			openRun(response.uuid);
			return true;
		}
		// 409 means a run is already going — show it rather than erroring.
		if (response?.run_uuid) {
			openRun(response.run_uuid);
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

	// Only the newest assistant turn can still be answered. Earlier ones need
	// no chips: the user's own reply repeats each question above its answer.
	const messages = req.messages || [];
	const lastAssistant = [...messages]
		.reverse()
		.find((m) => m.role === 'assistant');
	const openQuestions =
		!locked && !req.is_thinking && lastAssistant?.questions?.length
			? lastAssistant.questions
			: null;
	const answersReady = openQuestions ? isAnswered(openQuestions, answers) : false;

	const hasSpec = Boolean(req.spec_markdown || spec);
	const buildInFlight = Boolean(activeRun && !TERMINAL.includes(activeRun.status));
	// "partial" still produced a running app, so it counts as ready — what it
	// lost is some finishing steps, which the build card in the chat reports.
	const appReady =
		activeRun && ['success', 'partial'].includes(activeRun.status)
			? Boolean(activeRun.app_access?.url || activeRun.test_users?.length)
			: false;


	// Same box, two jobs: reply to the agent, or open the next version.
	const submit = () => (locked ? startFollowUp() : send());

	const sendAnswers = () => {
		if (!openQuestions || !answersReady) return;
		const composed = composeAnswer(openQuestions, answers);
		// Anything typed in the box is an addition to the choices, not a
		// replacement — discarding it silently would lose real intent.
		send(reply.trim() ? `${composed}\n\n${reply.trim()}` : composed);
	};

	return (
		<div className="flex min-h-0 grow gap-[12px]">
			{/* Conversation */}
			<div className="flex w-1/2 min-w-[380px] flex-col rounded-[12px] border border-[#DDE2E5] bg-white">
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
					{/* The build belongs in the thread it came from, as the last
					    thing that happened in the conversation. */}
					{activeRunId ? (
						<div className="px-[16px] py-[8px]">
							<RunLive
								key={activeRunId}
								appId={appId}
								runId={activeRunId}
								embedded
								onRun={setActiveRun}
								onSwitchRun={openRun}
							/>
						</div>
					) : null}
					{continuing ? (
						<Bubble
							message={{
								role: 'assistant',
								content:
									"Happy to keep going. What would you like to add or change? " +
									"I'll ask what I need to know, then write up the next version " +
									'for you to approve.',
							}}
						/>
					) : null}
				</div>

				{!locked || continuing ? (
					<div className="border-t border-[#F1F3F5] p-[10px]">
						{openQuestions && !locked ? (
							<div className="mb-[10px] rounded-[8px] border border-[#E5E7EB] bg-[#FAFAFF] p-[12px]">
								<QuestionAnswers
									questions={openQuestions}
									disabled={busy}
									onChange={setAnswers}
								/>
								<div className="mt-[12px] flex items-center justify-between gap-[10px]">
									<span className="font-lato text-[11px] text-[#9CA3AF]">
										{answersReady
											? 'Sensible defaults are already picked — change what you like.'
											: 'Pick an answer for each question.'}
									</span>
									<button
										onClick={sendAnswers}
										disabled={busy || !answersReady}
										className="shrink-0 rounded-[6px] bg-gradient-to-br from-[#5048ED] to-[#346BD4] px-[14px] py-[6px] font-lato text-[13px] font-medium text-white hover:opacity-90 disabled:opacity-40"
									>
										Send answers
									</button>
								</div>
							</div>
						) : null}
						<textarea
							ref={replyRef}
							value={reply}
							onChange={(e) => setReply(e.target.value)}
							onKeyDown={(e) => {
								if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) submit();
							}}
							rows={3}
							disabled={busy || (!locked && req.is_thinking)}
							placeholder={
								locked
									? 'What would you like to add or change?'
									: req.is_thinking
										? 'The agent is replying…'
										: openQuestions
											? 'Anything to add? (optional)'
											: 'Answer the questions, or ask for changes…'
							}
							className="w-full resize-none rounded-[8px] border border-[#DDE2E5] p-[8px] font-lato text-[13px] focus:border-primary focus:outline-none disabled:bg-[#F8FAFC]"
						/>
						<div className="mt-[6px] flex items-center justify-between gap-[10px]">
							<span className="font-lato text-[11px] text-[#9CA3AF]">
								{locked
									? 'This starts the next version — nothing changes until you approve it.'
									: req.is_thinking
										? 'Waiting for the agent…'
										: '⌘/Ctrl + Enter'}
							</span>
							<button
								onClick={submit}
								disabled={busy || !reply.trim() || (!locked && req.is_thinking)}
								className="rounded-[6px] bg-[#346BD4] px-[14px] py-[6px] font-lato text-[13px] font-medium text-white hover:bg-[#2556B0] disabled:opacity-40"
							>
								{busy ? 'Starting…' : req.is_thinking && !locked ? 'Replying…' : 'Send'}
							</button>
						</div>
					</div>
				) : null}
			</div>

			{/* What you're getting */}
			<div className="flex min-w-0 grow flex-col rounded-[12px] border border-[#DDE2E5] bg-white">
				<div className="flex items-center justify-between gap-[10px] border-b border-[#F1F3F5] px-[10px] py-[7px]">
					<div className="flex gap-[2px]">
						{BASE_TABS.map((tab) => (
							<button
								key={tab.id}
								onClick={() => setRightTab(tab.id)}
								className={`rounded-[6px] px-[10px] py-[5px] font-lato text-[12.5px] font-medium ${
									rightTab === tab.id
										? 'bg-[#EEF2FF] text-[#3730A3]'
										: 'text-[#6B7280] hover:bg-[#F8FAFC]'
								}`}
							>
								{tab.label}
								{tab.id === 'requirement' && req.spec_version ? ` · v${req.spec_version}` : ''}
							</button>
						))}
					</div>
					<span className="flex items-center gap-[10px]">
						{specDirty ? (
							<span className="font-lato text-[11px] text-[#B45309]">unsaved edits</span>
						) : null}
						{rightTab === 'requirement' && hasSpec && !locked ? (
							<button
								onClick={() => setEditingSpec((v) => !v)}
								className="font-lato text-[11px] font-medium text-[#6B7280] hover:text-[#111827]"
							>
								{editingSpec ? 'Preview' : 'Edit'}
							</button>
						) : null}
					</span>
				</div>

				<div className="flex min-h-0 grow flex-col overflow-hidden">
					{rightTab === 'highlights' ? (
						<div
							className={`min-h-0 grow overflow-y-auto ${
								appReady ? 'bg-gradient-to-br from-[#F5F4FF] to-[#F2F7FF]' : ''
							}`}
						>
							{appReady ? (
								<AppReadyCard appName={req.title} run={activeRun} />
							) : null}
							{appReady ? null : <SpecHighlights spec={spec} />}
						</div>
					) : hasSpec ? (
						<div className="flex min-h-0 grow flex-col overflow-y-auto">
							{editingSpec && !locked ? (
								<textarea
									value={spec}
									onChange={(e) => { setSpec(e.target.value); setSpecDirty(true); }}
									autoFocus
									className="min-h-[360px] grow resize-none p-[16px] font-mono text-[12px] leading-[18px] text-[#111827] focus:outline-none"
								/>
							) : (
								<div className="p-[16px] font-lato text-[13px] leading-[19px] text-[#111827]">
									<Markdown text={spec} />
								</div>
							)}
						</div>
					) : (
						<div className="flex grow items-center justify-center px-[24px] text-center">
							<p className="font-lato text-[13px] leading-[20px] text-[#9CA3AF]">
								The agent is working out what you need.
								<br />
								Once the requirement is clear it will appear here for review.
							</p>
						</div>
					)}
				</div>

				{hasSpec ? (
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
								<button
									onClick={appReady ? () => setContinuing(true) : build}
									disabled={busy || buildInFlight || (appReady && continuing)}
									className="rounded-[8px] bg-gradient-to-br from-[#5048ED] to-[#346BD4] px-[16px] py-[8px] font-lato text-[13px] font-medium text-white hover:opacity-90 disabled:opacity-40"
								>
									{buildInFlight
										? 'Building…'
										: appReady
											? 'Continue building →'
											: req.runs?.length
												? 'Build again'
												: 'Start build'}
								</button>
							</>
						)}
					</div>
				) : null}

				{req.runs?.length > 1 ? (
					<div className="border-t border-[#F1F3F5]">
						<div className="px-[16px] pb-[4px] pt-[10px] font-lato text-[11px] font-bold uppercase tracking-[0.06em] text-[#6B7280]">
							Earlier builds
						</div>
						<div className="max-h-[140px] overflow-y-auto pb-[6px]">
							{req.runs.map((run) => {
								const rm = RUN_META[run.status] || RUN_META.queued;
								return (
									<button
										key={run.uuid}
										onClick={() => openRun(run.uuid)}
										className={`flex w-full items-center gap-[10px] px-[16px] py-[7px] text-left hover:bg-[#F8FAFC] ${
											run.uuid === activeRunId ? 'bg-[#F8FAFC]' : ''
										}`}
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
