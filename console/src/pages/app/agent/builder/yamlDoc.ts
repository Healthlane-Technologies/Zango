// The spec as a `yaml` Document (YAML 1.2: a bare `on:` key stays the string "on"), with
// JSON Pointer → source range lookups for the YAML view and the checks list.

import { isMap, isPair, isScalar, isSeq, LineCounter, parseDocument, type Document } from 'yaml';
import { parsePointer } from './pointer';

export interface ParsedSpec {
	doc: Document;
	value: unknown;
	errors: Array<{ message: string; line?: number }>;
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
