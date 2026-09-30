import { cx } from './cx';

const PALETTE = ['#4F46E5', '#0F766E', '#B45309', '#A21CAF', '#1D4ED8', '#BE185D'];
// Soft background / strong foreground pairs for app tiles, from the prototype's vertical colours.
const TILE: Array<[string, string]> = [
	['#EEF2FF', '#4338CA'],
	['#F0FDFA', '#0F766E'],
	['#FEF2F2', '#B91C1C'],
	['#FDF4FF', '#A21CAF'],
	['#FFFBEB', '#B45309'],
	['#EFF6FF', '#1D4ED8'],
];

function hash(s: string): number {
	let h = 0;
	for (const c of s) h = (h * 31 + c.charCodeAt(0)) >>> 0;
	return h;
}

export function initials(name: string): string {
	const words = name.split(/[\s_—-]+/).filter((w) => /^[A-Za-z0-9]/.test(w));
	const picked = words.length > 1 ? words.slice(0, 2).map((w) => w[0]) : [name.slice(0, 2)];
	return picked.join('').toUpperCase();
}

export function Avatar({ name, small }: { name: string; small?: boolean }) {
	return (
		<span
			className={cx('av', small && 'sm')}
			style={{ background: PALETTE[hash(name) % PALETTE.length] }}
		>
			{initials(name)}
		</span>
	);
}

export function AppIcon({ name, size }: { name: string; size?: number }) {
	const [bg, fg] = TILE[hash(name) % TILE.length];
	const sized = size
		? { width: size, height: size, borderRadius: size / 4, fontSize: size / 2.9 }
		: {};
	return (
		<span className="appic" style={{ background: bg, color: fg, ...sized }}>
			{initials(name)}
		</span>
	);
}
