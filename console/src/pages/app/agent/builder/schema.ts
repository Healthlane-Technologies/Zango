// Walking a template's JSON Schema alongside the spec it describes. Read-only helpers for
// the builder: resolve $refs, find the subschema at a pointer, classify how to render it.

import { parsePointer } from './pointer';

export interface XUi {
	widget?: 'textarea' | 'tags' | 'switch' | 'keyed' | 'map';
	summary?: string;
	itemTitle?: string;
	ref?: string;
	refKey?: string;
	keyTitle?: string;
	keyRef?: string;
	bareAllowed?: boolean;
	hidden?: boolean;
}

export interface Schema {
	$ref?: string;
	$defs?: Record<string, Schema>;
	type?: string | string[];
	title?: string;
	description?: string;
	properties?: Record<string, Schema>;
	additionalProperties?: boolean | Schema;
	items?: Schema;
	anyOf?: Schema[];
	oneOf?: Array<Schema & { const?: unknown }>;
	enum?: unknown[];
	const?: unknown;
	required?: string[];
	format?: string;
	minProperties?: number;
	maxProperties?: number;
	'x-ui'?: XUi;
	[k: string]: unknown;
}

const EMPTY: Schema = {};

/** Follow `#/$defs/...` refs, keeping the referring node's title/description/x-ui on top. */
export function resolve(root: Schema, node: Schema | undefined): Schema {
	let cur = node ?? EMPTY;
	let overlay: Schema = {};
	for (let i = 0; i < 20 && cur.$ref; i++) {
		const { $ref, ...rest } = cur;
		overlay = {
			...rest,
			...overlay,
			'x-ui': { ...(rest['x-ui'] ?? {}), ...(overlay['x-ui'] ?? {}) },
		};
		const name = $ref.split('/').pop() ?? '';
		cur = root.$defs?.[name] ?? EMPTY;
	}
	if (!Object.keys(overlay).length) return cur;
	const merged: Schema = { ...cur, ...stripUndefined(overlay) };
	merged['x-ui'] = { ...(cur['x-ui'] ?? {}), ...(overlay['x-ui'] ?? {}) };
	return merged;
}

function stripUndefined(o: Schema): Schema {
	const out: Schema = {};
	for (const [k, v] of Object.entries(o))
		if (v !== undefined && !(k === 'x-ui' && !Object.keys(v as object).length)) out[k] = v;
	return out;
}

export const ui = (s: Schema): XUi => s['x-ui'] ?? {};

function typesOf(s: Schema): string[] {
	if (Array.isArray(s.type)) return s.type;
	if (s.type) return [s.type];
	if (s.properties || s.additionalProperties !== undefined) return ['object'];
	if (s.items) return ['array'];
	if (s.enum) return [...new Set(s.enum.map(jsType))];
	return [];
}

export function jsType(v: unknown): string {
	if (v === null || v === undefined) return 'null';
	if (Array.isArray(v)) return 'array';
	if (typeof v === 'number') return Number.isInteger(v) ? 'integer' : 'number';
	return typeof v;
}

function fits(s: Schema, v: unknown): boolean {
	const types = typesOf(s);
	if (!types.length) return true;
	const t = jsType(v);
	return types.includes(t) || (t === 'integer' && types.includes('number'));
}

/** The anyOf/oneOf branch that describes `value` (the first that fits), or the node itself. */
export function branchFor(root: Schema, node: Schema, value: unknown): Schema {
	const s = resolve(root, node);
	const options = s.anyOf ?? (s.oneOf && !s.oneOf.every((o) => 'const' in o) ? s.oneOf : undefined);
	if (!options) return s;
	const branches = options.map((b) => resolve(root, b));
	const pick =
		value === undefined
			? branches.find((b) => typesOf(b).includes('object') || typesOf(b).includes('array'))
			: branches.find((b) => fits(b, value));
	const chosen = pick ?? branches[0] ?? EMPTY;
	// The wrapper's title and x-ui describe the whole thing; keep them.
	return {
		...chosen,
		title: s.title ?? chosen.title,
		description: s.description ?? chosen.description,
		'x-ui': { ...(chosen['x-ui'] ?? {}), ...(s['x-ui'] ?? {}) },
	};
}

/** The schema describing a direct child of `node` (by property name or array index). */
export function childSchema(
	root: Schema,
	node: Schema,
	key: string,
	parentValue?: unknown,
): Schema {
	const s = branchFor(root, node, parentValue);
	if (Array.isArray(parentValue) || (!s.properties && s.items)) return resolve(root, s.items);
	if (s.properties && key in s.properties) return resolve(root, s.properties[key]);
	if (s.additionalProperties && typeof s.additionalProperties === 'object')
		return resolve(root, s.additionalProperties);
	if (s.items) return resolve(root, s.items);
	return EMPTY;
}

/** The (resolved, branch-selected) schema at `pointer`, walking with the document for anyOf choices. */
export function subschemaAt(root: Schema, pointer: string, doc?: unknown): Schema {
	let node: Schema = root;
	let value: unknown = doc;
	for (const part of parsePointer(pointer)) {
		node = childSchema(root, node, part, value);
		if (Array.isArray(value)) value = value[Number(part)];
		else if (value && typeof value === 'object') value = (value as Record<string, unknown>)[part];
		else value = undefined;
	}
	return branchFor(root, node, value);
}

/** A human label for a schema node: its title, else the key humanised. */
export function titleOf(s: Schema, key?: string | number): string {
	if (s.title) return s.title;
	if (key === undefined || typeof key === 'number') return '';
	return humanise(key);
}

export function humanise(key: string): string {
	const t = key.replace(/[_-]+/g, ' ').trim();
	return t.charAt(0).toUpperCase() + t.slice(1);
}

/** Title for an enum value: a oneOf const title if the schema has one. */
export function enumLabel(s: Schema, v: unknown): string {
	const hit = s.oneOf?.find((o) => o.const === v);
	return hit?.title ?? String(v);
}

export type Kind = 'scalar' | 'tags' | 'text' | 'keyed' | 'map' | 'cards' | 'object' | 'unknown';

/** How to render `value` described by `s` (already branch-selected). */
export function kindOf(root: Schema, s: Schema, value: unknown): Kind {
	const hint = ui(s);
	if (hint.widget === 'textarea' || s.format === 'textarea') return 'text';
	if (Array.isArray(value)) {
		const item = resolve(root, s.items);
		if (hint.widget === 'keyed' || ui(item).widget === 'keyed') return 'keyed';
		if (value.every((v) => v === null || typeof v !== 'object')) return 'tags';
		if (value.every(isSingleKeyMap)) return 'keyed';
		return 'cards';
	}
	if (value && typeof value === 'object') {
		if (hint.widget === 'map' || (!s.properties && typeof s.additionalProperties === 'object'))
			return 'map';
		return 'object';
	}
	if (hint.widget === 'tags') return 'tags';
	if (value === undefined || value === null) return 'unknown';
	return 'scalar';
}

export function isSingleKeyMap(v: unknown): v is Record<string, unknown> {
	return !!v && typeof v === 'object' && !Array.isArray(v) && Object.keys(v).length === 1;
}
