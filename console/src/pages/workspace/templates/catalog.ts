import type { TemplateSummary } from '@/api/templates';
import type { IconName } from '@/ui';

// Pure helpers for the template gallery, ported from the prototype's tplList / tplGroups /
// TSORT / VT. No React here, so they can be unit-checked in node.

/** Category colours and a default icon, after the prototype's VT map. */
const VT: Record<string, [bg: string, fg: string, icon: IconName]> = {
	'Patient Services': ['#FEF2F2', '#B91C1C', 'heart'],
	'Advanced Therapies': ['#FDF4FF', '#A21CAF', 'dna'],
	'Commercial Operations': ['#EEF2FF', '#4338CA', 'cart'],
	'Traceability & Supply Chain': ['#F0FDFA', '#0F766E', 'truck'],
	'Compliance & Quality': ['#F4F4F5', '#3F3F46', 'shield'],
	'Regulatory Affairs': ['#FFFBEB', '#B45309', 'file'],
	'Medical Affairs': ['#EFF6FF', '#1D4ED8', 'book'],
	'Clinical Operations': ['#ECFEFF', '#0E7490', 'pulse'],
	'Market Access': ['#F0FDF4', '#15803D', 'card'],
	'Cross-functional': ['#F4F4F5', '#52525B', 'apps'],
};
const FALLBACK: [string, string, IconName] = ['#F4F4F5', '#52525B', 'tpl'];

const ICONS = new Set<string>([
	'heart',
	'dna',
	'cart',
	'truck',
	'shield',
	'file',
	'book',
	'pulse',
	'card',
	'apps',
	'gift',
	'barcode',
	'mic',
	'eye',
	'bot',
	'tpl',
	'users',
	'pkg',
	'blank',
	'agent',
	'badge',
	'key',
]);

export function categoryStyle(category: string): { bg: string; fg: string; icon: IconName } {
	const [bg, fg, icon] = VT[category] ?? FALLBACK;
	return { bg, fg, icon };
}

export function templateIcon(t: Pick<TemplateSummary, 'icon' | 'category'>): IconName {
	return ICONS.has(t.icon) ? (t.icon as IconName) : categoryStyle(t.category).icon;
}

export type SortKey = 'used' | 'name' | 'updated';

export const SORTS: Record<
	SortKey,
	[label: string, cmp: (a: TemplateSummary, b: TemplateSummary) => number]
> = {
	used: ['Most used', (a, b) => b.apps_using - a.apps_using || a.name.localeCompare(b.name)],
	name: ['Name A–Z', (a, b) => a.name.localeCompare(b.name)],
	updated: [
		'Recently updated',
		(a, b) => ts(b.published_at) - ts(a.published_at) || a.name.localeCompare(b.name),
	],
};

function ts(iso: string | null): number {
	const t = iso ? Date.parse(iso) : NaN;
	return Number.isNaN(t) ? 0 : t;
}

export const hasAgents = (t: TemplateSummary) => (t.catalogue.recommended_agents?.length ?? 0) > 0;

export function tokens(q: string): string[] {
	return q.toLowerCase().split(/\s+/).filter(Boolean);
}

const wordStart = (h: string, w: string) =>
	h.startsWith(w) ||
	h.includes(' ' + w) ||
	h.includes('-' + w) ||
	h.includes('/' + w) ||
	h.includes('(' + w);

/** 0 = no match. Every token must match somewhere; name matches weigh most. */
export function score(t: TemplateSummary, words: string[]): number {
	if (!words.length) return 1;
	const n = t.name.toLowerCase();
	const c = t.catalogue;
	const other = [
		t.one_liner,
		c.description ?? '',
		t.category,
		...(c.workflows ?? []).map((w) => w.name),
		...(c.roles ?? []).map((r) => r.name),
		...(c.aka ?? []),
	]
		.join(' ')
		.toLowerCase();
	let sc = 0;
	for (const w of words) {
		if (n.startsWith(w)) sc += 4;
		else if (wordStart(n, w)) sc += 3;
		else if (wordStart(other, w)) sc += 1;
		else if (w.length > 3 && (n + ' ' + other).includes(w)) sc += 0.5;
		else return 0;
	}
	return sc;
}

export interface Filters {
	q: string;
	category: string; // '' = all
	sort: SortKey;
	withAgents: boolean;
	used: boolean;
}

export function filterTemplates(all: TemplateSummary[], f: Filters): TemplateSummary[] {
	const words = tokens(f.q);
	const cmp = SORTS[f.sort][1];
	return all
		.map((t) => [t, score(t, words)] as const)
		.filter(
			([t, sc]) =>
				sc > 0 &&
				(!f.category || t.category === f.category) &&
				(!f.withAgents || hasAgents(t)) &&
				(!f.used || t.apps_using > 0),
		)
		.sort((a, b) => b[1] - a[1] || cmp(a[0], b[0]))
		.map(([t]) => t);
}

