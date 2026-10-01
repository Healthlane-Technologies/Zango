import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { documentUrl, type SpecIssue } from '@/api/agentMode';
import { Badge, Button, cx, Icon, Menu, SaveBar, Tabs, TemplateBadge, type Tone } from '@/ui';
import { ChecksList, type CheckRow } from './ChecksList';
import { EmbeddedBuilder } from './EmbeddedBuilder';
import { BuilderContext, type BuilderCtx } from './context';
import { changedPointers } from './diff';
import { humanPath } from './labels';
import { ancestors } from './pointer';
import type { BuilderProps } from './registry';
import type { Schema } from './schema';
import { ReviewPanel } from './ReviewPanel';
import { SectionDetails } from './SectionDetails';
import { SectionNav, type SectionState } from './SectionNav';
import { orderedSections, sectionCount, sectionOf, type BuilderSection } from './sections';
import { rangeOf } from './yamlDoc';
import { useSpecDraft } from './useSpecDraft';
import { YamlView } from './YamlView';
import './builder.css';

type Tab = 'builder' | 'details' | 'yaml' | 'checks' | 'review';
type Mode = 'default' | 'all' | 'none';

const FLASH_MS = 1600;
const NONE: string[] = [];

function withAncestors(pointers: string[]): Set<string> {
	const out = new Set<string>();
	for (const p of pointers) for (const a of [p, ...ancestors(p)]) out.add(a);
	return out;
}

/** Scroll to the element for `pointer`, or the nearest ancestor that is on screen, and flash it. */
function flash(root: HTMLElement | null, pointer: string) {
	if (!root) return;
	for (const p of [pointer, ...ancestors(pointer), '']) {
		const el = root.querySelector<HTMLElement>(`[id="f:${CSS.escape(p)}"]`);
		if (el) {
			el.scrollIntoView({ block: 'center', behavior: 'smooth' });
			el.classList.remove('bv-flash');
			void el.offsetWidth;
			el.classList.add('bv-flash');
			window.setTimeout(() => el.classList.remove('bv-flash'), FLASH_MS);
			return;
		}
	}
}

