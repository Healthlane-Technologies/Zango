/**
 * Build with AI — one screen, the whole history of the app.
 *
 * There used to be a list of requirements you picked from before you could
 * talk to anything. But a requirement is not a document you file, it is a
 * round of the same conversation: you ask for something, agree it, build it,
 * then ask for the next thing. So every round lives in one thread, in order,
 * with the build that came out of it.
 *
 * A round is an `AgentRequirement` on the wire and `versions[i]` here, but it
 * is never called a version to the user — the first one is the Initial Build
 * and the rest are Enhancements, which is what they actually are. (`version`
 * already means something else nearby: `spec_version` counts revisions
 * *inside* one round.)
 *
 * Only the newest round is live. Earlier ones are approved and built — their
 * spec is fixed, because what was agreed and what was built have to keep
 * matching — so they read as history and the composer belongs to the last
 * one.
 *
 * Right is what you are getting: the requirement while it is being agreed,
 * and the live app's address, sign-ins, Share and Deploy once one exists.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import toast from 'react-hot-toast';
import { useParams } from 'react-router-dom';
import Toast from '../../../components/Notifications/Toast';
import useApi from '../../../hooks/useApi';
import AppReadyCard from './AppReadyCard';
import Markdown from './Markdown';
import QuestionAnswers, { composeAnswer, isAnswered } from './QuestionAnswers';
import RunLive, { TERMINAL } from './RunLive';
import SpecHighlights from './SpecHighlights';

const POLL_MS = 1500;

const TABS = [
	{ id: 'highlights', label: 'My Build' },
	{ id: 'requirement', label: 'Requirement' },
];

const STATUS_META = {
	gathering: { label: 'Gathering', bg: '#EEF2FF', accent: '#5048ED' },
	ready: { label: 'Ready for review', bg: '#FEF3C7', accent: '#B45309' },
	approved: { label: 'Built', bg: '#ECFDF5', accent: '#047857' },
	abandoned: { label: 'Abandoned', bg: '#F3F4F6', accent: '#6B7280' },
};

const PLACEHOLDER =
	'e.g. a way for staff to book patient appointments and track whether they were attended';

function notify(type, title, description) {
	toast.custom(
		(t) => <Toast type={type} toastRef={t} title={title} description={description} />,
		{ duration: 5000, position: 'bottom-left' }
	);
}

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

function roundLabel(index) {
	return index === 0 ? 'Initial Build' : `Enhancement ${index}`;
}

/** Compact and unambiguous: the year only appears when it is not this one. */
function stamp(iso) {
	if (!iso) return '';
	const when = new Date(iso);
	if (Number.isNaN(when.getTime())) return '';
	const opts = { day: 'numeric', month: 'short' };
	if (when.getFullYear() !== new Date().getFullYear()) opts.year = 'numeric';
	return `${when.toLocaleDateString(undefined, opts)} · ${when.toLocaleTimeString(
		undefined,
		{ hour: '2-digit', minute: '2-digit' }
	)}`;
}

/** Where one round ends and the next begins. */
function RoundRule({ index, requirement }) {
	const meta = STATUS_META[requirement.status] || STATUS_META.gathering;
	const when = stamp(requirement.created_at);
	return (
		<div className="flex items-center gap-[10px] px-[16px] pb-[4px] pt-[14px]">
			<span className="h-px w-[16px] shrink-0 bg-[#EDEFF1]" />
			<span className="shrink-0 font-lato text-[11px] font-bold uppercase tracking-[0.06em] text-[#6B7280]">
				{roundLabel(index)}
			</span>
			{when ? (
				<span className="shrink-0 font-lato text-[11px] text-[#9CA3AF]">{when}</span>
			) : null}
			{requirement.title ? (
				<span className="min-w-0 truncate font-lato text-[12px] text-[#9CA3AF]">
					{requirement.title}
				</span>
			) : null}
			<span className="h-px grow bg-[#EDEFF1]" />
			<span
				className="shrink-0 rounded-full px-[8px] py-[2px] font-lato text-[10px] font-bold uppercase tracking-[0.05em]"
				style={{ backgroundColor: meta.bg, color: meta.accent }}
			>
				{meta.label}
			</span>
		</div>
	);
}

