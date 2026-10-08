import {
	useEffect,
	useMemo,
	useRef,
	useState,
	type FormEvent,
	type KeyboardEvent,
	type ReactNode,
} from 'react';
import {
	isRunActive,
	type AnalystQuestion,
	type Requirement,
	type RequirementMessage,
	type RunRef,
} from '@/api/agentMode';
import { useMe } from '@/api/me';
import { Avatar, Button, Icon, cx } from '@/ui';
import { Markdown } from './Markdown';
import { composeAnswer, isAnswered, seedAnswers, toggleOption, type Answers } from './questions';
import { roundLabel, runLabel, stamp, type Round } from './rounds';

const INTRO =
	"What do you want to build? Describe it in a sentence or two, the way you'd explain it to a colleague — no technical detail needed. I'll ask what I need to know, then write it up for you to approve before anything is built.";

function AgentMark() {
	return (
		<span className="ma" aria-hidden>
			<Icon name="agent" size={12} weight={2} />
		</span>
	);
}

function Message({
	message,
	fresh,
	you,
}: {
	message: Pick<RequirementMessage, 'role' | 'content' | 'ts'>;
	fresh?: boolean;
	you: string;
}) {
	const user = message.role === 'user';
	return (
		<div className={cx('msg', user && 'user', fresh && 'fresh')}>
			{user ? <Avatar name={you} small /> : <AgentMark />}
			<div className="mb">
				<div className="mn">
					{user ? 'You' : 'Zango Agent'}
					{message.ts && <small>{stamp(message.ts)}</small>}
				</div>
				{/* The user typed plain text; the agent replies in markdown. */}
				<div className="mt">{user ? message.content : <Markdown text={message.content} />}</div>
			</div>
		</div>
	);
}

function RoundRule({ round }: { round: Round }) {
	return (
		<div className="round">
			<b>{roundLabel(round.index)}</b>
			<span>{stamp(round.summary.created_at)}</span>
			<span className="min-w-0 truncate">{round.summary.title}</span>
		</div>
	);
}

/** The build that came out of a round, as the last thing that happened in it. Details live in Builds. */
function BuildMarker({ run, onOpen }: { run: RunRef; onOpen: () => void }) {
	const active = isRunActive(run.status);
	const bad = ['failed', 'timeout', 'aborted'].includes(run.status);
	return (
		<div className={cx('upd', bad && 'bad')}>
			{active ? (
				<span className="spin text-amber" />
			) : (
				<Icon name={bad ? 'alert' : 'check'} size={13} weight={2.6} />
			)}
			<span>
				<b>{runLabel(run.status)}</b>
				{run.queued_at && ` · ${stamp(run.queued_at)}`}
			</span>
			<button type="button" onClick={onOpen}>
				View build
			</button>
		</div>
	);
}

function QuestionCards({
	questions,
	disabled,
	extra,
	onSend,
}: {
	questions: AnalystQuestion[];
	disabled: boolean;
	/** Text already typed in the composer; sent as an addition to the choices. */
	extra: string;
	onSend: (content: string) => void;
}) {
	// Identity of the question set: answers reset when a new turn arrives, but survive polling.
	const key = questions.map((q) => q.id).join('|');
	const [answers, setAnswers] = useState<Answers>(() => seedAnswers(questions));
	useEffect(() => setAnswers(seedAnswers(questions)), [key]); // eslint-disable-line react-hooks/exhaustive-deps

	const ready = isAnswered(questions, answers);
	const send = () => {
		const composed = composeAnswer(questions, answers);
		onSend(extra.trim() ? `${composed}\n\n${extra.trim()}` : composed);
	};

	return (
		<div className="msg fresh">
			<AgentMark />
			<div className="mb">
				{questions.map((q, i) => {
					const a = answers[q.id] ?? { selected: [], other: '' };
					return (
						<div key={q.id} className="qc" role="group" aria-label={q.question}>
							<div className="qh">
								<b>
									Question {i + 1} of {questions.length}
								</b>
								{q.type === 'multi' && <span>Pick any</span>}
							</div>
							<h4>{q.question}</h4>
							{q.options.map((o) => {
								const on = a.selected.includes(o);
								return (
									<button
										key={o}
										type="button"
										className={cx('qo', on && 'on')}
										role={q.type === 'multi' ? 'checkbox' : 'radio'}
										aria-checked={on}
										disabled={disabled}
										onClick={() => setAnswers({ ...answers, [q.id]: toggleOption(q, a, o) })}
									>
										<span className={cx('rd', q.type === 'multi' && 'sq')}>
											{q.type === 'multi' && on && <Icon name="check" size={10} weight={3} />}
										</span>
										{o}
									</button>
								);
							})}
							{q.allow_other && (
								<div className="qother">
									<input
										value={a.other}
										disabled={disabled}
										placeholder="Something else…"
										aria-label={`Other answer: ${q.question}`}
										onChange={(e) =>
											setAnswers({ ...answers, [q.id]: { ...a, other: e.target.value } })
										}
									/>
								</div>
							)}
						</div>
					);
				})}
				<div className="mt-2.5 flex items-center gap-3">
					<span className="text-[12px] text-t3">
						{ready
							? 'The agent’s recommendations are picked — change what you like.'
							: 'Pick an answer for each question.'}
					</span>
					<Button
						variant="primary"
						size="sm"
						className="ml-auto"
						disabled={disabled || !ready}
						onClick={send}
					>
						Send answers
					</Button>
				</div>
			</div>
		</div>
	);
}

