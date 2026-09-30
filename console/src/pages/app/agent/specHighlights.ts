// Port of frontend/src/pages/appAgentMode/specHighlights.js: read a requirement spec as
// highlights rather than as a document. Headings are matched by keyword, not exact text,
// because the spec is model output against a template ("Screens" may come back as
// "Screens and pages").

export type GroupKey =
	| 'entities'
	| 'roles'
	| 'stages'
	| 'screens'
	| 'automatic'
	| 'branding'
	| 'excluded'
	| 'assumptions';

export interface HighlightItem {
	name: string;
	detail: string;
}

export interface HighlightGroup {
	key: GroupKey;
	label: string;
	items: HighlightItem[];
}

export interface SpecHighlights {
	title: string;
	summary: string;
	groups: HighlightGroup[];
}

const GROUPS: Array<{ key: GroupKey; label: string; match: RegExp }> = [
	{ key: 'entities', label: 'What it keeps track of', match: /keeps? track|entit|data/i },
	{ key: 'roles', label: 'Who uses it', match: /\brole|who uses/i },
	{ key: 'stages', label: 'Stages', match: /\bstage|workflow|lifecycle/i },
	{ key: 'screens', label: 'Screens', match: /\bscreen|\bpage/i },
	{ key: 'automatic', label: 'Automatic actions', match: /automatic|background|scheduled/i },
	{ key: 'branding', label: 'Branding', match: /brand/i },
	{ key: 'excluded', label: 'Not in this version', match: /not in this version|out of scope/i },
	{ key: 'assumptions', label: 'Assumptions', match: /assumption/i },
];

// "What this does" is the lead paragraph, not a group, so it must not also appear as bullets.
const SUMMARY = /what this does|summary|purpose/i;

/** `- **Name** — detail`, `- Name — detail` or `- Plain line`. */
function parseItem(line: string): HighlightItem {
	const text = line.replace(/^[-*]\s+/, '').trim();
	const bold = text.match(/^\*\*(.+?)\*\*\s*[—–:-]?\s*(.*)$/);
	if (bold) return { name: bold[1].trim(), detail: bold[2].trim() };
	const dashed = text.match(/^(.{2,60}?)\s+[—–]\s+(.*)$/);
	if (dashed) return { name: dashed[1].trim(), detail: dashed[2].trim() };
	return { name: text, detail: '' };
}

function stripMarkdown(text: string): string {
	return text
		.replace(/\*\*(.+?)\*\*/g, '$1')
		.replace(/`(.+?)`/g, '$1')
		.trim();
}

interface Section {
	heading: string;
	lines: string[];
	claimed?: boolean;
}

export function specHighlights(spec: string | null | undefined): SpecHighlights {
	if (!spec || !spec.trim()) return { title: '', summary: '', groups: [] };

	const sections: Section[] = [];
	let current: Section | null = null;
	let title = '';

	for (const raw of spec.split('\n')) {
		const line = raw.trim();
		const heading = line.match(/^(#{1,6})\s+(.*)$/);
		if (heading) {
			const level = heading[1].length;
			const text = stripMarkdown(heading[2]);
			// The first and shallowest heading names the app.
			if (level <= 2 && !title) {
				title = text;
				current = null;
				continue;
			}
			current = { heading: text, lines: [] };
			sections.push(current);
			continue;
		}
		if (current && line) current.lines.push(line);
		else if (!current && line && !title) title = stripMarkdown(line);
	}

	const summarySection = sections.find((s) => SUMMARY.test(s.heading));
	const summary = summarySection
		? stripMarkdown(summarySection.lines.filter((l) => !/^[-*]\s/.test(l)).join(' '))
		: '';

	const groups: HighlightGroup[] = [];
	for (const group of GROUPS) {
		// First match wins, and the summary section is never re-used (it would match /data/).
		const section = sections.find(
			(s) => s !== summarySection && !s.claimed && group.match.test(s.heading),
		);
		if (!section) continue;
		section.claimed = true;
		const items = section.lines
			.filter((l) => /^[-*]\s/.test(l))
			.map(parseItem)
			.filter((i) => i.name);
		if (!items.length) {
			// Prose without bullets still says something ("None in this version" is an answer).
			const prose = stripMarkdown(section.lines.join(' '));
			if (prose)
				groups.push({
					key: group.key,
					label: section.heading || group.label,
					items: [{ name: prose, detail: '' }],
				});
			continue;
		}
		groups.push({ key: group.key, label: section.heading || group.label, items });
	}
	return { title, summary, groups };
}
