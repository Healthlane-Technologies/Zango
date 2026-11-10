import { parsePointer } from './pointer';
import { branchFor, childSchema, isSingleKeyMap, titleOf, ui, type Schema } from './schema';
import { fill } from './template';

/** Index of the list item a pointer segment names: a number, or an `@code` selector. */
function itemIndex(list: unknown[], part: string): number {
	if (!part.startsWith('@')) return Number(part);
	const code = part.slice(1);
	return list.findIndex(
		(it) =>
			!!it &&
			typeof it === 'object' &&
			((it as Record<string, unknown>).code === code ||
				(isSingleKeyMap(it) && Object.keys(it)[0] === code)),
	);
}

/** "Programs › Enhertu PAP › Orders › Free vials" for a pointer, from schema titles and item titles. */
export function humanPath(root: Schema, doc: unknown, pointer: string): string {
	const out: string[] = [];
	let schema: Schema = root;
	let value: unknown = doc;
	// Set right after labelling a keyed entry (`- name: {…}`) by its key, so the key segment
	// that follows isn't repeated.
	let labelledByKey = false;
	for (const part of parsePointer(pointer)) {
		const parent = branchFor(root, schema, value);
		const next = childSchema(root, parent, part, value);
		let nextValue: unknown;
		if (Array.isArray(value)) {
			const at = itemIndex(value, part);
			nextValue = value[at];
			const item = branchFor(root, next, nextValue);
			const hint = { ...ui(parent), ...ui(item) };
			const label = isSingleKeyMap(nextValue)
				? Object.keys(nextValue)[0]
				: nextValue && typeof nextValue === 'object'
					? fill(hint.itemTitle, nextValue)
					: String(nextValue ?? '');
			const own =
				nextValue && typeof nextValue === 'object'
					? [
							('name' in nextValue && nextValue.name) || '',
							('title' in nextValue && nextValue.title) || '',
							('code' in nextValue && nextValue.code) || '',
						].find((v) => typeof v === 'string' && v)
					: '';
			out.push(label || (own as string) || (at >= 0 ? `#${at + 1}` : part.replace(/^@/, '')));
			labelledByKey = isSingleKeyMap(nextValue);
		} else {
			nextValue =
				value && typeof value === 'object' ? (value as Record<string, unknown>)[part] : undefined;
			if (!labelledByKey)
				out.push(parent.properties && part in parent.properties ? titleOf(next, part) : part);
			labelledByKey = false;
		}
		schema = next;
		value = nextValue;
	}
	return out.filter(Boolean).join(' › ');
}
