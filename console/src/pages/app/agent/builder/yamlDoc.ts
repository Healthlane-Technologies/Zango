// The spec as a `yaml` Document (YAML 1.2: a bare `on:` key stays the string "on"), with
// JSON Pointer → source range lookups for the YAML view and the checks list.

import { isMap, isPair, isScalar, isSeq, LineCounter, parseDocument, type Document } from 'yaml';
import { parsePointer } from './pointer';

export interface ParsedSpec {
	doc: Document;
	value: unknown;
	/** `from`/`to` are character offsets of the problem, for editor diagnostics. */
	errors: Array<{ message: string; line?: number; from?: number; to?: number }>;
	lines: LineCounter;
	text: string;
}

export function parseSpec(text: string): ParsedSpec {
	const lines = new LineCounter();
	const doc = parseDocument(text ?? '', {
		version: '1.2',
		lineCounter: lines,
		prettyErrors: false,
	});
	const errors = doc.errors.map((e) => ({
		message: e.message.split('\n')[0],
		line: e.linePos?.[0]?.line,
		from: e.pos?.[0],
		to: e.pos?.[1],
	}));
	let value: unknown = null;
	try {
		value = doc.toJS({ maxAliasCount: 100 });
	} catch {
		value = null;
	}
	return { doc, value, errors, lines, text: text ?? '' };
}

export interface SourceRange {
	from: number;
	to: number;
	line: number;
	endLine: number;
}

/**
 * Where `pointer` lives in the text: the key through the end of the value for a map entry,
 * the item for a list entry. Falls back to the nearest ancestor that exists.
 */
export function rangeOf(parsed: ParsedSpec, pointer: string): SourceRange | null {
	let node: unknown = parsed.doc.contents;
	let range: [number, number] | null = null;
	for (const part of parsePointer(pointer)) {
		if (isMap(node)) {
			const pair = node.items.find((p) => isPair(p) && keyText(p.key) === part);
			if (!pair) break;
			const start = (pair.key as { range?: number[] } | null)?.range?.[0];
			const val = pair.value as { range?: number[] } | null;
			const end =
				val?.range?.[2] ?? val?.range?.[1] ?? (pair.key as { range?: number[] })?.range?.[1];
			if (start !== undefined && end !== undefined) range = [start, end];
			node = pair.value;
		} else if (isSeq(node)) {
			const item = node.items[Number(part)] as { range?: number[] } | undefined;
			if (!item) break;
			if (item.range) range = [item.range[0], item.range[2] ?? item.range[1]];
			node = item;
		} else break;
	}
	if (!range) return null;
	const a = parsed.lines.linePos(range[0]);
	// A block value's range ends at the start of the next line; don't count that line.
	const endOffset = Math.max(range[0], range[1] - 1);
	const b = parsed.lines.linePos(endOffset);
	return { from: range[0], to: range[1], line: a.line, endLine: b.line };
}

function keyText(key: unknown): string {
	if (isScalar(key)) return String(key.value);
	return String(key);
}

// ---- editing ------------------------------------------------------------------------------
//
// Form edits are applied to a `yaml` Document and printed back, so comments, key order and
// flow/block style survive. A scalar replaced by a scalar keeps its node (and its comments).

export type SpecEdit =
	| { op: 'set'; path: string; value: unknown }
	| { op: 'add'; path: string; value: unknown; index?: number }
	| { op: 'remove'; path: string }
	| { op: 'move'; path: string; from: number; to: number }
	| { op: 'rename'; path: string; to: string };

export class SpecEditError extends Error {}

const PRINT = { lineWidth: 0 };

/** The `yaml` getIn/setIn path for a JSON Pointer: sequence steps become numbers. */
function docPath(doc: Document, pointer: string): Array<string | number> {
	const out: Array<string | number> = [];
	let node: unknown = doc.contents;
	for (const part of parsePointer(pointer)) {
		if (isSeq(node)) {
			const i = Number(part);
			out.push(i);
			node = node.items[i];
		} else {
			out.push(part);
			node = isMap(node) ? node.get(part, true) : undefined;
		}
	}
	return out;
}

