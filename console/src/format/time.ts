const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });
const UNITS: Array<[Intl.RelativeTimeFormatUnit, number]> = [
	['year', 365 * 24 * 3600],
	['month', 30 * 24 * 3600],
	['week', 7 * 24 * 3600],
	['day', 24 * 3600],
	['hour', 3600],
	['minute', 60],
];

/** "3 hours ago", "yesterday". Returns "—" for missing or unparseable input. */
export function timeAgo(iso: string | null | undefined, now = Date.now()): string {
	if (!iso) return '—';
	const t = Date.parse(iso);
	if (Number.isNaN(t)) return '—';
	const seconds = Math.round((t - now) / 1000);
	for (const [unit, size] of UNITS) {
		if (Math.abs(seconds) >= size) return rtf.format(Math.round(seconds / size), unit);
	}
	return 'just now';
}

export function formatDateTime(iso: string | null | undefined): string {
	if (!iso) return '—';
	const d = new Date(iso);
	return Number.isNaN(d.getTime())
		? '—'
		: d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}
