/**
 * Build with Agent — the step before an app exists.
 *
 * The user has no app yet, so there is nothing to name, configure or upload.
 * They describe what they need in one message; the agent picks the name,
 * launches the app in the background, and opens a requirement conversation
 * inside it seeded with that same message. From there this page hands over to
 * the ordinary Agent Mode chat, which is why it deliberately borrows that
 * page's chrome — the transition should read as one continuous conversation.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import toast from 'react-hot-toast';
import { useNavigate, useParams } from 'react-router-dom';
import Toast from '../../../components/Notifications/Toast';
import useApi from '../../../hooks/useApi';

const POLL_MS = 2500;
// The app is already built by the time the hand-off runs, so a transient
// failure is worth retrying — but a persistent one needs to stop and say so.
const MAX_HANDOFF_ATTEMPTS = 4;
const BASE = '/api/v1/platform/agent-mode';

const REASON_TEXT = {
	feature_disabled: 'Build with AI is disabled. Set AGENT_MODE_ENABLED=True.',
	sdk_not_installed: 'The Claude Agent SDK is not installed on the server.',
	cli_not_found: 'The Claude Code binary could not be found.',
	no_credentials: 'No Anthropic API key is configured for the platform.',
	skill_plugin_missing: 'The Zango skill plugin is missing from the install.',
	no_worker: 'No Celery worker is consuming the agent_mode queue.',
};

const PLACEHOLDER =
	'e.g. a way for our clinic staff to book patient appointments and record whether the patient turned up';

function notify(type, title, description) {
	toast.custom(
		(t) => (
			<Toast type={type} toastRef={t} title={title} description={description} />
		),
		{ duration: 5000, position: 'bottom-left' }
	);
}

function Bubble({ role, children }) {
	const isUser = role === 'user';
	return (
		<div
			className={`flex ${isUser ? 'justify-end' : 'justify-start'} px-[16px] py-[6px]`}
		>
			<div
				className={`max-w-[85%] rounded-[10px] border px-[12px] py-[8px] font-lato text-[13px] leading-[19px] ${
					isUser
						? 'whitespace-pre-wrap border-[#C7D2FE] bg-[#EEF2FF] text-[#312E81]'
						: 'border-[#EDEFF1] bg-[#F7F8FA] text-[#111827]'
				}`}
			>
				{children}
			</div>
		</div>
	);
}

/** One line of the launch checklist: pending, running, or done. */
function Step({ state, label, detail }) {
	const colour = {
		done: '#047857',
		running: '#5048ED',
		pending: '#9CA3AF',
		failed: '#DC2626',
	}[state];

	return (
		<li className="flex items-start gap-[10px] py-[5px]">
			<span
				className="mt-[4px] flex h-[14px] w-[14px] shrink-0 items-center justify-center rounded-full border-[1.5px]"
				style={{
					borderColor: colour,
					backgroundColor: state === 'done' ? colour : 'transparent',
				}}
			>
				{state === 'done' ? (
					<svg width="8" height="8" viewBox="0 0 12 12" fill="none">
						<path
							d="M2.5 6.2L4.8 8.5L9.5 3.5"
							stroke="white"
							strokeWidth="2"
							strokeLinecap="round"
							strokeLinejoin="round"
						/>
					</svg>
				) : null}
				{state === 'running' ? (
					<span
						className="h-[6px] w-[6px] animate-pulse rounded-full"
						style={{ backgroundColor: colour }}
					/>
				) : null}
			</span>
			<span className="min-w-0">
				<span
					className="font-lato text-[13px] leading-[19px]"
					style={{
						color: state === 'pending' ? '#9CA3AF' : '#111827',
						fontWeight: state === 'running' ? 600 : 400,
					}}
				>
					{label}
				</span>
				{detail ? (
					<span className="ml-[6px] font-mono text-[12px] text-[#6B7280]">
						{detail}
					</span>
				) : null}
			</span>
		</li>
	);
}

