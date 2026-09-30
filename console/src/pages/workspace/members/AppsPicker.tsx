import { useMemo, useState } from 'react';
import { AppIcon, Icon, cx } from '@/ui';

/**
 * Checkbox list of apps with a filter box. Local to Members; a candidate for a shared
 * multi-select in @/ui.
 */
export function AppsPicker({
	options,
	value,
	onChange,
	invalid,
	describedBy,
}: {
	options: Array<{ id: string; label: string }>;
	value: string[];
	onChange: (v: string[]) => void;
	invalid?: boolean;
	describedBy?: string;
}) {
	const [q, setQ] = useState('');
	const selected = useMemo(() => new Set(value), [value]);
	const shown = options.filter((o) => !q || o.label.toLowerCase().includes(q.toLowerCase()));
	const toggle = (id: string) =>
		onChange(selected.has(id) ? value.filter((v) => v !== id) : [...value, id]);

	return (
		<div
			className={cx(
				'overflow-hidden rounded-[7px] border bg-panel shadow-card',
				invalid ? 'border-red' : 'border-border',
			)}
			aria-describedby={describedBy}
		>
			<div className="flex items-center gap-2 border-b border-border-soft px-[10px] text-t4">
				<Icon name="search" />
				<input
					className="h-8 min-w-0 flex-1 bg-transparent text-t1 outline-none"
					placeholder="Filter apps"
					value={q}
					onChange={(e) => setQ(e.target.value)}
					aria-label="Filter apps"
				/>
				<span className="text-[12px] text-t3 num">{value.length} selected</span>
			</div>
			<div className="max-h-[220px] overflow-y-auto p-1" role="group" aria-label="Apps">
				{shown.length === 0 && <div className="px-2 py-3 text-center text-t3">No apps match</div>}
				{shown.map((o) => (
					<label
						key={o.id}
						className="flex h-9 cursor-pointer items-center gap-[10px] rounded-md px-2 hover:bg-hover"
					>
						<input
							type="checkbox"
							className="h-[14px] w-[14px] accent-[var(--accent)]"
							checked={selected.has(o.id)}
							onChange={() => toggle(o.id)}
						/>
						<AppIcon name={o.label} size={22} />
						<span className="truncate text-t1">{o.label}</span>
					</label>
				))}
			</div>
		</div>
	);
}
