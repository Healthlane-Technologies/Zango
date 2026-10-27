import {
	useEffect,
	useMemo,
	useRef,
	useState,
	type ClipboardEvent,
	type DragEvent,
	type FormEvent,
	type KeyboardEvent,
	type ReactNode,
} from 'react';
import {
	isRunActive,
	type AnalystQuestion,
	type PreviewFocus,
	type Requirement,
	type RequirementMessage,
	type RunRef,
} from '@/api/agentMode';
import { useMe } from '@/api/me';
import type { UploadedDocument } from '@/api/scaffolds';
import { ACCEPTED, addFiles, extOf, formatBytes } from '@/pages/new/intake';
import { Avatar, Button, Icon, cx } from '@/ui';
import { CARD_LABEL } from './BuildCard';
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

/** Files attached to a sent message: image thumbnails, other files as chips; both download. */
function Attachments({ files, url }: { files: UploadedDocument[]; url: (id: string | number) => string }) {
	return (
		<div className="att-sent">
			{files.map((f) =>
				f.content_type.startsWith('image/') ? (
					<a key={f.id} href={url(f.id)} className="att-img" title={f.name}>
						<img src={`${url(f.id)}?inline=1`} alt={f.name} loading="lazy" />
					</a>
				) : (
					<a key={f.id} href={url(f.id)} className="att-chip" title={`Download ${f.name}`}>
						<span className="docext">{extOf(f.name).toUpperCase()}</span>
						<span className="min-w-0 truncate">{f.name}</span>
						<small>{formatBytes(f.size)}</small>
					</a>
				),
			)}
		</div>
	);
}

