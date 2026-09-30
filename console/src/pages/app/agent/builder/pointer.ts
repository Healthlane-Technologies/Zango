// RFC 6901 JSON Pointers: "" is the document root, "/a/0/b" walks into it.

export type Segment = string | number;

export function parsePointer(pointer: string): string[] {
	if (!pointer) return [];
	return pointer
		.slice(1)
		.split('/')
		.map((s) => s.replace(/~1/g, '/').replace(/~0/g, '~'));
}

export function joinPointer(parts: Array<string | number>): string {
	return parts.map((p) => '/' + String(p).replace(/~/g, '~0').replace(/\//g, '~1')).join('');
}

export function child(pointer: string, key: string | number): string {
	return pointer + joinPointer([key]);
}

/** `pointer` and every ancestor, root excluded, nearest first. */
export function ancestors(pointer: string): string[] {
	const parts = parsePointer(pointer);
	const out: string[] = [];
	for (let i = parts.length; i > 0; i--) out.push(joinPointer(parts.slice(0, i)));
	return out;
}

export function isWithin(pointer: string, base: string): boolean {
	return base === '' || pointer === base || pointer.startsWith(base + '/');
}

export function valueAt(doc: unknown, pointer: string): unknown {
	let node: unknown = doc;
	for (const part of parsePointer(pointer)) {
		if (Array.isArray(node)) node = node[Number(part)];
		else if (node && typeof node === 'object') node = (node as Record<string, unknown>)[part];
		else return undefined;
	}
	return node;
}
