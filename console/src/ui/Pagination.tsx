import { useEffect, useState } from 'react';
import { Button } from './Button';

const PAGE_SIZES = [20, 50, 100];

interface PaginationProps {
	/** 1-based. */
	page: number;
	pageSize: number;
	totalRecords: number;
	totalPages: number;
	onPage: (page: number) => void;
	onPageSize?: (size: number) => void;
	/** Noun for the count, e.g. "events". */
	noun?: string;
	/** Shown after the count, e.g. a refetch spinner. */
	busy?: boolean;
}

/** Contents for a Table `footer`: range, optional page size, previous/next. */
export function Pagination({
	page,
	pageSize,
	totalRecords,
	totalPages,
	onPage,
	onPageSize,
	noun = 'records',
	busy,
}: PaginationProps) {
	const from = totalRecords === 0 ? 0 : (page - 1) * pageSize + 1;
	const to = Math.min(page * pageSize, totalRecords);
	return (
		<>
			<span className="num">
				{from.toLocaleString()}–{to.toLocaleString()} of {totalRecords.toLocaleString()} {noun}
			</span>
			{busy && <span className="spin" aria-label="Loading" />}
			<div className="r items-center">
				{onPageSize && (
					<label className="mr-2 flex items-center gap-1.5">
						Rows
						<select
							className="select h-7 w-auto py-0 text-[12px]"
							value={pageSize}
							onChange={(e) => onPageSize(Number(e.target.value))}
						>
							{PAGE_SIZES.map((s) => (
								<option key={s} value={s}>
									{s}
								</option>
							))}
						</select>
					</label>
				)}
				<Button size="xs" disabled={page <= 1} onClick={() => onPage(page - 1)}>
					Previous
				</Button>
				<Button size="xs" disabled={page >= totalPages} onClick={() => onPage(page + 1)}>
					Next
				</Button>
			</div>
		</>
	);
}

const CLIENT_PAGE_SIZE = 25;

/**
 * Client-side paging over an already-filtered list. Resets to page 1 when `resetKey` changes.
 * `footer` is undefined when everything fits on one page.
 */
export function usePaged<T>(rows: T[], resetKey: unknown, pageSize = CLIENT_PAGE_SIZE) {
	const [page, setPage] = useState(1);
	useEffect(() => setPage(1), [resetKey]);
	const totalPages = Math.max(1, Math.ceil(rows.length / pageSize));
	const current = Math.min(page, totalPages);
	return {
		rows: rows.slice((current - 1) * pageSize, current * pageSize),
		footer:
			rows.length > pageSize ? (
				<Pagination
					page={current}
					pageSize={pageSize}
					totalRecords={rows.length}
					totalPages={totalPages}
					onPage={setPage}
				/>
			) : undefined,
	};
}
