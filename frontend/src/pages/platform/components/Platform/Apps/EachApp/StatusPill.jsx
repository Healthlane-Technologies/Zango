/**
 * StatusPill — small colored badge for a tenant's operational status.
 *
 * `deployed` → sage/green (running normally)
 * `suspended` → amber (blocked, but reversible)
 * `staged`, `deleted`, everything else → slate (informational fallback)
 */
const VARIANTS = {
	deployed: {
		label: 'Active',
		bg: '#EFF7EE',
		border: 'rgba(90,164,91,0.28)',
		dot: '#5AA45B',
		text: '#36713A',
	},
	suspended: {
		label: 'Suspended',
		bg: '#FEF6E7',
		border: 'rgba(218,144,17,0.28)',
		dot: '#DA9011',
		text: '#8A5A07',
	},
	staged: {
		label: 'Staged',
		bg: '#F4F5F8',
		border: 'rgba(110,116,141,0.28)',
		dot: '#6E748D',
		text: '#3D4159',
	},
	deleted: {
		label: 'Deleted',
		bg: '#F4F5F8',
		border: 'rgba(110,116,141,0.28)',
		dot: '#6E748D',
		text: '#3D4159',
	},
};

export default function StatusPill({ status }) {
	const v = VARIANTS[status] || VARIANTS.staged;
	return (
		<span
			className="inline-flex items-center gap-[6px] rounded-full border px-[8px] py-[2px] font-lato text-[10px] font-bold uppercase leading-[14px] tracking-[0.06em]"
			style={{
				backgroundColor: v.bg,
				borderColor: v.border,
				color: v.text,
			}}
		>
			<span
				aria-hidden
				style={{
					display: 'inline-block',
					width: 6,
					height: 6,
					borderRadius: 999,
					backgroundColor: v.dot,
					boxShadow: `0 0 0 2px ${v.dot}22`,
				}}
			/>
			{v.label}
		</span>
	);
}
