// x-ui templates: "{name} · {fields.length} fields", "{from} → {to}", "buy {a} get {b}", "{key}".

const EDGE = /^[\s·•|,→:-]+|[\s·•|,→:-]+$/g;

function lookup(value: unknown, path: string, key?: string): unknown {
	if (path === 'key') return key;
	let cur: unknown = value;
	for (const part of path.split('.')) {
		if (part === 'length') {
			if (Array.isArray(cur) || typeof cur === 'string') return cur.length;
			if (cur && typeof cur === 'object') return Object.keys(cur).length;
			return undefined;
		}
		if (cur && typeof cur === 'object' && !Array.isArray(cur))
			cur = (cur as Record<string, unknown>)[part];
		else return undefined;
	}
	return cur;
}

function show(v: unknown): string {
	if (v === undefined || v === null || v === '') return '';
	if (Array.isArray(v)) return v.map(show).filter(Boolean).join(', ');
	if (typeof v === 'object') return '';
	return String(v);
}

/**
 * Fill a template. A placeholder that resolves to nothing is dropped together with the
 * literal text just before it (its label or separator); trailing text survives only when
 * the last placeholder did. Leftover separators at the edges are trimmed.
 */
export function fill(template: string | undefined, value: unknown, key?: string): string {
	if (!template) return '';
	const parts = template.split(/(\{[^}]+\})/);
	const out: string[] = [];
	let lastFilled = true;
	for (let i = 0; i < parts.length; i += 2) {
		const literal = parts[i];
		const placeholder = parts[i + 1];
		if (placeholder === undefined) {
			if (lastFilled) out.push(literal);
			break;
		}
		const text = show(lookup(value, placeholder.slice(1, -1).trim(), key));
		if (text) out.push(literal, text);
		lastFilled = !!text;
	}
	return out.join('').replace(EDGE, '').trim();
}