/** `text` with `edit` applied. Throws SpecEditError if the YAML can't be edited as a document. */
export function applyEdit(text: string, edit: SpecEdit): string {
	// Widened from Document.Parsed: edits put freshly created (unparsed) nodes into it.
	const doc = parseDocument(text ?? '', { version: '1.2' }) as unknown as Document;
	if (doc.errors.length) throw new SpecEditError('Fix the YAML errors first.');
	if (doc.contents === null || doc.contents === undefined) doc.contents = doc.createNode({});
	const path = docPath(doc, edit.path);
	switch (edit.op) {
		case 'set': {
			if (!path.length) {
				doc.contents = doc.createNode(edit.value);
				break;
			}
			const cur = doc.getIn(path, true);
			const scalarValue = edit.value === null || typeof edit.value !== 'object';
			if (isScalar(cur) && scalarValue) cur.value = edit.value;
			else doc.setIn(path, doc.createNode(edit.value));
			break;
		}
		case 'add': {
			const target = path.length ? doc.getIn(path, true) : doc.contents;
			if (isSeq(target)) {
				const at = edit.index ?? target.items.length;
				target.items.splice(
					Math.max(0, Math.min(at, target.items.length)),
					0,
					doc.createNode(edit.value),
				);
			} else if (target === undefined) {
				doc.setIn(path, doc.createNode(edit.value));
			} else if (isMap(target) || target === null) {
				throw new SpecEditError(`${edit.path} already exists.`);
			} else {
				throw new SpecEditError(`Can't add to ${edit.path}.`);
			}
			break;
		}
		case 'remove':
			if (!path.length) throw new SpecEditError('The whole spec cannot be removed.');
			doc.deleteIn(path);
			break;
		case 'move': {
			const seq = doc.getIn(path, true);
			if (!isSeq(seq)) throw new SpecEditError(`${edit.path} is not a list.`);
			const [item] = seq.items.splice(edit.from, 1);
			seq.items.splice(Math.max(0, Math.min(edit.to, seq.items.length)), 0, item);
			break;
		}
		case 'rename': {
			const owner = path.length === 1 ? doc.contents : doc.getIn(path.slice(0, -1), true);
			const old = String(path[path.length - 1]);
			if (!isMap(owner)) throw new SpecEditError(`${edit.path} is not a key.`);
			if (!edit.to.trim()) throw new SpecEditError('A name is required.');
			if (owner.has(edit.to)) throw new SpecEditError(`${edit.to} already exists.`);
			const pair = owner.items.find((p) => isPair(p) && keyText(p.key) === old);
			if (!pair) throw new SpecEditError(`${edit.path} does not exist.`);
			if (isScalar(pair.key)) pair.key.value = edit.to;
			else pair.key = doc.createNode(edit.to);
			break;
		}
	}
	return keepFormatting(text, doc.toString(PRINT));
}

/**
 * The printer normalises flow-collection spacing (`{ a }` vs `[a]`) and implicit pairs, so
 * a one-field edit would otherwise rewrite dozens of untouched lines. Keep every original
 * line whose printed counterpart says the same thing (line-level LCS), so a save's diff —
 * and the YAML the user reads — only moves where they actually edited.
 */
export function keepFormatting(original: string, printed: string): string {
	const a = original.split('\n');
	const b = printed.split('\n');
	if (a.length * b.length > 4_000_000) return printed;
	const norm = (l: string) => l.replace(/\s+/g, '').replace(/\{\}/g, '\u0000').replace(/[{}]/g, '');
	const na = a.map(norm);
	const nb = b.map(norm);
	const n = a.length;
	const m = b.length;
	const lcs: Uint32Array[] = Array.from({ length: n + 1 }, () => new Uint32Array(m + 1));
	for (let i = n - 1; i >= 0; i--)
		for (let j = m - 1; j >= 0; j--)
			lcs[i][j] = na[i] === nb[j] ? lcs[i + 1][j + 1] + 1 : Math.max(lcs[i + 1][j], lcs[i][j + 1]);
	const out: string[] = [];
	let i = 0;
	let j = 0;
	while (j < m) {
		if (i < n && na[i] === nb[j]) {
			out.push(a[i]);
			i++;
			j++;
		} else if (i < n && lcs[i + 1][j] >= lcs[i][j + 1]) i++;
		else {
			out.push(b[j]);
			j++;
		}
	}
	return out.join('\n');
}
