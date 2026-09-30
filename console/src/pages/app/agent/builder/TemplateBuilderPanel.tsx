import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { SpecIssue } from '@/api/agentMode';
import { Badge, Button, Icon, Tabs, TemplateBadge, type Tone } from '@/ui';
import { ChecksList, type CheckRow } from './ChecksList';
import { BuilderContext, type BuilderCtx } from './context';
import { changedPointers } from './diff';
import { humanPath } from './labels';
import { ancestors } from './pointer';
import type { BuilderProps } from './registry';
import type { Schema } from './schema';
import { SectionDetails } from './SectionDetails';
import { SectionNav, type SectionState } from './SectionNav';
import { orderedSections, sectionCount, sectionOf, type BuilderSection } from './sections';
import { parseSpec, rangeOf } from './yamlDoc';
import { YamlView } from './YamlView';
import './builder.css';

type Tab = 'details' | 'yaml' | 'checks';
type Mode = 'default' | 'all' | 'none';

const FLASH_MS = 1600;

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
	requirement,
	builder,
	spec,
	changed: changedProp,
}: BuilderProps) {
	const root = builder.json_schema as Schema;
	const sections = useMemo<BuilderSection[]>(
		() => orderedSections(builder.ui_schema.sections),
		[builder],
	);
	const parsed = useMemo(() => parseSpec(spec.text), [spec.text]);
	const doc = parsed.value;

	// Changed pointers: what the server says the last turn touched, else a diff against what
	// this panel last showed (so a poll that brings no changed_paths still highlights).
	const previous = useRef<{ rev: number; value: unknown } | null>(null);
	const [diffed, setDiffed] = useState<string[]>([]);
	useEffect(() => {
		const prev = previous.current;
		if (prev && spec.draft_revision > prev.rev && !changedProp.length)
			setDiffed(changedPointers(prev.value, doc));
		else if (changedProp.length) setDiffed([]);
		previous.current = { rev: spec.draft_revision, value: doc };
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
			...spec.issues,
		],
		[parsed.errors, spec.issues],
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

	const [tab, setTab] = useState<Tab>('details');
	const [active, setActive] = useState<string>(() => sections[0]?.id ?? '');
	const section = sections.find((s) => s.id === active) ?? sections[0];
	const [overrides, setOverrides] = useState<Map<string, boolean>>(() => new Map());
	const [mode, setMode] = useState<Record<string, Mode>>({});
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
		}),
		[root, doc, issuesAt, issueWithin, changedWithin, changed, overrides, sectionMode],
	);

	/** Show `pointer`: in the YAML tab move to its line, otherwise open its section and cards. */
	const jumpTo = useCallback(
		(pointer: string, opts: { sectionHint?: string; line?: number; inTab?: Tab } = {}) => {
			const where = opts.inTab ?? (tab === 'yaml' ? 'yaml' : 'details');
			if (where === 'yaml') {
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
		[tab, parsed, sectionFor],
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
	const [tone, label]: [Tone, string] = spec.is_draft
		? ['amber', 'Draft']
		: spec.status === 'approved'
			? ['green', 'Approved']
			: spec.status === 'ready'
				? ['accent', 'Ready for review']
				: ['amber', 'Draft'];

	return (
		<BuilderContext.Provider value={ctx}>
			<div className="bld">
				<div className="bld-h">
					{spec.template && <TemplateBadge template={spec.template} />}
					<Badge tone={tone} dot>
						{label}
					</Badge>
					<span className="mono text-[11.5px] text-t4">rev {spec.draft_revision}</span>
					{requirement.is_thinking && (
						<span className="bld-thinking">
							<span className="spin" />
							Agent is editing…
						</span>
					)}
					{changed.length > 0 && (
						<Button size="xs" variant="secondary" className="ml-auto bld-chg" onClick={nextChanged}>
							<i className="bv-dot chg" />
							Changed by agent ({changed.length})
							<Icon name="up" size={12} className="rotate-180" />
						</Button>
					)}
				</div>
				<Tabs<Tab>
					className="bld-tabs"
					value={tab}
					onChange={setTab}
					items={[
						{ value: 'details', label: 'Details' },
						{ value: 'yaml', label: 'YAML' },
						{
							value: 'checks',
							label: errors ? `Checks · ${errors} to fix` : 'Checks',
							count: issues.length || undefined,
						},
					]}
				/>
				<div ref={body} className="bld-b">
					{tab === 'details' && section && (
						<div className="bld-split">
							<SectionNav sections={states} active={section.id} onSelect={setActive} />
							<SectionDetails
								key={section.id}
								section={section}
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
					{tab === 'yaml' && <YamlView text={spec.text} marks={lineMarks} jump={yamlJump} />}
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
			</div>
		</BuilderContext.Provider>
	);
}
