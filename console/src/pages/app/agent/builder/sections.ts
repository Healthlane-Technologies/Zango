// The builder's navigation: ui.json sections mapped onto pointers in the spec.

import { isWithin, parsePointer, valueAt } from './pointer';

export interface BuilderSection {
	id: string;
	title: string;
	/** Where the section lives; "" with `fields` for sections spread over the root. */
	pointer: string;
	hint?: string;
	order?: number;
	/** Specific pointers shown in this section, instead of the whole of `pointer`. */
	fields?: string[];
	/** For collections of parents (e.g. /programs): the child list shown per parent (e.g. orders). */
	item?: string;
}

export function orderedSections(sections: BuilderSection[] | undefined): BuilderSection[] {
	return [...(sections ?? [])].sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
}

/** Does `pointer` belong to `section`, and how specifically (longer = better)? -1 if not. */
function matchLength(section: BuilderSection, pointer: string): number {
	let best = -1;
	if (section.item) {
		// /programs/<i>/<item>/...
		const base = parsePointer(section.pointer);
		const parts = parsePointer(pointer);
		if (
			parts.length >= base.length + 2 &&
			base.every((b, i) => parts[i] === b) &&
			parts[base.length + 1] === section.item
		)
			best = section.pointer.length + section.item.length + 2;
		// An item section may also show some fields of its own (schemes → /catalogue).
		for (const root of section.fields ?? [])
			if (isWithin(pointer, root)) best = Math.max(best, root.length);
		return best;
	}
	const roots = section.fields?.length ? section.fields : [section.pointer];
	for (const root of roots) {
		if (isWithin(pointer, root)) best = Math.max(best, root.length);
	}
	return best;
}

/** The section a pointer falls in: the most specific match. */
export function sectionOf(sections: BuilderSection[], pointer: string): BuilderSection | undefined {
	let best: BuilderSection | undefined;
	let bestLen = -1;
	for (const s of sections) {
		const len = matchLength(s, pointer);
		if (len > bestLen) {
			best = s;
			bestLen = len;
		}
	}
	return best;
}

function countOf(v: unknown): number {
	if (Array.isArray(v)) return v.length;
	if (v && typeof v === 'object') return Object.keys(v).length;
	return v === undefined || v === null || v === '' ? 0 : 1;
}

/** A rough "how much is here": items in the list, entries in the map, filled fields. */
export function sectionCount(section: BuilderSection, doc: unknown): number {
	if (section.item) {
		const parents = valueAt(doc, section.pointer);
		return Array.isArray(parents)
			? parents.reduce(
					(n, p) => n + countOf((p as Record<string, unknown> | null)?.[section.item!]),
					0,
				)
			: 0;
	}
	if (section.fields?.length) {
		const filled = section.fields.filter((f) => countOf(valueAt(doc, f)) > 0);
		// A section of lists counts their items; a section of scalars counts filled fields.
		return section.fields.every((f) => !Array.isArray(valueAt(doc, f)))
			? filled.length
			: section.fields.reduce((n, f) => n + countOf(valueAt(doc, f)), 0);
	}
	return countOf(valueAt(doc, section.pointer));
}

export function isSectionEmpty(section: BuilderSection, doc: unknown): boolean {
	return sectionCount(section, doc) === 0;
}
