import type { ReactNode } from 'react';
import { cx } from './cx';
import { EmptyState, ErrorState, Skeleton } from './Feedback';

export interface Column<T> {
	key: string;
	header: ReactNode;
	cell: (row: T) => ReactNode;
	/** Right-aligned, narrow column (row actions). */
	align?: 'right';
	className?: string;
}

interface TableProps<T> {
	columns: Column<T>[];
	rows: T[] | undefined;
	rowKey: (row: T) => string | number;
	loading?: boolean;
	error?: Error | null;
	onRetry?: () => void;
	onRowClick?: (row: T) => void;
	empty?: ReactNode;
	footer?: ReactNode;
}

const SKELETON_ROWS = 5;

/** Card-wrapped data table in the prototype's `.t` style. */
export function Table<T>({
	columns,
	rows,
	rowKey,
	loading,
	error,
	onRetry,
	onRowClick,
	empty,
	footer,
}: TableProps<T>) {
	if (error) {
		return (
			<div className="card">
				<ErrorState error={error} onRetry={onRetry} />
			</div>
		);
	}
	const showEmpty = !loading && rows && rows.length === 0;
	return (
		<div className="card tbl-wrap">
			<table className="t">
				<thead>
					<tr>
						{columns.map((c) => (
							<th key={c.key} className={cx(c.align === 'right' && 'ra', c.className)}>
								{c.header}
							</th>
						))}
					</tr>
				</thead>
				<tbody>
					{loading &&
						Array.from({ length: SKELETON_ROWS }, (_, i) => (
							<tr key={i}>
								{columns.map((c) => (
									<td key={c.key}>
										<Skeleton width={c.align === 'right' ? 16 : `${50 + ((i * 17) % 40)}%`} />
									</td>
								))}
							</tr>
						))}
					{!loading &&
						rows?.map((row) => (
							<tr
								key={rowKey(row)}
								className={cx(onRowClick && 'row')}
								onClick={onRowClick ? () => onRowClick(row) : undefined}
							>
								{columns.map((c) => (
									<td key={c.key} className={cx(c.align === 'right' && 'ra', c.className)}>
										{c.cell(row)}
									</td>
								))}
							</tr>
						))}
				</tbody>
			</table>
			{showEmpty && (empty ?? <EmptyState title="Nothing here yet" />)}
			{footer && <div className="tfoot">{footer}</div>}
		</div>
	);
}
