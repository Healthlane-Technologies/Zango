import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { documentUrl, type SpecIssue } from '@/api/agentMode';
import {
	Badge,
	Button,
	cx,
	Drawer,
	Icon,
	Menu,
	SaveBar,
	Skeleton,
	Tabs,
	TemplateBadge,
	type MenuItem,
	type Tone,
} from '@/ui';
import { ChecksList, type CheckRow } from './ChecksList';
import { EmbeddedBuilder } from './EmbeddedBuilder';
import { GeneratingPreview, UpdatingPreview } from './GeneratingPreview';
import { isGeneratingPreview } from './generating';
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

// The swimlane renderer only loads when the Workflows tab is opened.
const WorkflowsPanel = lazy(() => import('./WorkflowsPanel'));

type Tab = 'builder' | 'preview' | 'details' | 'workflows' | 'yaml' | 'checks' | 'review';
/** What the preview pane's ⋯ menu opens over the preview. */
type Sheet = 'spec' | 'workflows' | 'checks' | 'flags' | 'documents';
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
	jump,
	commit,
	sheet: sheetSignal,
}: BuilderProps) {
	const root = builder.json_schema as Schema;
	const sections = useMemo<BuilderSection[]>(
		() => orderedSections(builder.ui_schema.sections),
		[builder],
	);
	const draft = useSpecDraft({ appId, reqId: requirement.uuid, server: serverSpec });
	// The page that renders the app from the spec (Journey Studio, App Studio…). With one, the
	// pane is just the live preview; the spec, workflows and checks open from its ⋯ menu.
	const previewUrl = builder.preview_url ?? builder.builder_url ?? null;
	const previewMode = !!previewUrl;
	// Without a preview page, a template's own builder replaces Details (older servers).
	const embedUrl = previewMode ? null : builder.builder_url || null;
	const [sheet, setSheet] = useState<Sheet | null>(null);
	const [inBuilder, setInBuilder] = useState(false);
	// What the page says it can do; older adapters don't say, and only builders had an editor.
	const [caps, setCaps] = useState<string[] | undefined>();
	const canEditInBuilder = caps
		? caps.includes('edit')
		: builder.preview_source !== 'generic' &&
			!!builder.builder_url &&
			previewUrl === builder.builder_url;
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
			if (previewMode) {
				setSheet('spec');
				setYamlJump({ line: opts.line ?? rangeOf(parsed, pointer)?.line ?? 1, nonce: Date.now() });
				return;
			}
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
		[tab, parsed, sectionFor, embedUrl, previewMode],
	);

	// A sheet to open, sent from outside the pane (Checks after a refused commit).
	useEffect(() => {
		if (sheetSignal && previewMode) setSheet(sheetSignal.sheet);
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [sheetSignal]);

	// A pointer to show, sent from outside the pane (a decision in the chat).
	useEffect(() => {
		if (jump) jumpTo(jump.pointer);
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [jump]);

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
		if (previewMode) return; // decisions are in the chat; flags behind the pill
		if (!reviewed.current && serverSpec.mode === 'draft' && !thinking && reviewCount > 0) {
			reviewed.current = true;
			setTab('review');
		}
	}, [serverSpec.mode, thinking, reviewCount, previewMode]);

	const [tone, label]: [Tone, string] = spec.is_draft
		? ['amber', 'Draft']
		: spec.status === 'approved'
			? ['green', 'Approved']
			: spec.status === 'ready'
				? ['accent', 'Ready for review']
				: ['amber', 'Draft'];

	const draftingStrip = drafting && (
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
				{states.length > 0 &&
					`${states.filter((st) => st.changed > 0).length} of ${states.length} sections written`}
			</span>
			<ul className="bld-ticks" aria-label="Sections">
				{states.map((st) => (
					<li key={st.section.id} className={cx(st.changed > 0 && 'done')} title={st.section.title}>
						{st.changed > 0 ? <Icon name="check" size={11} weight={2.6} /> : <i />}
						{st.section.title}
					</li>
				))}
			</ul>
		</div>
	);
	const conflictBar = draft.incoming && (
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
	);
	const saveBar = draft.dirty && !draft.reviewing && (
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
	);

	if (previewMode) {
		const warnings = issues.length - errors;
		// The first version of the app is still being written: the preview has nothing to show.
		const generating = isGeneratingPreview({
			thinking,
			text: spec.text,
			starter: builder.starter_yaml,
			draftRevision: spec.draft_revision,
			yamlBroken,
		});
		const writtenSections = [
			...new Set(
				(spec.changed_paths ?? []).map((p) => sectionFor(p)?.id).filter((id): id is string => !!id),
			),
		];
		const fileName = `${builder.spec_root || 'spec'}.yaml`;
		const menu: Array<MenuItem | null> = [
			{ label: 'Spec (YAML)', icon: 'file', onSelect: () => setSheet('spec') },
			{ label: 'Workflows', icon: 'flow', onSelect: () => setSheet('workflows') },
			{
				label: errors
					? `Checks · ${errors} to fix`
					: `Checks${issues.length ? ` · ${issues.length}` : ''}`,
				icon: 'alert',
				onSelect: () => setSheet('checks'),
			},
			{
				label: `Flagged by the agent${flags.length ? ` · ${flags.length}` : ''}`,
				icon: 'flag',
				onSelect: () => setSheet('flags'),
			},
			{
				label: `Documents${documents.length ? ` · ${documents.length}` : ''}`,
				icon: 'clip',
				onSelect: () => setSheet('documents'),
			},
			...(canEditInBuilder
				? [
						null,
						inBuilder
							? {
									label: 'Back to preview',
									icon: 'eye' as const,
									onSelect: () => setInBuilder(false),
								}
							: {
									label: 'Edit in builder',
									icon: 'pen' as const,
									onSelect: () => setInBuilder(true),
									disabled: locked,
								},
					]
				: []),
		];
		const sheetTitle: Record<Sheet, string> = {
			spec: 'Spec',
			workflows: 'Workflows',
			checks: 'Checks',
			flags: 'Flagged by the agent',
			documents: 'Documents',
		};
		return (
			<BuilderContext.Provider value={ctx}>
				<div className={cx('bld fill pv', draft.dirty && 'dirty')}>
					{/* The template is named in the page header already. */}
					<div className="bld-h pv-h">
						{generating ? (
							<Badge tone="accent" dot>
								Generating
							</Badge>
						) : (
							<>
								<Badge tone={tone} dot>
									{label}
								</Badge>
								<span className="mono text-[11.5px] text-t4" title="Spec revision">
									rev {spec.draft_revision}
								</span>
							</>
						)}
						<span className="ml-auto flex items-center gap-1.5">
							{/* Nothing to check or commit until there is an app to look at. */}
							{!generating && (
								<>
									<button
										type="button"
										className={cx('pv-pill', errors ? 'err' : warnings ? 'warn' : 'ok')}
										onClick={() => setSheet('checks')}
										title="Checks"
									>
										<Icon name={errors || warnings ? 'alert' : 'check'} size={12} weight={2.4} />
										{errors
											? `${errors} to fix`
											: warnings
												? `${warnings} warning${warnings > 1 ? 's' : ''}`
												: 'Valid'}
									</button>
									{flags.length > 0 && (
										<button
											type="button"
											className="pv-pill flag"
											onClick={() => setSheet('flags')}
											title="Values the agent assumed"
										>
											<Icon name="flag" size={12} />
											{flags.length} flagged
										</button>
									)}
									{changed.length > 0 && !thinking && (
										<button
											type="button"
											className="pv-pill chg"
											onClick={nextChanged}
											title="Show what the last update changed, in the spec"
										>
											<i className="bv-dot chg" />
											{changed.length} changed
										</button>
									)}
									{commit && spec.status !== 'approved' && (
										<Button
											size="xs"
											variant="primary"
											icon="rocket"
											loading={commit.loading}
											disabled={!!commit.blocked}
											onClick={commit.onClick}
											title={commit.blocked ?? 'Build the app exactly as previewed'}
										>
											Commit for build
										</Button>
									)}
									{!commit && canFinalize && (
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
								</>
							)}
							<Menu
								items={menu}
								trigger={
									<button
										type="button"
										className="ib"
										aria-label="Spec and details"
										title="Spec and details"
									>
										<Icon name="dots" />
									</button>
								}
							/>
						</span>
					</div>
					{conflictBar}
					<div className="bld-b">
						<GeneratingPreview
							shown={generating}
							documents={documents.length}
							sections={sections}
							changedSections={writtenSections}
						/>
						{thinking && !generating && <UpdatingPreview />}
						{inBuilder && (
							<div className="pv-editing" role="status">
								<Icon name="pen" size={13} />
								<span className="min-w-0 flex-1">
									<b>Editing in the builder.</b> Your changes are a draft until you save them.
								</span>
								<Button size="xs" icon="eye" onClick={() => setInBuilder(false)}>
									Back to preview
								</Button>
							</div>
						)}
						<EmbeddedBuilder
							url={previewUrl!}
							text={draft.text}
							readOnly={locked || !!draft.incoming}
							onChange={draft.type}
							preview={!inBuilder}
							onReady={setCaps}
						/>
					</div>
					{!sheet && saveBar}
				</div>
				<Drawer
					open={!!sheet}
					onOpenChange={(o) => !o && setSheet(null)}
					wide={sheet === 'spec' || sheet === 'workflows'}
					title={sheet ? sheetTitle[sheet] : ''}
					subtitle={
						sheet === 'spec'
							? `${fileName} · revision ${spec.draft_revision}${locked ? ' · read only' : ''}`
							: sheet === 'workflows'
								? 'How records move, and who moves them'
								: undefined
					}
					footer={
						sheet === 'spec' && draft.dirty && !draft.reviewing ? (
							<>
								<span className="mr-auto self-center text-[12px] text-t3">
									{thinking
										? 'The agent is working; save once it’s done.'
										: yamlBroken
											? 'Fix the YAML errors to save.'
											: 'Unsaved — the agent and the preview see it once saved.'}
								</span>
								<Button size="sm" onClick={draft.discard}>
									Discard
								</Button>
								<Button
									size="sm"
									variant="primary"
									loading={draft.busy === 'save'}
									disabled={yamlBroken || thinking}
									onClick={() => draft.save()}
								>
									Save
								</Button>
							</>
						) : undefined
					}
				>
					<div className={cx('pv-sheet', sheet && `pv-${sheet}`)}>
						{sheet === 'spec' && (
							<YamlView
								text={draft.text}
								marks={lineMarks}
								jump={yamlJump}
								editable={!locked}
								onChange={draft.type}
								diagnostics={yamlDiagnostics}
							/>
						)}
						{sheet === 'workflows' && (
							<Suspense fallback={<Skeleton height={240} />}>
								<WorkflowsPanel
									doc={yamlBroken ? undefined : doc}
									dialect={builder.spec_dialect}
									agent={serverSpec.workflows?.processes}
									thinking={thinking}
									onJump={(p) => jumpTo(p)}
								/>
							</Suspense>
						)}
						{sheet === 'checks' && (
							<ChecksList
								rows={rows}
								onJump={(r) =>
									r.issue.code === 'yaml' ? jumpTo('', { line: r.line }) : jumpTo(r.issue.path)
								}
							/>
						)}
						{sheet === 'flags' && (
							<ReviewPanel
								flagsOnly
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
								onShowInYaml={(p) => jumpTo(p)}
							/>
						)}
						{sheet === 'documents' &&
							(documents.length ? (
								<ul className="pv-docs">
									{documents.map((d) => (
										<li key={d.id}>
											<Icon name="file" size={15} />
											<a
												href={documentUrl(appId, requirement.uuid, d.id)}
												target="_blank"
												rel="noreferrer"
												className="min-w-0 flex-1 truncate"
											>
												{d.name}
											</a>
											<small>
												{d.pages ? `${d.pages} pages · ` : ''}
												{Math.max(1, Math.round(d.size / 1024))} KB
											</small>
										</li>
									))}
								</ul>
							) : (
								<div className="card">
									<div className="empty">
										<b>No documents</b>
										This requirement was written from a brief and the chat.
									</div>
								</div>
							))}
					</div>
				</Drawer>
			</BuilderContext.Provider>
		);
	}

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
				{draftingStrip}
				{conflictBar}
				<Tabs<Tab>
					className="bld-tabs"
					value={tab}
					onChange={setTab}
					items={[
						...(embedUrl
							? [
									{ value: 'builder' as const, label: 'Builder' },
									{ value: 'preview' as const, label: 'Preview' },
								]
							: [{ value: 'details' as const, label: 'Details' }]),
						{ value: 'workflows', label: 'Workflows' },
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
							hidden={tab !== 'builder' && tab !== 'preview'}
							preview={tab === 'preview'}
						/>
					)}
					{tab === 'workflows' && (
						<Suspense
							fallback={
								<div className="grid gap-3">
									<Skeleton width="30%" height={18} />
									<Skeleton height={240} />
								</div>
							}
						>
							<WorkflowsPanel
								doc={yamlBroken ? undefined : doc}
								agent={serverSpec.workflows?.processes}
								thinking={thinking}
								onJump={(p) => jumpTo(p, { inTab: 'yaml' })}
							/>
						</Suspense>
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
				{saveBar}
			</div>
		</BuilderContext.Provider>
	);
}