export function TemplateBuilderPanel({
	appId,
	requirement,
	builder,
	spec: serverSpec,
	editable = false,
	onController,
}: BuilderProps) {
	const root = builder.json_schema as Schema;
	const sections = useMemo<BuilderSection[]>(
		() => orderedSections(builder.ui_schema.sections),
		[builder],
	);
	const draft = useSpecDraft({ appId, reqId: requirement.uuid, server: serverSpec });
	// The template ships its own builder (e.g. Journey Studio): it replaces Details.
	const embedUrl = builder.builder_url || null;
	useEffect(() => onController?.(draft.controller), [onController, draft.controller]);
	// What's on screen: the agent's version while reviewing a conflict, else the draft/newest.
	const spec = draft.shown;
	const parsed = draft.parsed;
	const doc = parsed.value;
	const thinking = requirement.is_thinking;
	const locked = !editable || thinking || spec.status === 'approved' || draft.reviewing;
	// Unsaved edits have no "changed by agent"; a conflict under review shows the agent's.
	const changedProp =
		draft.reviewing && draft.incoming
			? draft.incoming.changed_paths
			: draft.dirty
				? NONE
				: (spec.changed_paths ?? NONE);

	// Changed pointers: what the server says the last turn touched, else a diff against what
	// this panel last showed (so a poll that brings no changed_paths still highlights).
	const previous = useRef<{ rev: number; value: unknown } | null>(null);
	const [diffed, setDiffed] = useState<string[]>([]);
	useEffect(() => {
		const prev = previous.current;
		if (prev && spec.draft_revision > prev.rev && !changedProp.length && !draft.dirty)
			setDiffed(changedPointers(prev.value, doc));
		else if (changedProp.length) setDiffed((d) => (d.length ? NONE : d));
		previous.current = { rev: spec.draft_revision, value: doc };
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [spec.draft_revision, doc, changedProp]);
	const changed = useMemo(() => {
		const list = changedProp.length ? changedProp : diffed;
		// In document order, so the chip walks top to bottom.
		return [...new Set(list)].sort(
			(a, b) => (rangeOf(parsed, a)?.line ?? 1e9) - (rangeOf(parsed, b)?.line ?? 1e9),
		);
	}, [changedProp, diffed, parsed]);

	const issues = useMemo<SpecIssue[]>(
		() => [
			...parsed.errors.map((e) => ({
				level: 'error' as const,
				path: '',
				message: `YAML: ${e.message}`,
				code: 'yaml',
			})),
			...draft.issues,
		],
		[parsed.errors, draft.issues],
	);
	const issuesAt = useMemo(() => {
		const m = new Map<string, SpecIssue[]>();
		for (const i of issues) m.set(i.path, [...(m.get(i.path) ?? []), i]);
		return m;
	}, [issues]);
	const issueWithin = useMemo(() => withAncestors(issues.map((i) => i.path)), [issues]);
	const changedWithin = useMemo(() => withAncestors(changed), [changed]);

	const sectionFor = useCallback(
		(pointer: string, hint?: string) =>
			sections.find((s) => s.id === hint) ?? sectionOf(sections, pointer),
		[sections],
	);

	const states: SectionState[] = useMemo(
		() =>
			sections.map((section) => ({
				section,
				count: sectionCount(section, doc),
				errors: issues.filter(
					(i) => i.level === 'error' && sectionFor(i.path, i.section)?.id === section.id,
				).length,
				warnings: issues.filter(
					(i) => i.level === 'warning' && sectionFor(i.path, i.section)?.id === section.id,
				).length,
				changed: changed.filter((p) => sectionFor(p)?.id === section.id).length,
			})),
		[sections, doc, issues, changed, sectionFor],
	);

	const [tab, setTab] = useState<Tab>(embedUrl ? 'builder' : 'details');
	const [active, setActive] = useState<string>(() => sections[0]?.id ?? '');
	const section = sections.find((s) => s.id === active) ?? sections[0];
	const [overrides, setOverrides] = useState<Map<string, boolean>>(() => new Map());
	const [mode, setMode] = useState<Record<string, Mode>>({});
	const [editingSections, setEditingSections] = useState<Set<string>>(() => new Set());
	const yamlBroken = parsed.errors.length > 0;
	const editingHere = !locked && !yamlBroken && !!section && editingSections.has(section.id);
	const [target, setTarget] = useState<{ pointer: string; nonce: number } | null>(null);
	const [yamlJump, setYamlJump] = useState<{ line: number; nonce: number } | null>(null);
	const body = useRef<HTMLDivElement>(null);

	const sectionMode = mode[section?.id ?? ''] ?? 'default';
	const ctx: BuilderCtx = useMemo(
		() => ({
			root,
			doc,
			issuesAt,
			issueWithin,
			changedWithin,
			changedExact: new Set(changed),
			isOpen: (p, fallback) =>
				overrides.get(p) ??
				(sectionMode === 'all' ? true : sectionMode === 'none' ? false : fallback),
			toggle: (p, fallback) =>
				setOverrides((m) => {
					const next = new Map(m);
					const cur =
						m.get(p) ?? (sectionMode === 'all' ? true : sectionMode === 'none' ? false : fallback);
					next.set(p, !cur);
					return next;
				}),
			editing: editingHere,
			edit: (change) => {
				if (editingHere) draft.edit(change);
			},
		}),
		[
			root,
			doc,
			issuesAt,
			issueWithin,
			changedWithin,
			changed,
			overrides,
			sectionMode,
			editingHere,
			draft,
		],
	);

	/** Show `pointer`: in the YAML tab move to its line, otherwise open its section and cards. */
	const jumpTo = useCallback(
		(pointer: string, opts: { sectionHint?: string; line?: number; inTab?: Tab } = {}) => {
			const where = opts.inTab ?? (tab === 'yaml' ? 'yaml' : 'details');
			// With the template's own builder there is no Details tab to jump into.
			if (where === 'yaml' || embedUrl) {
				setTab('yaml');
				setYamlJump({ line: opts.line ?? rangeOf(parsed, pointer)?.line ?? 1, nonce: Date.now() });
				return;
			}
			const s = sectionFor(pointer, opts.sectionHint);
			if (s) setActive(s.id);
			setOverrides((m) => {
				const next = new Map(m);
				for (const a of [pointer, ...ancestors(pointer)]) next.set(a, true);
				return next;
			});
			setTab('details');
			setTarget({ pointer, nonce: Date.now() });
		},
		[tab, parsed, sectionFor, embedUrl],
	);

	useEffect(() => {
		if (!target) return;
		const t = window.setTimeout(() => flash(body.current, target.pointer), 30);
		return () => window.clearTimeout(t);
	}, [target]);

	const [changedIdx, setChangedIdx] = useState(0);
	useEffect(() => setChangedIdx(0), [changed]);
	const nextChanged = () => {
		if (!changed.length) return;
		const p = changed[changedIdx % changed.length];
		setChangedIdx((i) => i + 1);
		jumpTo(p);
	};

	const rows: CheckRow[] = useMemo(() => {
		const order = new Map(sections.map((s, i) => [s.id, i]));
		return issues
			.map((issue) => ({
				issue,
				section: issue.code === 'yaml' ? undefined : sectionFor(issue.path, issue.section),
				where: issue.path ? humanPath(root, doc, issue.path) : '',
				line:
					issue.code === 'yaml'
						? parsed.errors.find((e) => `YAML: ${e.message}` === issue.message)?.line
						: rangeOf(parsed, issue.path)?.line,
			}))
			.sort(
				(a, b) => (order.get(a.section?.id ?? '') ?? -1) - (order.get(b.section?.id ?? '') ?? -1),
			);
	}, [issues, sections, sectionFor, root, doc, parsed]);

	const lineMarks = useMemo(() => {
		const linesOf = (ptrs: string[]) =>
			ptrs.flatMap((p) => {
				const r = rangeOf(parsed, p);
				if (!r) return [];
				return Array.from({ length: Math.min(r.endLine - r.line + 1, 40) }, (_, i) => r.line + i);
			});
		return {
			changed: linesOf(changed),
			errors: rows.filter((r) => r.issue.level === 'error' && r.line).map((r) => r.line!),
			warnings: rows.filter((r) => r.issue.level === 'warning' && r.line).map((r) => r.line!),
		};
	}, [changed, rows, parsed]);

	const errors = issues.filter((i) => i.level === 'error').length;
	const canFinalize =
		editable &&
		spec.is_draft &&
		spec.status !== 'approved' &&
		!thinking &&
		!draft.incoming &&
		!errors;
	const yamlDiagnostics = useMemo(
		() => [
			...parsed.errors
				.filter((e) => e.from !== undefined)
				.map((e) => ({
					from: e.from!,
					to: e.to ?? e.from!,
					severity: 'error' as const,
					message: e.message,
				})),
			...rows
				.filter((r) => r.issue.code !== 'yaml' && r.issue.path)
				.flatMap((r) => {
					const range = rangeOf(parsed, r.issue.path);
					return range
						? [
								{
									from: range.from,
									to: Math.max(range.from, range.to - 1),
									severity: r.issue.level === 'error' ? ('error' as const) : ('warning' as const),
									message: r.issue.message,
								},
							]
						: [];
				}),
		],
		[parsed, rows],
	);
	// One-pass drafting: the agent's open decisions and flags, and the documents it drew on.
	const decisions = serverSpec.open_decisions ?? [];
	const flags = serverSpec.flags ?? [];
	const documents = serverSpec.documents ?? [];
	const reviewCount = decisions.length + flags.length;
	const drafting = serverSpec.mode === 'draft' && thinking;
	const canReview = editable && !thinking && spec.status !== 'approved';
	const whereOf = useCallback(
		(p: string) => (p ? humanPath(root, doc, p) : 'The whole journey'),
		[root, doc],
	);
	// A finished draft with things to review opens on them, once.
	const reviewed = useRef(false);
	useEffect(() => {
		if (!reviewed.current && serverSpec.mode === 'draft' && !thinking && reviewCount > 0) {
			reviewed.current = true;
			setTab('review');
		}
	}, [serverSpec.mode, thinking, reviewCount]);

	const [tone, label]: [Tone, string] = spec.is_draft
		? ['amber', 'Draft']
		: spec.status === 'approved'
			? ['green', 'Approved']
			: spec.status === 'ready'
				? ['accent', 'Ready for review']
				: ['amber', 'Draft'];

	return (
		<BuilderContext.Provider value={ctx}>
			<div className={cx('bld', draft.dirty && 'dirty', embedUrl && 'fill')}>
				<div className="bld-h">
					{spec.template && <TemplateBadge template={spec.template} />}
					<Badge tone={tone} dot>
						{label}
					</Badge>
					<span className="mono text-[11.5px] text-t4">rev {spec.draft_revision}</span>
					{thinking && (
						<span className="bld-thinking">
							<span className="spin" />
							Agent is editing…
						</span>
					)}
					<span className="ml-auto flex items-center gap-1.5">
						{documents.length > 0 && (
							<Menu
								items={documents.map((d) => ({
									label: d.name,
									icon: 'file' as const,
									onSelect: () =>
										window.open(documentUrl(appId, requirement.uuid, d.id), '_blank', 'noopener'),
								}))}
								trigger={
									<Button size="xs" icon="clip">
										Documents ({documents.length})
									</Button>
								}
							/>
						)}
						{changed.length > 0 && (
							<Button size="xs" variant="secondary" className="bld-chg" onClick={nextChanged}>
								<i className="bv-dot chg" />
								Changed by agent ({changed.length})
								<Icon name="up" size={12} className="rotate-180" />
							</Button>
						)}
						{canFinalize && (
							<Button
								size="xs"
								variant="primary"
								icon="check"
								loading={draft.busy === 'finalize'}
								onClick={() => draft.finalize()}
								title="Check the spec strictly and hand it over for approval"
							>
								Mark as ready
							</Button>
						)}
					</span>
				</div>
				{drafting && (
					<div className="bld-drafting" role="status">
						<span className="spin" />
						<span className="min-w-0">
							<b>
								Drafting
								{documents.length
									? ` from ${documents.length} document${documents.length > 1 ? 's' : ''}`
									: ' from your brief'}
								…
							</b>{' '}
							{states.filter((st) => st.changed > 0).length} of {states.length} sections written
						</span>
						<ul className="bld-ticks" aria-label="Sections">
							{states.map((st) => (
								<li
									key={st.section.id}
									className={cx(st.changed > 0 && 'done')}
									title={st.section.title}
								>
									{st.changed > 0 ? <Icon name="check" size={11} weight={2.6} /> : <i />}
									{st.section.title}
								</li>
							))}
						</ul>
					</div>
				)}
				{draft.incoming && (
					<div className="bld-conflict" role="alert">
						<Icon name="alert" className="mt-[2px] shrink-0" />
						<div className="min-w-0 flex-1">
							<b>
								{draft.reviewing
									? 'You’re looking at the agent’s version.'
									: 'The spec changed while you were editing.'}
							</b>
							<span>
								{draft.reviewing
									? ' Your edits are kept aside until you choose.'
									: ` Revision ${draft.incoming.draft_revision} is newer than the one you started from (${draft.base.draft_revision}).`}
							</span>
						</div>
						<div className="flex shrink-0 gap-1.5">
							<Button size="xs" onClick={draft.toggleReview}>
								{draft.reviewing ? 'Back to my edits' : 'Review agent changes'}
							</Button>
							<Button
								size="xs"
								variant="primary"
								loading={draft.busy === 'save'}
								disabled={thinking}
								onClick={() => draft.keepMine()}
							>
								Keep mine
							</Button>
							<Button size="xs" variant="danger" onClick={draft.discard}>
								Discard mine
							</Button>
						</div>
					</div>
				)}
				<Tabs<Tab>
					className="bld-tabs"
					value={tab}
					onChange={setTab}
					items={[
						embedUrl
							? { value: 'builder', label: 'Builder' }
							: { value: 'details', label: 'Details' },
						{ value: 'yaml', label: 'YAML' },
						{
							value: 'checks',
							label: errors ? `Checks · ${errors} to fix` : 'Checks',
							count: issues.length || undefined,
						},
						{ value: 'review', label: 'Review', count: reviewCount || undefined },
					]}
				/>
				<div ref={body} className="bld-b">
					{embedUrl && (
						<EmbeddedBuilder
							url={embedUrl}
							text={draft.text}
							readOnly={locked || !!draft.incoming}
							onChange={draft.type}
							hidden={tab !== 'builder'}
						/>
					)}
					{tab === 'details' && yamlBroken && !draft.reviewing && (
						<div className="bld-note err" role="status">
							<Icon name="alert" size={13} />
							The YAML has an error
							{parsed.errors[0]?.line ? ` on line ${parsed.errors[0].line}` : ''}. Details are
							read-only until it’s fixed in the
							<button type="button" className="link" onClick={() => setTab('yaml')}>
								YAML tab
							</button>
							.
						</div>
					)}
					{tab === 'details' && !embedUrl && section && (
						<div className="bld-split">
							<SectionNav sections={states} active={section.id} onSelect={setActive} />
							<SectionDetails
								key={section.id}
								section={section}
								canEdit={!locked && !yamlBroken}
								editing={editingHere}
								onToggleEdit={() =>
									setEditingSections((set) => {
										const next = new Set(set);
										if (next.has(section.id)) next.delete(section.id);
										else next.add(section.id);
										return next;
									})
								}
								onExpandAll={() => {
									setOverrides(new Map());
									setMode((m) => ({ ...m, [section.id]: 'all' }));
								}}
								onCollapseAll={() => {
									setOverrides(new Map());
									setMode((m) => ({ ...m, [section.id]: 'none' }));
								}}
							/>
						</div>
					)}
					{tab === 'yaml' && (
						<YamlView
							text={draft.text}
							marks={lineMarks}
							jump={yamlJump}
							editable={!locked}
							onChange={draft.type}
							diagnostics={yamlDiagnostics}
						/>
					)}
					{tab === 'review' && (
						<ReviewPanel
							appId={appId}
							reqId={requirement.uuid}
							decisions={decisions}
							flags={flags}
							documents={documents}
							sections={sections}
							sectionFor={sectionFor}
							whereOf={whereOf}
							canAct={canReview}
							thinking={thinking}
							flush={() => draft.controller.flush()}
							onShowInYaml={(p) => jumpTo(p, { inTab: 'yaml' })}
						/>
					)}
					{tab === 'checks' && (
						<ChecksList
							rows={rows}
							onJump={(r) =>
								r.issue.code === 'yaml'
									? jumpTo('', { inTab: 'yaml', line: r.line })
									: jumpTo(r.issue.path, { sectionHint: r.issue.section, inTab: 'details' })
							}
						/>
					)}
				</div>
				{draft.dirty && !draft.reviewing && (
					<div className="bld-save">
						<SaveBar
							dirty
							saving={draft.busy === 'save'}
							onSave={() => {
								if (!yamlBroken && !thinking) draft.save();
							}}
							onDiscard={draft.discard}
							note={
								thinking
									? 'The agent is working; save once it’s done.'
									: yamlBroken
										? 'Fix the YAML errors to save.'
										: 'The agent sees your changes once they’re saved.'
							}
						/>
					</div>
				)}
			</div>
		</BuilderContext.Provider>
	);
}