function Message({
	message,
	fresh,
	you,
	docUrl,
}: {
	message: Pick<RequirementMessage, 'role' | 'content' | 'ts' | 'preview_focus' | 'attachments'>;
	fresh?: boolean;
	you: string;
	docUrl?: (id: string | number) => string;
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
				{user && docUrl && !!message.attachments?.length && (
					<Attachments files={message.attachments} url={docUrl} />
				)}
				{user && message.preview_focus && 'pointed' in message.preview_focus && message.preview_focus.pointed && (
					<div className="ptr-sent" title={message.preview_focus.pointed.path}>
						<Icon name="eye" size={11} />
						Pointed at {message.preview_focus.pointed.label || 'part of the preview'}
						{message.preview_focus.title && ` · ${message.preview_focus.title}`}
					</div>
				)}
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
	const bad = !run.user_status && ['failed', 'timeout', 'aborted'].includes(run.status);
	return (
		<div className={cx('upd', bad && 'bad')}>
			{run.status === 'waiting' ? (
				<Icon name="alert" size={13} weight={2.4} style={{ color: 'var(--amber)' }} />
			) : active ? (
				<span className="spin text-amber" />
			) : (
				<Icon name={bad ? 'alert' : 'check'} size={13} weight={2.6} />
			)}
			<span>
				<b>{run.user_status ? CARD_LABEL[run.user_status.state] : runLabel(run.status)}</b>
				{run.queued_at && ` · ${stamp(run.queued_at)}`}
			</span>
			<button type="button" onClick={onOpen}>
				{run.status === 'waiting' ? "See what's needed" : 'View build'}
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
	/** Resolve true when the message was accepted. `files` are attached to it. */
	onSend: (content: string, files: File[]) => Promise<boolean>;
	onNewRound: (prompt: string, files: File[]) => Promise<boolean>;
	/** Where a round's attached file can be fetched. */
	documentUrl?: (reqUuid: string, id: string | number) => string;
	onOpenBuild: (roundUuid: string) => void;
	/** Incremented to focus the composer (the header's "New change"). */
	focusSignal: number;
	/** A card from the agent after the newest message (e.g. its open decisions). */
	agentCard?: ReactNode;
	/** The composer's prompt once the agent has replied (e.g. "Ask for changes to the preview…"). */
	idlePlaceholder?: string;
	/** What the user pointed at in the preview; it goes with the next reply or new change. */
	pointer?: PreviewFocus | null;
	onClearPointer?: () => void;
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
	idlePlaceholder,
	pointer,
	onClearPointer,
	documentUrl,
}: ThreadProps) {
	const { data: me } = useMe();
	const you = me?.name || me?.email || 'You';
	const [draft, setDraft] = useState('');
	// Files to attach to the next message: chosen, dropped on the composer or pasted.
	const [files, setFiles] = useState<File[]>([]);
	const [fileErrors, setFileErrors] = useState<string[]>([]);
	const [dropping, setDropping] = useState(false);
	const fileInput = useRef<HTMLInputElement>(null);
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
	const pointed = mode !== 'first' ? pointer?.pointed : undefined;
	// Pointing is the start of a message: put the cursor in the box.
	useEffect(() => {
		if (pointer?.pointed) inputRef.current?.focus();
	}, [pointer]);

	const attach = (incoming: File[]) => {
		if (!incoming.length) return;
		const result = addFiles(files, incoming);
		setFileErrors(result.errors);
		setFiles(result.files);
	};
	const onDrop = (e: DragEvent) => {
		e.preventDefault();
		setDropping(false);
		if (!disabled) attach(Array.from(e.dataTransfer.files));
	};
	// A pasted screenshot arrives as an unnamed image: give it a name the agent can cite.
	const onPaste = (e: ClipboardEvent<HTMLTextAreaElement>) => {
		const pasted = Array.from(e.clipboardData.files);
		if (!pasted.length || disabled) return;
		e.preventDefault();
		const stamp = new Date().toISOString().slice(0, 19).replace(/[-:T]/g, '');
		attach(
			pasted.map((f, i) =>
				!f.name || f.name === 'image.png'
					? new File([f], `pasted-${stamp}${i ? `-${i}` : ''}.${f.type.split('/')[1] || 'png'}`, { type: f.type })
					: f,
			),
		);
	};

	/** Send `content` (the box, or composed answers) with the attached files. Both clear only once
	 * the send succeeds. */
	const send = async (content = draft) => {
		const text = content.trim();
		if ((!text && !files.length) || disabled) return;
		const ok = await (mode === 'reply' ? onSend(text, files) : onNewRound(text, files));
		if (ok) {
			setDraft('');
			setFiles([]);
			setFileErrors([]);
		}
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
				? pointed
					? 'What should change about it?'
					: 'Describe the next change…'
				: thinking
					? 'The agent is replying…'
					: pointed
						? 'What should change about it?'
						: openQuestions
							? 'Anything to add? (optional)'
							: (idlePlaceholder ?? 'Reply, or ask for changes…');
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
											docUrl={
												documentUrl ? (id) => documentUrl(round.summary.uuid, id) : undefined
											}
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
			<div
				className={cx('composer', dropping && 'dropping')}
				onDragOver={(e) => {
					if (!e.dataTransfer.types.includes('Files')) return;
					e.preventDefault();
					if (!disabled) setDropping(true);
				}}
				onDragLeave={(e) => {
					if (!e.currentTarget.contains(e.relatedTarget as Node | null)) setDropping(false);
				}}
				onDrop={onDrop}
			>
				<form onSubmit={onSubmit}>
					{pointed && (
						<div className="ptr" role="status">
							<Icon name="eye" size={12} />
							<span className="min-w-0 truncate">
								Pointing at <b>{pointed.label || 'this'}</b>
								{pointer?.title && <> · {pointer.title}</>}
								{pointer?.role && <> · as {pointer.role}</>}
							</span>
							<button type="button" onClick={onClearPointer} aria-label="Stop pointing" title="Stop pointing">
								<Icon name="x" size={12} />
							</button>
						</div>
					)}
					{(files.length > 0 || fileErrors.length > 0) && (
						<div className="att-tray">
							{files.map((f) => (
								<span key={`${f.name}-${f.size}`} className="att-chip">
									<span className="docext">{extOf(f.name).toUpperCase()}</span>
									<span className="min-w-0 truncate">{f.name}</span>
									<small>{formatBytes(f.size)}</small>
									<button
										type="button"
										aria-label={`Remove ${f.name}`}
										onClick={() => setFiles(files.filter((x) => x !== f))}
									>
										<Icon name="x" size={11} />
									</button>
								</span>
							))}
							{fileErrors.map((err) => (
								<span key={err} className="att-err" role="alert">
									{err}
								</span>
							))}
						</div>
					)}
					<textarea
						ref={inputRef}
						rows={1}
						value={draft}
						onChange={(e) => setDraft(e.target.value)}
						onKeyDown={onKeyDown}
						onPaste={onPaste}
						placeholder={placeholder}
						disabled={!enabled || (mode === 'reply' && thinking)}
						aria-label="Message the agent"
						autoFocus={mode === 'first'}
					/>
					<div className="cb">
						<span>{hint}</span>
						<div className="r">
							<button
								type="button"
								className="ib att-add"
								aria-label="Attach files"
								title={`Attach files or screenshots (${ACCEPTED.join(', ')}); you can also drop or paste them`}
								disabled={disabled}
								onClick={() => fileInput.current?.click()}
							>
								<Icon name="clip" size={14} />
							</button>
							<input
								ref={fileInput}
								type="file"
								multiple
								hidden
								accept={ACCEPTED.map((a) => `.${a}`).join(',')}
								onChange={(e) => {
									attach(Array.from(e.target.files ?? []));
									e.target.value = '';
								}}
							/>
							<Button
								type="submit"
								variant="primary"
								size="xs"
								className="!w-[26px] !px-0"
								aria-label="Send"
								disabled={disabled || (!draft.trim() && !files.length)}
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