export default function BuildWithAgent() {
	const { scaffoldId } = useParams();
	const navigate = useNavigate();
	const triggerApi = useApi();

	const [availability, setAvailability] = useState(null);
	const [prompt, setPrompt] = useState('');
	const [scaffold, setScaffold] = useState(null);
	const [busy, setBusy] = useState(false);
	const [handoffFailures, setHandoffFailures] = useState(0);
	// The hand-off is a POST, and polling would otherwise fire it repeatedly
	// while the first call is still in flight.
	const handingOffRef = useRef(false);
	const scrollRef = useRef(null);

	useEffect(() => {
		let cancelled = false;
		(async () => {
			const { response, success } = await triggerApi({
				url: `${BASE}/availability/`,
				type: 'GET',
				loader: false,
				showErrorModal: false,
			});
			if (!cancelled && success && response) setAvailability(response);
		})();
		return () => {
			cancelled = true;
		};
	}, []);

	const load = useCallback(
		async (uuid) => {
			const { response, success } = await triggerApi({
				url: `${BASE}/scaffolds/${uuid}/`,
				type: 'GET',
				loader: false,
				showErrorModal: false,
			});
			if (success && response) {
				setScaffold(response);
				return response;
			}
			return null;
		},
		[]
	);

	// Resume: the scaffold id lives in the URL, so a reload mid-creation
	// rejoins the same launch rather than starting a second app.
	useEffect(() => {
		if (scaffoldId && scaffold?.uuid !== scaffoldId) load(scaffoldId);
	}, [scaffoldId]);

	const handOff = useCallback(
		async (current) => {
			if (handingOffRef.current) return;
			handingOffRef.current = true;
			const { response, success } = await triggerApi({
				url: `${BASE}/scaffolds/${current.uuid}/requirement/`,
				type: 'POST',
				payload: {},
				loader: false,
				showErrorModal: false,
			});
			handingOffRef.current = false;
			if (success && response?.requirement_uuid) {
				setScaffold(response);
				navigate(
					`/platform/apps/${response.app_uuid}/agent-mode/requirements/${response.requirement_uuid}`,
					{ replace: true }
				);
				return;
			}
			// The app itself is built by now, so this is worth retrying rather
			// than abandoning — but not forever, and not one toast per poll.
			setHandoffFailures((n) => {
				if (n === 0) {
					notify(
						'error',
						'Could not open the conversation',
						response?.message || 'Retrying…'
					);
				}
				return n + 1;
			});
		},
		[navigate]
	);

	// Poll while the app is being built, and hand over the moment it is ready.
	useEffect(() => {
		if (!scaffold?.uuid) return undefined;
		if (scaffold.status === 'failed') return undefined;
		if (scaffold.requirement_uuid) return undefined;
		if (handoffFailures >= MAX_HANDOFF_ATTEMPTS) return undefined;

		if (scaffold.app_state === 'ready') handOff(scaffold);

		const timer = setInterval(async () => {
			// Re-read rather than trusting the closure: the hand-off must fire
			// against the state the server just reported, not the state that
			// set this interval up.
			const current = await load(scaffold.uuid);
			if (current?.app_state === 'ready' && !current.requirement_uuid) {
				handOff(current);
			}
		}, POLL_MS);
		return () => clearInterval(timer);
	}, [
		scaffold?.uuid,
		scaffold?.status,
		scaffold?.app_state,
		scaffold?.requirement_uuid,
		handoffFailures,
		load,
		handOff,
	]);

	useEffect(() => {
		if (scrollRef.current) {
			scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
		}
	}, [scaffold?.status, scaffold?.app_state, scaffold?.app_name]);

	const start = async () => {
		if (!prompt.trim() || busy) return;
		setBusy(true);
		const { response, success } = await triggerApi({
			url: `${BASE}/scaffolds/`,
			type: 'POST',
			payload: { prompt: prompt.trim() },
			loader: false,
			showErrorModal: false,
		});
		setBusy(false);
		if (success && response?.uuid) {
			setScaffold(response);
			navigate(`/platform/build-with-agent/${response.uuid}`, { replace: true });
		} else {
			notify(
				'error',
				'Could not start',
				response?.message || 'Please try again.'
			);
		}
	};

	const startOver = () => {
		handingOffRef.current = false;
		setHandoffFailures(0);
		setScaffold(null);
		setPrompt('');
		navigate('/platform/build-with-agent', { replace: true });
	};

	const blocked = availability && !availability.available;
	const started = Boolean(scaffold);
	const failed = scaffold?.status === 'failed';
	const appFailed = scaffold?.app_state === 'failed';
	// The app exists but the conversation would not open. Distinct from a
	// failed launch: there is something to salvage, so never offer "start over".
	const stuck = handoffFailures >= MAX_HANDOFF_ATTEMPTS;

	const namingState = failed && !scaffold?.app_name
		? 'failed'
		: scaffold?.app_name
			? 'done'
			: 'running';
	const creatingState = appFailed
		? 'failed'
		: scaffold?.app_state === 'ready'
			? 'done'
			: scaffold?.app_name
				? 'running'
				: 'pending';
	const handoffState = scaffold?.requirement_uuid
		? 'done'
		: creatingState === 'done'
			? 'running'
			: 'pending';

	return (
		<div className="flex h-full flex-col overflow-hidden bg-[#F8FAFC]">
			<div className="flex-shrink-0 border-b border-[#E5E7EB] bg-white px-[40px] py-[20px]">
				<button
					onClick={() => navigate('/platform/apps')}
					className="font-lato text-[12px] font-medium text-[#6B7280] hover:text-[#111827]"
				>
					← All apps
				</button>
				<div className="mt-[8px] flex items-center gap-[12px]">
					<div className="flex h-[40px] w-[40px] items-center justify-center rounded-[8px] bg-gradient-to-br from-[#5048ED] to-[#346BD4] shadow-lg">
						<svg width="22" height="22" viewBox="0 0 24 24" fill="none">
							<path
								d="M12 2L13.09 8.26L18 6L14.74 10.91L21 12L14.74 13.09L18 18L13.09 15.74L12 22L10.91 15.74L6 18L9.26 13.09L3 12L9.26 10.91L6 6L10.91 8.26L12 2Z"
								stroke="white"
								strokeWidth="1.5"
								strokeLinejoin="round"
								fill="none"
							/>
						</svg>
					</div>
					<div>
						<h1 className="font-source-sans-pro text-[24px] font-semibold leading-[32px] text-[#111827]">
							Build with Agent
						</h1>
						<p className="font-lato text-[14px] leading-[20px] text-[#6B7280]">
							Describe what you need — the agent names and launches the app,
							then builds it with you
						</p>
					</div>
				</div>
			</div>

			{blocked ? (
				<div className="mx-[40px] mt-[20px] rounded-[8px] border border-[#FCD34D] bg-[#FFFBEB] px-[16px] py-[12px]">
					<p className="font-lato text-[13px] font-semibold text-[#92400E]">
						Build with AI is not ready on this platform
					</p>
					<ul className="mt-[4px] list-disc pl-[18px]">
						{availability.reasons.map((r) => (
							<li key={r} className="font-lato text-[13px] text-[#92400E]">
								{REASON_TEXT[r] || r}
							</li>
						))}
					</ul>
				</div>
			) : null}

			<div className="flex min-h-0 grow justify-center px-[40px] py-[24px]">
				<div className="flex min-h-0 w-full max-w-[760px] flex-col rounded-[12px] border border-[#DDE2E5] bg-white">
					<div ref={scrollRef} className="min-h-0 grow overflow-y-auto py-[12px]">
						<Bubble role="assistant">
							What do you want to build? Describe it in a sentence or two, the
							way you would explain it to a colleague — no technical detail
							needed. I&apos;ll name the app, set it up, and then ask you a few
							questions before anything gets built.
						</Bubble>

						{started ? (
							<>
								<Bubble role="user">{scaffold.prompt}</Bubble>
								<Bubble role="assistant">
									<p className="mb-[6px]">
										{failed || appFailed
											? 'I ran into a problem setting the app up.'
											: scaffold.app_state === 'ready'
												? `Your app is ready. Opening the conversation…`
												: 'Good — setting your app up now. This takes a minute.'}
									</p>
									<ul className="mt-[8px]">
										<Step
											state={namingState}
											label="Choosing a name"
											detail={scaffold.app_name || ''}
										/>
										<Step
											state={creatingState}
											label={
												scaffold.app_label
													? `Creating ${scaffold.app_label}`
													: 'Creating the app'
											}
										/>
										<Step
											state={handoffState}
											label="Opening your requirement"
										/>
									</ul>
									{scaffold.app_description && !failed ? (
										<p className="mt-[8px] border-t border-[#E5E7EB] pt-[8px] text-[#6B7280]">
											{scaffold.app_description}
										</p>
									) : null}
								</Bubble>
							</>
						) : null}

						{failed || appFailed || stuck ? (
							<div className="mx-[16px] my-[8px] rounded-[6px] bg-[#FEF2F2] px-[10px] py-[8px] font-lato text-[12px] text-[#B91C1C]">
								{stuck && !failed && !appFailed
									? `${scaffold?.app_label || 'Your app'} was created, but the conversation could not be opened. Try again, or open Build with AI from the app itself.`
									: scaffold?.error_message ||
										'The app could not be created. Check the platform logs, then try again.'}
							</div>
						) : null}
					</div>

					<div className="border-t border-[#F1F3F5] p-[12px]">
						{started ? (
							<div className="flex items-center justify-between gap-[12px]">
								<span className="font-lato text-[12px] text-[#9CA3AF]">
									{failed || appFailed
										? 'Nothing was left half-built — you can try again.'
										: stuck
											? 'Your app is safe; only the hand-off failed.'
											: 'You can leave this page; the app keeps building.'}
								</span>
								{failed || appFailed ? (
									<button
										onClick={startOver}
										className="shrink-0 rounded-[6px] border border-[#DDE2E5] px-[14px] py-[6px] font-lato text-[13px] font-medium text-[#212429] hover:bg-[#F0F3F4]"
									>
										Start over
									</button>
								) : null}
								{stuck && !failed && !appFailed ? (
									<span className="flex shrink-0 items-center gap-[8px]">
										<button
											onClick={() =>
												navigate(
													`/platform/apps/${scaffold.app_uuid}/agent-mode`
												)
											}
											className="rounded-[6px] border border-[#DDE2E5] px-[14px] py-[6px] font-lato text-[13px] font-medium text-[#212429] hover:bg-[#F0F3F4]"
										>
											Open the app
										</button>
										<button
											onClick={() => setHandoffFailures(0)}
											className="rounded-[6px] bg-[#346BD4] px-[14px] py-[6px] font-lato text-[13px] font-medium text-white hover:bg-[#2556B0]"
										>
											Try again
										</button>
									</span>
								) : null}
							</div>
						) : (
							<>
								<textarea
									value={prompt}
									onChange={(e) => setPrompt(e.target.value)}
									onKeyDown={(e) => {
										if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) start();
									}}
									rows={3}
									autoFocus
									disabled={blocked || busy}
									placeholder={PLACEHOLDER}
									className="w-full resize-none rounded-[8px] border border-[#DDE2E5] p-[10px] font-lato text-[13px] leading-[19px] focus:border-primary focus:outline-none disabled:bg-[#F8FAFC]"
								/>
								<div className="mt-[8px] flex items-center justify-between">
									<span className="font-lato text-[11px] text-[#9CA3AF]">
										⌘/Ctrl + Enter
									</span>
									<button
										onClick={start}
										data-cy="build_with_agent_submit"
										disabled={blocked || busy || !prompt.trim()}
										className="rounded-[8px] bg-gradient-to-br from-[#5048ED] to-[#346BD4] px-[16px] py-[9px] font-lato text-[14px] font-medium text-white hover:opacity-90 disabled:opacity-40"
									>
										{busy ? 'Starting…' : 'Build it'}
									</button>
								</div>
							</>
						)}
					</div>
				</div>
			</div>
		</div>
	);
}
