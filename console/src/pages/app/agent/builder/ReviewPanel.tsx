import { useEffect, useMemo, useState } from 'react';
import {
	documentUrl,
	useAnswerDecisions,
	useConfirmFlags,
	type DecisionAnswer,
	type FlagKind,
	type OpenDecision,
	type SpecFlag,
} from '@/api/agentMode';
import type { UploadedDocument } from '@/api/scaffolds';
import { Badge, Button, cx, Icon, type Tone } from '@/ui';
import type { BuilderSection } from './sections';

// The review side of one-pass drafting: the agent drafts the whole journey, then lists
// (a) the few real gaps as decisions, answered together in one go, and (b) every value it
// did not take straight from the user's material, as flags to confirm or fix.

const KIND: Record<FlagKind, [Tone, string]> = {
	inferred: ['amber', 'Inferred'],
	reference: ['violet', 'From reference'],
	default: ['gray', 'Template default'],
	missing: ['red', 'Missing'],
};
const KIND_ORDER: FlagKind[] = ['missing', 'inferred', 'reference', 'default'];
const OTHER = '__other__';

interface ReviewPanelProps {
	appId: string;
	reqId: string;
	decisions: OpenDecision[];
	flags: SpecFlag[];
	documents: UploadedDocument[];
	sections: BuilderSection[];
	sectionFor: (pointer: string, hint?: string) => BuilderSection | undefined;
	/** Human-readable location for a pointer. */
	whereOf: (pointer: string) => string;
	/** Answers and confirmations are possible (active round, open, agent idle). */
	canAct: boolean;
	thinking: boolean;
	/** Save unsaved edits first, so the agent applies answers to what is on screen. */
	flush: () => Promise<boolean>;
	onShowInYaml: (pointer: string) => void;
}

function Decisions({
	appId,
	reqId,
	decisions,
	canAct,
	thinking,
	flush,
	whereOf,
	onShowInYaml,
}: Pick<
	ReviewPanelProps,
	'appId' | 'reqId' | 'decisions' | 'canAct' | 'thinking' | 'flush' | 'whereOf' | 'onShowInYaml'
>) {
	const answer = useAnswerDecisions(appId, reqId);
	const seed = () =>
		Object.fromEntries(decisions.map((d) => [d.id, d.recommended ?? d.options[0] ?? OTHER]));
	const [picked, setPicked] = useState<Record<string, string>>(seed);
	const [other, setOther] = useState<Record<string, string>>({});
	// A new set of decisions (the agent revised them) starts from its recommendations again.
	const key = decisions.map((d) => d.id).join('|');
	// eslint-disable-next-line react-hooks/exhaustive-deps
	useEffect(() => setPicked(seed()), [key]);

	const answers: DecisionAnswer[] = decisions.map((d) => ({
		id: d.id,
		path: d.path,
		answer: picked[d.id] === OTHER ? (other[d.id] ?? '').trim() : (picked[d.id] ?? ''),
	}));
	const complete = answers.every((a) => a.answer);
	const send = async () => {
		if (!complete || !(await flush())) return;
		const content =
			'Decisions:\n' + decisions.map((d, i) => `- ${d.question} → ${answers[i].answer}`).join('\n');
		answer.mutate({ content, answers });
	};

	return (
		<section className="rv-sec">
			<div className="rv-h">
				<h4>Open decisions</h4>
				<span className="ct">{decisions.length}</span>
				<span className="ml-auto text-[12px] text-t3">
					The agent's recommendation is picked; change what you like and send them together.
				</span>
			</div>
			<ol className="rv-decisions">
				{decisions.map((d, i) => (
					<li key={d.id} className="rv-dec">
						<div className="rv-q">
							<span className="rv-n">{i + 1}</span>
							<div className="min-w-0 flex-1">
								<b>{d.question}</b>
								{d.why && <small>{d.why}</small>}
							</div>
							{d.path && (
								<button
									type="button"
									className="rv-where"
									onClick={() => onShowInYaml(d.path)}
									title="Show in YAML"
								>
									{whereOf(d.path)}
								</button>
							)}
						</div>
						<div className="rv-opts" role="radiogroup" aria-label={d.question}>
							{[...d.options, OTHER].map((opt) => {
								const isOther = opt === OTHER;
								const on = picked[d.id] === opt;
								return (
									<label key={opt} className={cx('rv-opt', on && 'on')}>
										<input
											type="radio"
											name={`dec-${d.id}`}
											checked={on}
											disabled={!canAct || answer.isPending}
											onChange={() => setPicked((p) => ({ ...p, [d.id]: opt }))}
										/>
										{isOther ? (
											<input
												className="input h-7"
												placeholder="Something else…"
												value={other[d.id] ?? ''}
												disabled={!canAct || answer.isPending}
												onFocus={() => setPicked((p) => ({ ...p, [d.id]: OTHER }))}
												onChange={(e) => setOther((o) => ({ ...o, [d.id]: e.target.value }))}
											/>
										) : (
											<span>
												{opt}
												{opt === d.recommended && <em className="rv-rec">Recommended</em>}
											</span>
										)}
									</label>
								);
							})}
						</div>
					</li>
				))}
			</ol>
			<div className="rv-f">
				<span className="text-[12px] text-t3">
					{thinking ? 'The agent is working; answer once it’s done.' : 'Sent as one message.'}
				</span>
				<Button
					variant="primary"
					size="sm"
					icon="up"
					disabled={!canAct || !complete}
					loading={answer.isPending}
					onClick={send}
				>
					Send answers
				</Button>
			</div>
		</section>
	);
}