export default function BuildThread() {
	const { appId } = useParams();
	const triggerApi = useApi();

	// Oldest first: the thread reads top to bottom like any conversation.
	const [versions, setVersions] = useState(null);
	const [runs, setRuns] = useState({});
	const [reply, setReply] = useState('');
	const [spec, setSpec] = useState('');
	const [specDirty, setSpecDirty] = useState(false);
	const [editingSpec, setEditingSpec] = useState(false);
	const [busy, setBusy] = useState(false);
	const [answers, setAnswers] = useState({});
	const [rightTab, setRightTab] = useState('highlights');
	// Which version's requirement is on screen. null follows the newest,
	// so starting a round never leaves you reading a stale spec.
	const [specIdx, setSpecIdx] = useState(null);
	// The newest version is approved and built, and the user wants another
	// round. Reopens the composer to take the next ask.
	const [continuing, setContinuing] = useState(false);
	// Set the moment we send, cleared only when the server reports a reply.
	// Without it an in-flight poll can clear is_thinking and re-enable Send.
	const pendingRef = useRef(false);

	const replyRef = useRef(null);
	const scrollRef = useRef(null);
	const pollRef = useRef(null);
	const base = `/api/v1/apps/${appId}/agent-mode`;

	const active = versions?.length ? versions[versions.length - 1] : null;

	const loadAll = useCallback(async () => {
		const { response, success } = await triggerApi({
			url: `${base}/requirements/?page_size=50`,
			type: 'GET', loader: false, showErrorModal: false,
		});
		if (!success || !response) {
			setVersions([]);
			return;
		}
		// The list comes back newest first; the thread wants the opposite.
		const rows = [...(response.requirements?.records || [])].reverse();
		const details = await Promise.all(
			rows.map((row) =>
				triggerApi({
					url: `${base}/requirements/${row.uuid}/`,
					type: 'GET', loader: false, showErrorModal: false,
				}).then((r) => (r.success ? r.response : null))
			)
		);
		const loaded = details.filter(Boolean);
		setVersions(loaded);
		const newest = loaded[loaded.length - 1];
		setSpec((cur) => (specDirty ? cur : newest?.spec_markdown || ''));
	}, [base, specDirty]);

	// Only the newest version can change: everything before it is approved and
	// built, so re-fetching the whole thread on every tick would be waste.
	const reloadActive = useCallback(async () => {
		if (!active?.uuid) return null;
		const { response, success } = await triggerApi({
			url: `${base}/requirements/${active.uuid}/`,
			type: 'GET', loader: false, showErrorModal: false,
		});
		if (!success || !response) return null;
		// A newly-arrived reply means the turn really is over.
		if (response.is_thinking === false && (response.messages || []).length) {
			const last = response.messages[response.messages.length - 1];
			if (last.role === 'assistant') pendingRef.current = false;
		}
		const merged = {
			...response,
			is_thinking: response.is_thinking || pendingRef.current,
		};
		setVersions((vs) =>
			(vs || []).map((v) => (v.uuid === merged.uuid ? merged : v))
		);
		// Never clobber unsaved edits with the server copy.
		setSpec((cur) => (specDirty ? cur : response.spec_markdown || ''));
		return merged;
	}, [base, active?.uuid, specDirty]);

	useEffect(() => {
		setVersions(null);
		setRuns({});
		setContinuing(false);
		loadAll();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [appId]);

	// Poll only while the agent is composing a reply.
	useEffect(() => {
		if (!active?.is_thinking) {
			if (pollRef.current) clearInterval(pollRef.current);
			pollRef.current = null;
			return undefined;
		}
		pollRef.current = setInterval(reloadActive, POLL_MS);
		return () => {
			if (pollRef.current) clearInterval(pollRef.current);
			pollRef.current = null;
		};
	}, [active?.is_thinking, reloadActive]);

	useEffect(() => {
		if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
	}, [versions?.length, active?.messages?.length, active?.is_thinking, continuing]);

	useEffect(() => {
		if (continuing && replyRef.current) replyRef.current.focus();
	}, [continuing]);

	const recordRun = useCallback((run) => {
		if (!run?.uuid) return;
		setRuns((prev) => ({ ...prev, [run.uuid]: run }));
	}, []);

	// A finished build changes the version's run history and its status.
	const finishedRef = useRef('');
	const activeRunUuid = active?.runs?.[0]?.uuid || null;
	const activeRun = activeRunUuid ? runs[activeRunUuid] : null;
	useEffect(() => {
		if (!activeRun?.status || !TERMINAL.includes(activeRun.status)) return;
		if (finishedRef.current === activeRunUuid) return;
		finishedRef.current = activeRunUuid;
		reloadActive();
	}, [activeRun?.status, activeRunUuid, reloadActive]);

	// The app is live regardless of which version built it, so the card must
	// survive starting a new version that has not been built yet.
	const appRun = useMemo(() => {
		const ordered = [];
		[...(versions || [])].reverse().forEach((v) =>
			(v.runs || []).forEach((r) => ordered.push(r.uuid))
		);
		return (
			ordered
				.map((uuid) => runs[uuid])
				.find(
					(r) =>
						r &&
						['success', 'partial'].includes(r.status) &&
						(r.app_access?.url || r.test_users?.length)
				) || null
		);
	}, [versions, runs]);

	const startRound = async (content) => {
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
			// Follow the newest again: having explicitly opened an old version
			// should not leave you reading it once a new round starts.
			setSpecIdx(null);
			pendingRef.current = true;
			await loadAll();
			return;
		}
		notify('error', 'Could not start', response?.message);
	};

	const send = async (override) => {
		const content = (override ?? reply).trim();
		if (!content || active?.is_thinking) return;
		setBusy(true);
		const { success, response, responseStatus } = await triggerApi({
			url: `${base}/requirements/${active.uuid}/messages/`,
			type: 'POST', loader: false, payload: { content },
			showErrorModal: false,
		});
		setBusy(false);
		if (success) {
			pendingRef.current = true;
			setReply('');
			setVersions((vs) =>
				(vs || []).map((v) =>
					v.uuid === active.uuid
						? {
								...v,
								is_thinking: true,
								messages: [
									...(v.messages || []),
									{ seq: (v.messages?.length || 0) + 1, role: 'user', content },
								],
							}
						: v
				)
			);
		} else if (responseStatus === 409) {
			// The agent was still replying. Keep the text so nothing is lost
			// and reflect the real state instead of reporting a failure.
			pendingRef.current = true;
			setVersions((vs) =>
				(vs || []).map((v) =>
					v.uuid === active.uuid ? { ...v, is_thinking: true } : v
				)
			);
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
			url: `${base}/requirements/${active.uuid}/spec/`,
			type: 'POST', loader: false, payload: { spec_markdown: spec },
			showErrorModal: false,
		});
		setBusy(false);
		if (success) {
			setSpecDirty(false);
			notify('success', 'Requirement saved', `Revision ${response?.spec_version}`);
			reloadActive();
		} else {
			notify('error', 'Could not save', response?.message);
		}
	};

	const startRun = async () => {
		const { success, response } = await triggerApi({
			url: `${base}/runs/`, type: 'POST', loader: false,
			payload: { requirement_uuid: active.uuid }, showErrorModal: false,
		});
		// Either way the version's run list is what the thread renders from,
		// so refetch rather than splicing a run in by hand.
		if (success || response?.run_uuid) {
			await reloadActive();
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
			url: `${base}/requirements/${active.uuid}/approve/`,
			type: 'POST', loader: false, payload: {}, showErrorModal: false,
		});
		if (!success) {
			setBusy(false);
			notify('error', 'Could not approve', response?.message);
			return;
		}
		const ok = await startRun();
		setBusy(false);
		if (!ok) reloadActive();
	};

	if (versions === null) return null;

	const locked = active?.status === 'approved';
	// Open unless the newest version is already built and the user has not
	// asked for another round.
	const composing = !active || !locked || continuing;

	// Only the newest assistant turn can still be answered. Earlier ones need
	// no chips: the user's own reply repeats each question above its answer.
	const lastAssistant = [...(active?.messages || [])]
		.reverse()
		.find((m) => m.role === 'assistant');
	const openQuestions =
		active && !locked && !active.is_thinking && lastAssistant?.questions?.length
			? lastAssistant.questions
			: null;
	const answersReady = openQuestions ? isAnswered(openQuestions, answers) : false;

	const viewedIdx =
		specIdx !== null && specIdx < versions.length ? specIdx : versions.length - 1;
	const viewed = versions[viewedIdx] || null;
	const viewingActive = Boolean(viewed && viewed.uuid === active?.uuid);
	// The active version's spec is the editable local copy; every earlier
	// one is fixed, so it comes straight off the record.
	const viewedSpec = viewingActive ? spec : viewed?.spec_markdown || '';
	const hasSpec = Boolean(viewedSpec);
	const canEditSpec = viewingActive && !locked;
	const buildInFlight = Boolean(activeRun && !TERMINAL.includes(activeRun.status));
	const appReady = Boolean(appRun);

	// One box, three jobs: the first ask, a reply to the agent, or the next
	// version. Which one it is follows from where the thread has got to.
	const submit = () => {
		const content = reply.trim();
		if (!content || busy) return;
		if (!active || locked) startRound(content);
		else send();
	};

	const sendAnswers = () => {
		if (!openQuestions || !answersReady) return;
		const composed = composeAnswer(openQuestions, answers);
		// Anything typed in the box is an addition to the choices, not a
		// replacement — discarding it silently would lose real intent.
		send(reply.trim() ? `${composed}\n\n${reply.trim()}` : composed);
	};

	return (
		<div className="flex min-h-0 grow gap-[12px]">
			{/* The thread */}
			<div className="flex w-1/2 min-w-[380px] flex-col rounded-[12px] border border-[#DDE2E5] bg-white">
				<div ref={scrollRef} className="min-h-0 grow overflow-y-auto py-[8px]">
					{versions.length === 0 ? (
						<Bubble
							message={{
								role: 'assistant',
								content:
									"What do you want to build? Describe it in a sentence or two, the way you'd explain it to a colleague — no technical detail needed. I'll ask what I need to know, then write it up for you to approve before anything is built.",
							}}
						/>
					) : null}

					{versions.map((version, index) => {
						const isActive = version.uuid === active?.uuid;
						const runUuid = version.runs?.[0]?.uuid;
						return (
							<div key={version.uuid}>
								{versions.length > 1 || !isActive ? (
									<RoundRule index={index} requirement={version} />
								) : null}
								{(version.messages || []).map((m) => (
									<Bubble key={`${version.uuid}-${m.seq}`} message={m} />
								))}
								{isActive && version.is_thinking ? (
									<div className="px-[16px] py-[6px] font-lato text-[12px] italic text-[#9CA3AF]">
										Thinking…
									</div>
								) : null}
								{isActive && version.error_message ? (
									<div className="mx-[16px] my-[8px] rounded-[6px] bg-[#FEF2F2] px-[10px] py-[8px] font-lato text-[12px] text-[#B91C1C]">
										{version.error_message}
									</div>
								) : null}
								{/* The build belongs in the version it came from, as the
								    last thing that happened in that round. */}
								{runUuid ? (
									<div className="px-[16px] py-[8px]">
										<RunLive
											key={runUuid}
											appId={appId}
											runId={runUuid}
											embedded
											onRun={recordRun}
											onSwitchRun={() => reloadActive()}
										/>
									</div>
								) : null}
							</div>
						);
					})}

					{continuing ? (
						<Bubble
							message={{
								role: 'assistant',
								content:
									'Happy to keep going. What would you like to add or change? ' +
									"I'll ask what I need to know, then write it up " +
									'for you to approve.',
							}}
						/>
					) : null}
				</div>

				{composing ? (
					<div className="border-t border-[#F1F3F5] p-[10px]">
						{openQuestions ? (
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
							autoFocus={!active}
							disabled={busy || Boolean(active && !locked && active.is_thinking)}
							placeholder={
								!active
									? PLACEHOLDER
									: locked
										? 'What would you like to add or change?'
										: active.is_thinking
											? 'The agent is replying…'
											: openQuestions
												? 'Anything to add? (optional)'
												: 'Answer the questions, or ask for changes…'
							}
							className="w-full resize-none rounded-[8px] border border-[#DDE2E5] p-[8px] font-lato text-[13px] focus:border-primary focus:outline-none disabled:bg-[#F8FAFC]"
						/>
						<div className="mt-[6px] flex items-center justify-between gap-[10px]">
							<span className="font-lato text-[11px] text-[#9CA3AF]">
								{!active
									? '⌘/Ctrl + Enter'
									: locked
										? 'This starts the next enhancement — nothing changes until you approve it.'
										: active.is_thinking
											? 'Waiting for the agent…'
											: '⌘/Ctrl + Enter'}
							</span>
							<button
								onClick={submit}
								disabled={
									busy ||
									!reply.trim() ||
									Boolean(active && !locked && active.is_thinking)
								}
								className="rounded-[6px] bg-[#346BD4] px-[14px] py-[6px] font-lato text-[13px] font-medium text-white hover:bg-[#2556B0] disabled:opacity-40"
							>
								{busy
									? 'Starting…'
									: active && !locked && active.is_thinking
										? 'Replying…'
										: 'Send'}
							</button>
						</div>
					</div>
				) : null}
			</div>

			{/* What you're getting */}
			<div className="flex min-w-0 grow flex-col rounded-[12px] border border-[#DDE2E5] bg-white">
				<div className="flex items-center justify-between gap-[10px] border-b border-[#F1F3F5] px-[10px] py-[7px]">
					<div className="flex gap-[2px]">
						{TABS.map((tab) => (
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
							</button>
						))}
					</div>
					<span className="flex items-center gap-[10px]">
						{specDirty ? (
							<span className="font-lato text-[11px] text-[#B45309]">unsaved edits</span>
						) : null}
						{rightTab === 'requirement' && hasSpec && canEditSpec ? (
							<button
								onClick={() => setEditingSpec((v) => !v)}
								className="font-lato text-[11px] font-medium text-[#6B7280] hover:text-[#111827]"
							>
								{editingSpec ? 'Preview' : 'Edit'}
							</button>
						) : null}
					</span>
				</div>

				{rightTab === 'requirement' && versions.length > 1 ? (
					<div className="flex items-center gap-[6px] overflow-x-auto border-b border-[#F1F3F5] px-[10px] py-[6px]">
						{versions.map((v, i) => {
							const m = STATUS_META[v.status] || STATUS_META.gathering;
							const on = i === viewedIdx;
							return (
								<button
									key={v.uuid}
									onClick={() => setSpecIdx(i)}
									title={v.title || roundLabel(i)}
									className={`flex shrink-0 flex-col items-start gap-[1px] rounded-[9px] border px-[10px] py-[5px] text-left font-lato ${
										on
											? 'border-[#5048ED] bg-[#EEF2FF] text-[#3730A3]'
											: 'border-[#DDE2E5] bg-white text-[#6B7280] hover:border-[#9CA3AF]'
									}`}
								>
									<span className="flex items-center gap-[6px] text-[12px] font-semibold">
										{roundLabel(i)}
										<span
											className="h-[6px] w-[6px] rounded-full"
											style={{ backgroundColor: m.accent }}
										/>
									</span>
									<span className="text-[10.5px] text-[#9CA3AF]">{stamp(v.created_at)}</span>
								</button>
							);
						})}
					</div>
				) : null}

				<div className="flex min-h-0 grow flex-col overflow-hidden">
					{rightTab === 'highlights' ? (
						<div
							className={`min-h-0 grow overflow-y-auto ${
								appReady ? 'bg-gradient-to-br from-[#F5F4FF] to-[#F2F7FF]' : ''
							}`}
						>
							{appReady ? (
								<AppReadyCard appName={active?.title} run={appRun} />
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
									<Markdown text={viewedSpec} />
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

				{hasSpec && viewingActive ? (
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
									disabled={busy || active?.is_thinking}
									className="rounded-[8px] bg-gradient-to-br from-[#5048ED] to-[#346BD4] px-[16px] py-[8px] font-lato text-[13px] font-medium text-white hover:opacity-90 disabled:opacity-40"
								>
									Approve &amp; build →
								</button>
							</>
						) : (
							<button
								onClick={appReady ? () => setContinuing(true) : build}
								disabled={busy || buildInFlight || (appReady && continuing)}
								className="rounded-[8px] bg-gradient-to-br from-[#5048ED] to-[#346BD4] px-[16px] py-[8px] font-lato text-[13px] font-medium text-white hover:opacity-90 disabled:opacity-40"
							>
								{buildInFlight
									? 'Building…'
									: appReady
										? 'Continue building →'
										: active?.runs?.length
											? 'Build again'
											: 'Start build'}
							</button>
						)}
					</div>
				) : null}
			</div>
		</div>
	);
}