/** One flat group while a category or search narrows the list; by category otherwise. */
export function groupTemplates(
	list: TemplateSummary[],
	f: Pick<Filters, 'q' | 'category'>,
): Array<[heading: string | null, items: TemplateSummary[]]> {
	if (f.category || tokens(f.q).length) return list.length ? [[null, list]] : [];
	const groups = new Map<string, TemplateSummary[]>();
	for (const t of list) {
		const k = t.category || 'Other';
		groups.set(k, [...(groups.get(k) ?? []), t]);
	}
	return [...groups.entries()];
}

export function categories(all: TemplateSummary[]): Array<[name: string, count: number]> {
	const counts = new Map<string, number>();
	for (const t of all)
		counts.set(t.category || 'Other', (counts.get(t.category || 'Other') ?? 0) + 1);
	return [...counts.entries()].sort((a, b) => a[0].localeCompare(b[0]));
}

/** Split `text` into [plain, match] segments for the search words (for <mark>). */
export function highlight(text: string, q: string): Array<[string, boolean]> {
	const words = tokens(q).filter((w) => w.length > 0);
	if (!words.length) return [[text, false]];
	const re = new RegExp(
		`(${words.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`,
		'ig',
	);
	return text
		.split(re)
		.filter(Boolean)
		.map((part) => [part, words.includes(part.toLowerCase())]);
}

export function formatUpdated(iso: string | null): string {
	if (!iso) return '—';
	const d = new Date(iso);
	return Number.isNaN(d.getTime())
		? '—'
		: d.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
}

/** The gallery's category order (the mockup's CATS); others follow alphabetically. */
const CATEGORY_ORDER = [
	'Patient Services',
	'Advanced Therapies',
	'Commercial Operations',
	'Traceability & Supply Chain',
	'Compliance & Quality',
	'Regulatory Affairs',
	'Medical Affairs',
	'Clinical Operations',
	'Market Access',
	'Cross-functional',
];

export function orderedCategories(all: TemplateSummary[]): Array<[name: string, count: number]> {
	const rank = (c: string) => {
		const i = CATEGORY_ORDER.indexOf(c);
		return i < 0 ? CATEGORY_ORDER.length : i;
	};
	return categories(all).sort((a, b) => rank(a[0]) - rank(b[0]) || a[0].localeCompare(b[0]));
}

/** Three to feature: the most used, then the most complete catalogue entries. */
export function featured(all: TemplateSummary[], n = 3): TemplateSummary[] {
	const richness = (t: TemplateSummary) =>
		(t.catalogue.workflows?.length ?? 0) + (t.catalogue.roles?.length ?? 0);
	return [...all]
		.filter((t) => !t.is_beta)
		.sort(
			(a, b) =>
				b.apps_using - a.apps_using ||
				richness(b) - richness(a) ||
				a.name.localeCompare(b.name),
		)
		.slice(0, n);
}

const STOP = new Set(
	'a an and are as at be by for from has have in into is it its of on or our that the their them they this to we when where which who will with want need app apps system track manage build'.split(
		' ',
	),
);

export interface Match {
	template: TemplateSummary;
	score: number;
	/** What in the template the description touched: workflow and role names. */
	workflows: string[];
	roles: string[];
}

/** Templates ranked against a free-text description of what someone wants to build. */
export function describeMatches(all: TemplateSummary[], text: string, n = 3): Match[] {
	const words = [
		...new Set(
			text
				.toLowerCase()
				.split(/[^a-z0-9]+/)
				.filter((w) => w.length > 2 && !STOP.has(w)),
		),
	];
	if (!words.length) return [];
	const stem = (w: string) => w.replace(/(ies|es|s|ing|ed)$/, '');
	const hit = (hay: string) => words.some((w) => hay.toLowerCase().includes(stem(w)));
	return all
		.map((t) => {
			const c = t.catalogue;
			const fields: Array<[string, number]> = [
				[t.name, 4],
				[(c.aka ?? []).join(' '), 3],
				[t.one_liner + ' ' + (c.description ?? ''), 1.5],
				[(c.fits_when ?? []).join(' '), 1.5],
				[(c.workflows ?? []).map((w) => w.name + ' ' + (w.description ?? '')).join(' '), 2],
				[(c.roles ?? []).map((r) => r.name).join(' '), 1],
				[(c.data_objects ?? []).join(' '), 1],
				[t.category, 0.5],
			];
			let score = 0;
			for (const w of words) {
				const s = stem(w);
				for (const [hay, weight] of fields) if (hay.toLowerCase().includes(s)) score += weight;
			}
			return {
				template: t,
				score,
				workflows: (c.workflows ?? []).map((w) => w.name).filter(hit).slice(0, 3),
				roles: (c.roles ?? []).map((r) => r.name).filter(hit).slice(0, 2),
			};
		})
		.filter((m) => m.score > 0)
		.sort((a, b) => b.score - a.score || b.template.apps_using - a.template.apps_using)
		.slice(0, n);
}
