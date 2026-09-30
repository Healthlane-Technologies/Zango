import { child } from './pointer';

/**
 * Pointers where `before` and `after` differ, as specific as possible: a changed scalar
 * reports its own pointer; an added or removed key or item reports that key/item.
 */
export function changedPointers(before: unknown, after: unknown, base = ''): string[] {
	if (Object.is(before, after)) return [];
	const bothArrays = Array.isArray(before) && Array.isArray(after);
	const bothObjects = isObj(before) && isObj(after);
	if (bothArrays) {
		const out: string[] = [];
		const n = Math.max(before.length, after.length);
		for (let i = 0; i < n; i++) out.push(...changedPointers(before[i], after[i], child(base, i)));
		return out;
	}
	if (bothObjects) {
		const out: string[] = [];
		for (const k of new Set([...Object.keys(before), ...Object.keys(after)]))
			out.push(...changedPointers(before[k], after[k], child(base, k)));
		return out;
	}
	return [base];
}

function isObj(v: unknown): v is Record<string, unknown> {
	return !!v && typeof v === 'object' && !Array.isArray(v);
}