function Flags({
	appId,
	reqId,
	flags,
	documents,
	sections,
	sectionFor,
	whereOf,
	canAct,
	onShowInYaml,
}: Pick<
	ReviewPanelProps,
	| 'appId'
	| 'reqId'
	| 'flags'
	| 'documents'
	| 'sections'
	| 'sectionFor'
	| 'whereOf'
	| 'canAct'
	| 'onShowInYaml'
>) {
	const confirm = useConfirmFlags(appId, reqId);
	const groups = useMemo(() => {
		const order = new Map(sections.map((s, i) => [s.id, i]));
		const bySection = new Map<string, { section?: BuilderSection; flags: SpecFlag[] }>();
		for (const f of flags) {
			const section = sectionFor(f.path, f.section);
			const key = section?.id ?? '';
			const g = bySection.get(key) ?? { section, flags: [] };
			g.flags.push(f);
			bySection.set(key, g);
		}
		return [...bySection.values()]
			.map((g) => ({
				...g,
				flags: [...g.flags].sort((a, b) => KIND_ORDER.indexOf(a.kind) - KIND_ORDER.indexOf(b.kind)),
			}))
			.sort(
				(a, b) => (order.get(a.section?.id ?? '') ?? 999) - (order.get(b.section?.id ?? '') ?? 999),
			);
	}, [flags, sections, sectionFor]);
	const docByName = useMemo(() => new Map(documents.map((d) => [d.name, d])), [documents]);

	return (
		<section className="rv-sec">
			<div className="rv-h">
				<h4>Flagged by the agent</h4>
				<span className="ct">{flags.length}</span>
				<span className="ml-auto text-[12px] text-t3">
					Values the agent didn’t take straight from your material. Confirm them, or fix them in the
					builder — editing a value clears its flag.
				</span>
			</div>
			{groups.map((g) => (
				<div key={g.section?.id ?? 'other'} className="rv-group">
					<div className="rv-gh">
						<b>{g.section?.title ?? 'Other'}</b>
						<span className="ct">{g.flags.length}</span>
						<Button
							size="xs"
							className="ml-auto"
							disabled={!canAct || confirm.isPending}
							onClick={() => confirm.mutate(g.flags.map((f) => f.path))}
						>
							Confirm all in section
						</Button>
					</div>
					<ul className="rv-flags">
						{g.flags.map((f) => {
							const [tone, label] = KIND[f.kind] ?? ['gray', f.kind];
							const doc = f.source?.document ? docByName.get(f.source.document) : undefined;
							return (
								<li key={`${f.path}-${f.kind}`} className="rv-flag">
									<div className="rv-fl">
										<Badge tone={tone}>{label}</Badge>
										<button
											type="button"
											className="rv-where"
											onClick={() => onShowInYaml(f.path)}
											title="Show in YAML"
										>
											{whereOf(f.path)}
										</button>
									</div>
									<p>{f.note}</p>
									{f.source && (f.source.quote || f.source.document) && (
										<blockquote className="rv-src">
											{f.source.quote && <span>“{f.source.quote}”</span>}
											{f.source.document && (
												<cite>
													{doc ? (
														<a
															href={documentUrl(appId, reqId, doc.id)}
															target="_blank"
															rel="noreferrer"
														>
															{f.source.document}
														</a>
													) : (
														f.source.document
													)}
													{f.source.locator && ` · ${f.source.locator}`}
												</cite>
											)}
										</blockquote>
									)}
									<div className="rv-acts">
										<Button
											size="xs"
											icon="check"
											disabled={!canAct || confirm.isPending}
											onClick={() => confirm.mutate([f.path])}
										>
											Confirm
										</Button>
										<Button size="xs" variant="ghost" onClick={() => onShowInYaml(f.path)}>
											Show in YAML
										</Button>
									</div>
								</li>
							);
						})}
					</ul>
				</div>
			))}
		</section>
	);
}

export function ReviewPanel(props: ReviewPanelProps) {
	const { decisions, flags } = props;
	if (!decisions.length && !flags.length) {
		return (
			<div className="card">
				<div className="empty">
					<b>Nothing to review</b>
					{props.thinking
						? 'The agent is still drafting. Anything it has to assume shows up here.'
						: 'No open decisions, and nothing the agent had to assume.'}
				</div>
			</div>
		);
	}
	return (
		<div className="rv">
			{decisions.length > 0 && <Decisions {...props} />}
			{flags.length > 0 && <Flags {...props} />}
			{decisions.length === 0 && (
				<p className="rv-done">
					<Icon name="check" size={13} /> No open decisions.
				</p>
			)}
		</div>
	);
}
