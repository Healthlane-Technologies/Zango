/**
 * Read a template spec — journey.yaml — as highlights.
 *
 * A template requirement is configuration, not prose: there are no headings to
 * match on, and what the user wants to check at a glance is different too. Not
 * "what did I ask for" but "did it hear my program right" — the roles, the
 * programs, the documents, the stages a patient moves through.
 *
 * Deliberately a scanner and not a YAML parser. The spec is model output that
 * the user can then edit by hand, and a parser would throw on a half-typed line
 * and blank the whole panel, where a scanner just shows a little less.
 */

/** Lines as { indent, text }, with blanks and whole-line comments dropped. */
function scan(spec) {
	return spec
		.split('\n')
		.map((raw) => ({
			indent: raw.length - raw.trimStart().length,
			text: raw.trim(),
		}))
		.filter((l) => l.text && !l.text.startsWith('#'));
}

/** The shallowest indent in a block — the level its own keys sit at. */
function base(lines) {
	return lines.length ? Math.min(...lines.map((l) => l.indent)) : 0;
}

const uncomment = (text) => text.replace(/\s+#.*$/, '').trim();

/** The lines nested under `key:` within this block. */
function section(lines, key) {
	const at = base(lines);
	const head = lines.findIndex((l) => l.indent === at && uncomment(l.text) === `${key}:`);
	if (head < 0) return [];
	const body = [];
	for (let i = head + 1; i < lines.length; i += 1) {
		if (lines[i].indent <= at) break;
		body.push(lines[i]);
	}
	return body;
}

/** The scalar value of `key:` in this block. */
function value(lines, key) {
	const at = base(lines);
	const line = lines.find((l) => l.indent === at && l.text.startsWith(`${key}:`));
	if (!line) return '';
	return uncomment(line.text.slice(key.length + 1)).replace(/^["']|["']$/g, '');
}

/** A flow list — `[a, b, c]` or a bare scalar — as its members. */
function members(raw) {
	return raw
		.replace(/^\[|\]$/g, '')
		.split(',')
		.map((item) => item.trim())
		.filter(Boolean);
}

/** Mapping keys at this block's own level — `Manager: {}` → `Manager`. */
function mappingKeys(lines) {
	const at = base(lines);
	return lines
		.filter((l) => l.indent === at)
		.map((l) => l.text.match(/^([A-Za-z][\w .-]*)\s*:/))
		.filter(Boolean)
		.map((m) => m[1]);
}

/** Sequence entries at this block's own level, each with the lines under it. */
function entries(lines) {
	const at = base(lines);
	const out = [];
	lines.forEach((line) => {
		if (line.indent === at && line.text.startsWith('- ')) {
			out.push({ head: uncomment(line.text.slice(2)), lines: [] });
		} else if (out.length) {
			out[out.length - 1].lines.push(line);
		}
	});
	return out;
}

/**
 * What an entry is called. Covers both shapes the spec uses: `- code: pap`
 * with a `name:` beneath it, and `- prescription:` with its settings beneath.
 */
function entryName(entry) {
	const coded = entry.head.match(/^code:\s*(.+)$/);
	if (coded) return value(entry.lines, 'name') || value(entry.lines, 'label') || coded[1];
	const [first] = entry.head.split(/[:{]/);
	return (first || entry.head).trim();
}

const humanise = (text) => {
	const words = text.replace(/_/g, ' ').trim();
	return words.charAt(0).toUpperCase() + words.slice(1);
};

/** A lifecycle read as a path: `Pending → Active → Closed`. */
function stagePath(lines) {
	return entries(section(lines, 'states'))
		.map((e) => humanise(entryName(e)))
		.filter(Boolean)
		.join(' → ');
}

/** A reference list explicitly turned off stays in the spec, but not on screen. */
const isDisabled = (entry) => entry.lines.some((l) => /^enabled:\s*false\b/.test(l.text));

const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;

export default function journeyHighlights(spec) {
	if (!spec || !spec.trim()) return { title: '', summary: '', groups: [] };

	const doc = scan(spec);
	const roleBlock = section(doc, 'roles');
	const patient = section(doc, 'patient');
	const documents = section(doc, 'documents');
	const detail = section(doc, 'detail');
	const reports = section(doc, 'reports');

	const roles = mappingKeys(roleBlock);
	const masters = entries(section(doc, 'masters')).filter((m) => !isDisabled(m));
	const docTypes = entries(section(documents, 'types')).filter((d) => !isDisabled(d));
	const programs = entries(section(doc, 'programs'));

	const groups = [];
	const push = (key, label, items) => {
		if (items.length) groups.push({ key, label, items });
	};

	push(
		'roles',
		'Who uses it',
		roles.map((name) => ({
			name,
			detail: section(roleBlock, name).some((l) => /^sees_only:\s*own\b/.test(l.text))
				? 'sees only their own records'
				: '',
		}))
	);

	const tracked = [];
	if (patient.length) tracked.push({ name: 'Patients', detail: '' });
	programs.forEach((p) => {
		tracked.push({ name: entryName(p), detail: 'enrolment' });
		entries(section(p.lines, 'orders')).forEach((o) =>
			tracked.push({ name: entryName(o), detail: 'orders' })
		);
	});
	masters.forEach((m) => tracked.push({ name: humanise(entryName(m)), detail: 'reference list' }));
	push('entities', 'What it keeps track of', tracked);

	push(
		'screens',
		'Documents collected',
		docTypes.map((d) => ({ name: humanise(entryName(d)), detail: '' }))
	);

	const stages = [];
	const patientPath = stagePath(patient);
	if (patientPath) stages.push({ name: 'A patient', detail: patientPath });
	programs.forEach((p) => {
		const path = stagePath(section(p.lines, 'enrolment'));
		if (path) stages.push({ name: `${entryName(p)} enrolment`, detail: path });
	});
	push('stages', 'Stages', stages);

	const page = [];
	const features = members(value(detail, 'features'));
	if (features.length) page.push({ name: features.map(humanise).join(' · '), detail: '' });
	entries(section(detail, 'custom_tabs')).forEach((t) =>
		page.push({ name: value(t.lines, 'label') || humanise(entryName(t)), detail: 'built for you' })
	);
	push('branding', 'On a patient’s page', page);

	const also = [];
	const consent = section(patient, 'consent');
	if (consent.length) {
		const channels = members(value(section(consent, 'communication'), 'channels'));
		also.push({
			name: 'Consent',
			detail: channels.length ? `messages by ${channels.join(', ')}` : '',
		});
	}
	if (section(doc, 'adverse_events').length) {
		also.push({ name: 'Adverse events', detail: '' });
	}
	const reportItems = entries(section(reports, 'items'));
	if (reportItems.length) {
		also.push({
			name: plural(reportItems.length, 'report'),
			detail: reportItems.map((r) => value(r.lines, 'label') || entryName(r)).join(', '),
		});
	}
	entries(section(doc, 'extra_modules')).forEach((x) =>
		also.push({ name: value(x.lines, 'name') || humanise(entryName(x)), detail: 'built for you' })
	);
	push('automatic', 'Also included', also);

	const counts = [
		programs.length && plural(programs.length, 'program'),
		roles.length && plural(roles.length, 'role'),
		docTypes.length && plural(docTypes.length, 'document'),
	].filter(Boolean);

	return {
		title: value(doc, 'name') || value(doc, 'journey'),
		summary: counts.join(' · '),
		groups,
	};
}