interface ThreadProps {
	rounds: Round[];
	/** Newest round; the only one the composer talks to. */
	active: Requirement | undefined;
	/** False when Agent Mode is unavailable for this app. */
	enabled: boolean;
	sending: boolean;
	/** Resolve true when the message was accepted. */
	onSend: (content: string) => Promise<boolean>;
	onNewRound: (prompt: string) => Promise<boolean>;
	onOpenBuild: (roundUuid: string) => void;
	/** Incremented to focus the composer (the header's "New change"). */
	focusSignal: number;
	/** A card from the agent after the newest message (e.g. its open decisions). */
	agentCard?: ReactNode;
}

export function Thread({
	rounds,
	active,
	enabled,
	sending,
	onSend,
	onNewRound,
	onOpenBuild,
	focusSignal,
	agentCard,
}: ThreadProps) {
	const { data: me } = useMe();
	const you = me?.name || me?.email || 'You';
	const [draft, setDraft] = useState('');
	const scrollRef = useRef<HTMLDivElement>(null);
	const inputRef = useRef<HTMLTextAreaElement>(null);
	// Messages present when a round was first seen don't animate; ones that arrive later do.
	const seenSeq = useRef(new Map<string, number>());

	const open = !!active && (active.status === 'gathering' || active.status === 'ready');
	const thinking = !!active?.is_thinking;
	// Replying to the analyst, or starting the next round once the newest one is agreed.
	const mode: 'first' | 'reply' | 'next' = !rounds.length ? 'first' : open ? 'reply' : 'next';

	const lastAssistant = useMemo(
		() => [...(active?.messages ?? [])].reverse().find((m) => m.role === 'assistant'),
		[active?.messages],
	);
	const openQuestions =
		open && !thinking && lastAssistant?.questions?.length ? lastAssistant.questions : null;

	// Stay pinned to the newest message while the user is at the bottom. Content keeps growing
	// after render (details load round by round, markdown lays out), so follow its size rather
	// than scrolling once per message.
	const contentRef = useRef<HTMLDivElement>(null);
	const pinned = useRef(true);
	useEffect(() => {
		const scroller = scrollRef.current;
		const content = contentRef.current;
		if (!scroller || !content) return;
		// Where we last put the scroller. A scroll event at or below it is our own (content kept
		// growing after we set it); only scrolling up from there means the user is reading back.
		let expectedTop = 0;
		const toBottom = () => {
			scroller.scrollTop = scroller.scrollHeight;
			expectedTop = scroller.scrollTop;
		};
		const onScroll = () => {
			if (scroller.scrollTop >= expectedTop - 4) return;
			pinned.current = scroller.scrollHeight - scroller.scrollTop - scroller.clientHeight < 80;
			if (pinned.current) expectedTop = scroller.scrollTop;
		};
		const follow = new ResizeObserver(() => {
			if (pinned.current) toBottom();
		});
		toBottom();
		scroller.addEventListener('scroll', onScroll, { passive: true });
		// The scroller shrinks too (a banner appearing above, the composer growing).
		follow.observe(content);
		follow.observe(scroller);
		return () => {
			scroller.removeEventListener('scroll', onScroll);
			follow.disconnect();
		};
	}, []);
	// Sending always returns you to the bottom, wherever you'd scrolled to.
	useEffect(() => {
		if (!sending) return;
		pinned.current = true;
		const el = scrollRef.current;
		if (el) el.scrollTop = el.scrollHeight;
	}, [sending]);

	useEffect(() => {
		if (focusSignal) inputRef.current?.focus();
	}, [focusSignal]);

	// Grow with the text, up to the CSS max-height.
	useEffect(() => {
		const el = inputRef.current;
		if (!el) return;
		el.style.height = 'auto';
		el.style.height = `${el.scrollHeight}px`;
	}, [draft]);

	const disabled = !enabled || sending || (mode === 'reply' && thinking);

	/** Send `content` (the box, or composed answers). The box clears only once the send succeeds. */
	const send = async (content = draft) => {
		const text = content.trim();
		if (!text || disabled) return;
		const ok = await (mode === 'reply' ? onSend(text) : onNewRound(text));
		if (ok) setDraft('');
	};

	const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
		if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
			e.preventDefault();
			send();
		}
	};
	const onSubmit = (e: FormEvent) => {
		e.preventDefault();
		send();
	};

	const placeholder = !enabled
		? 'Agent Mode is not available for this app'
		: mode === 'first'
			? 'e.g. a way for staff to book patient appointments and track whether they were attended'
			: mode === 'next'
				? 'Describe the next change…'
				: thinking
					? 'The agent is replying…'
					: openQuestions
						? 'Anything to add? (optional)'
						: 'Reply, or ask for changes…';
	const hint =
		mode === 'next'
			? 'Starts a new change — nothing is built until you approve it.'
			: mode === 'reply' && thinking
				? 'Waiting for the agent…'
				: 'Enter to send · Shift+Enter for a new line';

	return (
		<section className="chat" aria-label="Conversation">
			<div className="thread" ref={scrollRef}>
				<div className="flex flex-col gap-[18px]" ref={contentRef} aria-live="polite">
					{!rounds.length && (
						<Message message={{ role: 'assistant', content: INTRO, ts: '' }} you={you} />
					)}
					{rounds.map((round) => {
						const d = round.detail;
						const seen = seenSeq.current.get(round.summary.uuid);
						if (d && seen === undefined)
							seenSeq.current.set(round.summary.uuid, d.messages[d.messages.length - 1]?.seq ?? 0);
						const isActive = round.summary.uuid === active?.uuid;
						const latestRun = d?.runs[0] ?? round.summary.latest_run;
						return (
							<div key={round.summary.uuid} className="flex flex-col gap-[18px]">
								{(rounds.length > 1 || !isActive) && <RoundRule round={round} />}
								{d ? (
									d.messages.map((m) => (
										<Message
											key={m.seq}
											message={m}
											you={you}
											fresh={seen !== undefined && m.seq > seen}
										/>
									))
								) : (
									<div className="typing">
										<span className="spin" />
										Loading…
									</div>
								)}
								{isActive && d?.is_thinking && (
									<div className="msg fresh">
										<AgentMark />
										<div className="mb">
											<div className="typing">
												<span className="spin" />
												Thinking…
											</div>
										</div>
									</div>
								)}
								{isActive && d?.error_message && (
									<div className="flex items-start gap-2 rounded-lg border border-[#fecaca] bg-red-soft px-3 py-2 text-[12.5px] text-red-t">
										<Icon name="alert" size={14} className="mt-[2px]" />
										<span>{d.error_message}</span>
									</div>
								)}
								{latestRun && (
									<BuildMarker run={latestRun} onOpen={() => onOpenBuild(round.summary.uuid)} />
								)}
							</div>
						);
					})}
					{openQuestions && (
						<QuestionCards
							questions={openQuestions}
							disabled={disabled}
							extra={draft}
							onSend={(c) => send(c)}
						/>
					)}
					{agentCard && (
						<div className="msg fresh">
							<AgentMark />
							<div className="mb">{agentCard}</div>
						</div>
					)}
				</div>
			</div>
			<div className="composer">
				<form onSubmit={onSubmit}>
					<textarea
						ref={inputRef}
						rows={1}
						value={draft}
						onChange={(e) => setDraft(e.target.value)}
						onKeyDown={onKeyDown}
						placeholder={placeholder}
						disabled={!enabled || (mode === 'reply' && thinking)}
						aria-label="Message the agent"
						autoFocus={mode === 'first'}
					/>
					<div className="cb">
						<span>{hint}</span>
						<div className="r">
							<Button
								type="submit"
								variant="primary"
								size="xs"
								className="!w-[26px] !px-0"
								aria-label="Send"
								disabled={disabled || !draft.trim()}
								loading={sending}
							>
								{!sending && <Icon name="up" weight={2.2} />}
							</Button>
						</div>
					</div>
				</form>
			</div>
		</section>
	);
}
