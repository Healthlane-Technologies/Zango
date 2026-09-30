import { parsePointer } from './pointer';
import { branchFor, childSchema, isSingleKeyMap, titleOf, ui, type Schema } from './schema';
import { fill } from './template';

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
			nextValue = value[Number(part)];
			const item = branchFor(root, next, nextValue);
			const hint = { ...ui(parent), ...ui(item) };
			const label = isSingleKeyMap(nextValue)
				? Object.keys(nextValue)[0]
				: nextValue && typeof nextValue === 'object'
					? fill(hint.itemTitle, nextValue)
					: String(nextValue ?? '');
			out.push(label || `#${Number(part) + 1}`);
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
