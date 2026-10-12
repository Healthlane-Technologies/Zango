import { parse as parseYaml } from 'yaml';

// What a template's starter spec actually holds, for the detail page: its records with
// their fields, which role may do what to each, and the lifecycles they move through.
// Read from the Zango app spec (App Studio, `zango-app/1`); other spec languages (the PSP
// journey) yield nothing and the page falls back to the catalogue's own lists.

export interface ModelField {
	key: string;
	label: string;
	type: string;
	required: boolean;
	/** The entity a link field points at. */
	to?: string;
}

export interface ModelStatus {
	code: string;
	label: string;
	color: string;
}

export interface ModelEntity {
	code: string;
	name: string;
	module: string;
	kind: string;
	fields: ModelField[];
	/** Entity codes this one links to. */
	links: string[];
	/** role name -> letters (C, R, U, D). */
	access: Record<string, string>;
	statuses: ModelStatus[];
	transitions: Array<{ label: string; roles: string[] }>;
}

export interface SpecModel {
	roles: Array<{ name: string; description: string }>;
	entities: ModelEntity[];
}

type Obj = Record<string, unknown>;
const isObj = (v: unknown): v is Obj => !!v && typeof v === 'object' && !Array.isArray(v);
const arr = (v: unknown): unknown[] => (Array.isArray(v) ? v : v == null ? [] : [v]);
const str = (v: unknown) => (v == null ? '' : String(v));
const titleize = (s: string) =>
	s
		.replace(/[_-]+/g, ' ')
		.trim()
		.replace(/\b\w/g, (c) => c.toUpperCase());

/** A list of single-key maps (`- name: {…}`) or a map, as [key, value] pairs. */
function pairs(v: unknown): Array<[string, Obj]> {
	if (isObj(v)) return Object.entries(v).map(([k, x]) => [k, isObj(x) ? x : {}]);
	return arr(v).flatMap((item): Array<[string, Obj]> => {
		if (typeof item === 'string') return [[item, {}]];
		if (!isObj(item)) return [];
		if (typeof item.key === 'string' || typeof item.code === 'string')
			return [[str(item.key || item.code), item]];
		const [k] = Object.keys(item);
		return k ? [[k, isObj(item[k]) ? (item[k] as Obj) : {}]] : [];
	});
}

const LETTERS: Array<[string, string]> = [
	['add', 'C'],
	['view', 'R'],
	['edit', 'U'],
	['delete', 'D'],
];

function accessOf(v: unknown): Record<string, string> {
	const out: Record<string, string> = {};
	for (const [role, a] of pairs(v)) {
		if (a.no_access) continue;
		const actions = new Set(arr(a.actions ?? a.can).map(str));
		const letters = LETTERS.filter(([act]) => actions.has(act))
			.map(([, l]) => l)
			.join('');
		if (letters) out[role] = letters;
	}
	return out;
}

export function specModel(yamlText: string | null | undefined): SpecModel | null {
	if (!yamlText?.trim()) return null;
	let doc: unknown;
	try {
		doc = parseYaml(yamlText);
	} catch {
		return null;
	}
	if (!isObj(doc) || !Array.isArray(doc.modules)) return null;

	const roles = arr(doc.roles)
		.filter(isObj)
		.map((r) => ({ name: str(r.name), description: str(r.description) }))
		.filter((r) => r.name);

	const entities: ModelEntity[] = [];
	for (const m of arr(doc.modules).filter(isObj)) {
		for (const e of arr(m.entities).filter(isObj)) {
			const code = str(e.code);
			if (!code) continue;
			const fields = pairs(e.fields).map(([key, f]) => ({
				key,
				label: str(f.label) || titleize(key),
				type: str(f.type) || 'text',
				required: !!f.required,
				to: f.type === 'link' || f.type === 'multi_link' ? str(f.to) || undefined : undefined,
			}));
			const wf = isObj(e.workflow) ? e.workflow : null;
			entities.push({
				code,
				name: str(e.name) || titleize(code),
				module: str(m.name) || titleize(str(m.code)),
				kind: str(e.kind),
				fields,
				links: [...new Set(fields.map((f) => f.to).filter((t): t is string => !!t))],
				access: accessOf(e.access),
				statuses: wf
					? pairs(wf.statuses).map(([c, s]) => ({
							code: c,
							label: str(s.label) || titleize(c),
							color: str(s.color) || 'gray',
						}))
					: [],
				transitions: wf
					? arr(wf.transitions)
							.filter(isObj)
							.map((t) => ({
								label: str(t.label) || titleize(str(t.name)),
								roles: arr(t.roles).map(str),
							}))
					: [],
			});
		}
	}
	return entities.length ? { roles, entities } : null;
}

/** The entity most others link to: the template's primary record. */
export function primaryEntity(model: SpecModel): string | undefined {
	const hero = model.entities.find((e) => e.kind === 'hero');
	if (hero) return hero.code;
	const inbound = new Map<string, number>();
	for (const e of model.entities) for (const l of e.links) inbound.set(l, (inbound.get(l) ?? 0) + 1);
	return [...inbound.entries()].sort((a, b) => b[1] - a[1])[0]?.[0];
}

const TYPE_LABEL: Record<string, string> = {
	long_text: 'text',
	multi_choice: 'choices',
	multi_link: 'links',
	integer: 'number',
	decimal: 'number',
};
export const typeLabel = (t: string) => TYPE_LABEL[t] ?? t;
