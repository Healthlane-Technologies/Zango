/**
 * Read a requirement spec as highlights rather than as a document.
 *
 * The spec is written for a business user to approve, but it is still a page
 * of prose — and while a build is running nobody wants to re-read it. What
 * they want is the shape of what they are getting: how many things it tracks,
 * who uses it, what screens exist, what was deliberately left out.
 *
 * Headings are matched by keyword, not by exact text. The spec is model
 * output against a template, so "Screens" may come back as "Screens and
 * pages" — a parser that demanded the template exactly would show an empty
 * panel for a perfectly good spec.
 */

const GROUPS = [
	{ key: 'entities', label: 'What it keeps track of', match: /keeps? track|entit|data/i },
	{ key: 'roles', label: 'Who uses it', match: /\brole|who uses/i },
	{ key: 'stages', label: 'Stages', match: /\bstage|workflow|lifecycle/i },
	{ key: 'screens', label: 'Screens', match: /\bscreen|\bpage/i },
	{ key: 'automatic', label: 'Automatic actions', match: /automatic|background|scheduled/i },
	{ key: 'branding', label: 'Branding', match: /brand/i },
	{ key: 'excluded', label: 'Not in this version', match: /not in this version|out of scope/i },
	{ key: 'assumptions', label: 'Assumptions', match: /assumption/i },
];

// "What this does" is the summary, not a group — it is rendered as the lead
// paragraph, so it must not also appear as a bullet list.
const SUMMARY = /what this does|summary|purpose/i;

/** `- **Name** — detail` or `- Name — detail` or `- Plain line`. */
function parseItem(line) {
	const text = line.replace(/^[-*]\s+/, '').trim();
	const bold = text.match(/^\*\*(.+?)\*\*\s*[—–:-]?\s*(.*)$/);
	if (bold) return { name: bold[1].trim(), detail: bold[2].trim() };

	const dashed = text.match(/^(.{2,60}?)\s+[—–]\s+(.*)$/);
	if (dashed) return { name: dashed[1].trim(), detail: dashed[2].trim() };

	return { name: text, detail: '' };
}

function stripMarkdown(text) {
	return text.replace(/\*\*(.+?)\*\*/g, '$1').replace(/`(.+?)`/g, '$1').trim();
}

export default function specHighlights(spec) {
	const empty = { title: '', summary: '', groups: [] };
	if (!spec || !spec.trim()) return empty;

	const sections = [];
	let current = null;
	let title = '';

	spec.split('\n').forEach((raw) => {
		const line = raw.trim();
		const heading = line.match(/^(#{1,6})\s+(.*)$/);
		if (heading) {
			const level = heading[1].length;
			const text = stripMarkdown(heading[2]);
			// The first and shallowest heading names the app.
			if (level <= 2 && !title) {
				title = text;
				current = null;
				return;
			}
			current = { heading: text, lines: [] };
			sections.push(current);
			return;
		}
		if (current && line) current.lines.push(line);
		else if (!current && line && !title) title = stripMarkdown(line);
	});

	const summarySection = sections.find((s) => SUMMARY.test(s.heading));
	const summary = summarySection
		? stripMarkdown(summarySection.lines.filter((l) => !/^[-*]\s/.test(l)).join(' '))
		: '';

	const groups = [];
	GROUPS.forEach((group) => {
		// First match wins, and a section already claimed as the summary is
		// never re-used — otherwise "What this does" would also match /data/.
		const section = sections.find(
			(s) => s !== summarySection && !s.claimed && group.match.test(s.heading)
		);
		if (!section) return;
		section.claimed = true;

		const items = section.lines
			.filter((l) => /^[-*]\s/.test(l))
			.map(parseItem)
			.filter((i) => i.name);

		// A section with prose but no bullets still says something worth
		// showing — "None in this version" is a real answer.
		if (!items.length) {
			const prose = stripMarkdown(section.lines.join(' '));
			if (!prose) return;
			groups.push({ ...group, label: section.heading || group.label, items: [{ name: prose, detail: '' }] });
			return;
		}
		groups.push({ ...group, label: section.heading || group.label, items });
	});

	return { title, summary, groups };
}
