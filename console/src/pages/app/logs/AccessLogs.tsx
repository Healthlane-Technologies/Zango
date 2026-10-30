import { useMemo, useState } from 'react';
import { na, useAccessLogs, type AccessLog } from '@/api/logs';
import {
	Badge,
	EmptyState,
	FilterSelect,
	Pagination,
	SearchInput,
	Spinner,
	Toolbar,
	useDebounced,
} from '@/ui';
import { ANY_TIME, LogTable, RawJson, TimeRange, rangeFor, type LogColumn } from './shared';

const ATTEMPT_TYPE: Record<string, string> = {
	login: 'Sign-in',
	logout: 'Sign-out',
	switch_role: 'Role switch',
};

/** "Name (12)" without the id. */
const userName = (v: string) => na(v)?.replace(/\s*\(\d+\)$/, '') ?? null;

function AccessDetail({ log }: { log: AccessLog }) {
	const facts: Array<[string, string | null]> = [
		['User', na(log.user)],
		['Username', log.username],
		['Role', na(log.role)],
		['IP address', log.ip_address],
		['Session expired', na(log.session_expired_at)],
		['User agent', log.user_agent],
	];
	return (
		<div className="grid items-start gap-3 px-4 py-3 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]">
			<dl className="kv rounded-lg border border-border bg-panel p-3 text-[12.5px]">
				{facts.map(([label, value]) => (
					<div key={label} className="contents">
						<dt>{label}</dt>
						<dd className="[overflow-wrap:anywhere]" style={{ whiteSpace: 'normal' }}>
							{value ?? <span className="text-t4">—</span>}
						</dd>
					</div>
				))}
			</dl>
			<div className="min-w-0 rounded-lg border border-border bg-panel">
				<RawJson value={log} />
			</div>
		</div>
	);
}

export function AccessLogs({ appId }: { appId: string }) {
	const [page, setPage] = useState(1);
	const [pageSize, setPageSize] = useState(20);
	const [search, setSearch] = useState('');
	const [attemptType, setAttemptType] = useState('');
	const [result, setResult] = useState('');
	const [role, setRole] = useState('');
	const [range, setRange] = useState(ANY_TIME);
	const debounced = useDebounced(search.trim());

	const filters = useMemo(
		() => ({ page, pageSize, search: debounced, attemptType, result, role, range: rangeFor(range) }),
		[page, pageSize, debounced, attemptType, result, role, range],
	);
	const { data, isLoading, isFetching, error, refetch } = useAccessLogs(appId, filters);

	// Any filter change goes back to the first page.
	const filter =
		<V,>(set: (v: V) => void) =>
		(v: V) => {
			set(v);
			setPage(1);
		};
	const options = data?.dropdown_options;

	const columns: LogColumn<AccessLog>[] = [
		{ key: 'time', header: 'Time', className: 'mono text-t3', cell: (l) => na(l.attempt_time) ?? '—' },
		{
			key: 'result',
			header: 'Result',
			cell: (l) =>
				l.is_login_successful ? (
					<Badge tone="green" dot>
						Succeeded
					</Badge>
				) : (
					<Badge tone="red" dot>
						Failed
					</Badge>
				),
		},
		{
			key: 'type',
			header: 'Type',
			cell: (l) => (l.attempt_type ? (ATTEMPT_TYPE[l.attempt_type] ?? l.attempt_type) : '—'),
		},
		{
			key: 'user',
			header: 'User',
			cell: (l) => (
				<span className="text-t1">
					{userName(l.user) ?? <span className="text-t3">Unknown</span>}
					{l.username && <span className="ml-1.5 text-[11.5px] text-t4">{l.username}</span>}
				</span>
			),
		},
		{ key: 'role', header: 'Role', cell: (l) => na(l.role) ?? <span className="text-t4">—</span> },
		{ key: 'ip', header: 'IP address', className: 'mono', cell: (l) => l.ip_address ?? '—' },
	];
	const filtered = !!(debounced || attemptType || result || role || range.preset !== 'any');

	return (
		<>
			<Toolbar>
				<SearchInput
					value={search}
					onChange={filter(setSearch)}
					placeholder="Search user, IP or user agent"
				/>
				<FilterSelect
					label="Attempt type"
					allLabel="All types"
					value={attemptType}
					onChange={filter(setAttemptType)}
					options={options?.attempt_type}
				/>
				<FilterSelect
					label="Result"
					allLabel="Any result"
					value={result}
					onChange={filter(setResult)}
					options={options?.is_login_successful}
				/>
				<FilterSelect
					label="Role"
					allLabel="All roles"
					value={role}
					onChange={filter(setRole)}
					options={options?.role}
				/>
				<TimeRange value={range} onChange={filter(setRange)} />
				<span className="ml-auto flex items-center gap-2 text-[12px] text-t3">
					{isFetching && !isLoading && <Spinner />}
					{data && data.total_failed_attempts > 0 && (
						<span className="num text-red-t">
							{data.total_failed_attempts.toLocaleString()} failed
						</span>
					)}
				</span>
			</Toolbar>
			<LogTable
				columns={columns}
				rows={data?.access_logs.records}
				rowKey={(l) => l.id}
				detail={(l) => <AccessDetail log={l} />}
				loading={isLoading}
				error={error}
				onRetry={() => refetch()}
				empty={
					filtered ? (
						<EmptyState title="No sign-ins match">Try a different filter or time range.</EmptyState>
					) : (
						<EmptyState title="No sign-ins yet">Sign-in and role-switch attempts appear here.</EmptyState>
					)
				}
				footer={
					data && (
						<Pagination
							page={page}
							pageSize={pageSize}
							totalRecords={data.access_logs.total_records}
							totalPages={data.access_logs.total_pages}
							onPage={setPage}
							onPageSize={filter(setPageSize)}
							noun="attempts"
						/>
					)
				}
			/>
		</>
	);
}
