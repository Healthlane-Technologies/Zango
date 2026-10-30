import { Fragment, useState, type ReactNode } from 'react';
import type { DateRange } from '@/api/logs';
import { cx, ErrorState, Icon, Skeleton } from '@/ui';

/* ---------- time range filter ---------- */

export type RangePreset = 'any' | 'today' | '7d' | '30d' | 'custom';

export interface RangeValue {
	preset: RangePreset;
	start: string;
	end: string;
}

export const ANY_TIME: RangeValue = { preset: 'any', start: '', end: '' };

const PRESETS: Array<[RangePreset, string]> = [
	['any', 'Any time'],
	['today', 'Today'],
	['7d', 'Last 7 days'],
	['30d', 'Last 30 days'],
	['custom', 'Custom range'],
];

const ymd = (d: Date) =>
	`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;

/** The date range a preset stands for (inclusive, local days), or null for no filter. */
export function rangeFor(value: RangeValue, now = new Date()): DateRange | null {
	const daysAgo = (n: number) => ymd(new Date(now.getFullYear(), now.getMonth(), now.getDate() - n));
	switch (value.preset) {
		case 'today':
			return { start: daysAgo(0), end: daysAgo(0) };
		case '7d':
			return { start: daysAgo(6), end: daysAgo(0) };
		case '30d':
			return { start: daysAgo(29), end: daysAgo(0) };
		case 'custom':
			if (!value.start || !value.end) return null;
			// Either order works: the earlier date is the start.
			return value.start <= value.end
				? { start: value.start, end: value.end }
				: { start: value.end, end: value.start };
		default:
			return null;
	}
}

export function TimeRange({
	value,
	onChange,
}: {
	value: RangeValue;
	onChange: (v: RangeValue) => void;
}) {
	return (
		<div className="flex items-center gap-1.5">
			<select
				className="select w-auto"
				aria-label="Time range"
				value={value.preset}
				onChange={(e) => onChange({ ...value, preset: e.target.value as RangePreset })}
			>
				{PRESETS.map(([v, label]) => (
					<option key={v} value={v}>
						{label}
					</option>
				))}
			</select>
			{value.preset === 'custom' && (
				<>
					<input
						type="date"
						className="input w-auto"
						aria-label="From"
						value={value.start}
						max={value.end || undefined}
						onChange={(e) => onChange({ ...value, start: e.target.value })}
					/>
					<span className="text-t4">–</span>
					<input
						type="date"
						className="input w-auto"
						aria-label="To"
						value={value.end}
						min={value.start || undefined}
						onChange={(e) => onChange({ ...value, end: e.target.value })}
					/>
				</>
			)}
		</div>
	);
}

/* ---------- expandable log table ---------- */

export interface LogColumn<T> {
	key: string;
	header: string;
	className?: string;
	cell: (row: T) => ReactNode;
}

/** A table whose rows open in place to show `detail(row)`; one row open at a time. */
export function LogTable<T>({
	columns,
	rows,
	rowKey,
	detail,
	loading,
	error,
	onRetry,
	empty,
	footer,
}: {
	columns: LogColumn<T>[];
	rows: T[] | undefined;
	rowKey: (row: T) => string | number;
	detail: (row: T) => ReactNode;
	loading: boolean;
	error: Error | null;
	onRetry: () => void;
	empty: ReactNode;
	footer?: ReactNode;
}) {
	const [open, setOpen] = useState<string | number | null>(null);
	if (error)
		return (
			<div className="card">
				<ErrorState error={error} onRetry={onRetry} />
			</div>
		);
	const span = columns.length + 1;
	return (
		<div className="card tbl-wrap">
			<table className="t">
				<thead>
					<tr>
						<th style={{ width: 28, paddingRight: 0 }} aria-label="Expand" />
						{columns.map((c) => (
							<th key={c.key} className={c.className}>
								{c.header}
							</th>
						))}
					</tr>
				</thead>
				<tbody>
					{loading &&
						Array.from({ length: 8 }, (_, i) => (
							<tr key={i}>
								<td style={{ height: 38 }} />
								{columns.map((c) => (
									<td key={c.key} style={{ height: 38 }}>
										<Skeleton width={`${45 + ((i * 13 + c.key.length * 7) % 45)}%`} />
									</td>
								))}
							</tr>
						))}
					{!loading &&
						rows?.map((row) => {
							const key = rowKey(row);
							const isOpen = open === key;
							const toggle = () => setOpen(isOpen ? null : key);
							return (
								<Fragment key={key}>
									<tr
										className="row"
										aria-expanded={isOpen}
										tabIndex={0}
										onClick={toggle}
										onKeyDown={(e) => {
											if (e.key === 'Enter' || e.key === ' ') {
												e.preventDefault();
												toggle();
											}
										}}
									>
										<td style={{ height: 38, paddingRight: 0 }} className="text-t4">
											<Icon
												name="back"
												size={13}
												style={{
													transform: isOpen ? 'rotate(-90deg)' : 'rotate(180deg)',
													transition: 'transform .12s',
												}}
											/>
										</td>
										{columns.map((c) => (
											<td key={c.key} style={{ height: 38 }} className={cx(c.className)}>
												{c.cell(row)}
											</td>
										))}
									</tr>
									{isOpen && (
										<tr>
											<td
												colSpan={span}
												style={{ height: 'auto', padding: 0, background: 'var(--bg)' }}
											>
												{detail(row)}
											</td>
										</tr>
									)}
								</Fragment>
							);
						})}
					{!loading && rows?.length === 0 && (
						<tr>
							<td colSpan={span} style={{ height: 'auto', padding: 0 }}>
								{empty}
							</td>
						</tr>
					)}
				</tbody>
			</table>
			{footer && <div className="tfoot">{footer}</div>}
		</div>
	);
}

/** The raw log entry, as the API returned it. */
export function RawJson({ value }: { value: unknown }) {
	return (
		<pre className="m-0 max-h-[420px] overflow-y-auto whitespace-pre-wrap px-4 py-3 font-mono text-[11.5px] leading-[1.7] text-t2 [overflow-wrap:anywhere]">
			{JSON.stringify(value, null, 2)}
		</pre>
	);
}
