import { useMemo, useState } from 'react';
import { useAuditLogs, type AuditChanges, type AuditLog, type AuditModelType } from '@/api/logs';
import {
	Badge,
	EmptyState,
	FilterSelect,
	Pagination,
	SearchInput,
	Spinner,
	Toolbar,
	useDebounced,
	type Tone,
} from '@/ui';
import { ANY_TIME, LogTable, RawJson, TimeRange, rangeFor, type LogColumn } from './shared';

interface FieldChange {
	field: string;
	before: string | null;
	after: string | null;
}

// The server stringifies values, so a missing one arrives as one of these.
const EMPTY = new Set(['None', 'null', '']);

const shown = (v: unknown): string | null => {
	if (v === null || v === undefined) return null;
	const s = typeof v === 'string' ? v : JSON.stringify(v);
	return EMPTY.has(s) ? null : s;
};

function fieldChanges(changes: AuditChanges | null): FieldChange[] {
	if (!changes || typeof changes !== 'object') return [];
	return Object.entries(changes).map(([field, change]) => {
		if (Array.isArray(change)) return { field, before: shown(change[0]), after: shown(change[1]) };
		if (change && typeof change === 'object' && (change as { type?: string }).type === 'm2m') {
			const m2m = change as { objects?: string[]; operation?: string };
			const objects = (m2m.objects ?? []).join(', ');
			return m2m.operation === 'delete' || m2m.operation === 'remove'
				? { field, before: objects, after: null }
				: { field, before: null, after: objects };
		}
		return { field, before: null, after: shown(change) };
	});
}

/** One line for the table: a count for creates and deletes, the fields (and short new values) for updates. */
function summary(changes: AuditChanges | null, action: string): string {
	const rows = fieldChanges(changes);
	if (!rows.length) return '—';
	if (action === 'Create' || action === 'Delete')
		return `${rows.length} field${rows.length === 1 ? '' : 's'}`;
	return rows
		.map((r) =>
			r.after !== null && r.after.length <= 24 && !r.after.includes('\n')
				? `${r.field} → ${r.after}`
				: r.field,
		)
		.join(', ');
}

const ACTION_TONE: Record<string, Tone> = { Create: 'green', Update: 'accent', Delete: 'red' };

const ACTOR_TYPE: Record<string, string> = {
	tenant_actor: 'App user',
	platform_actor: 'Platform user',
};

function AuditDetail({ log }: { log: AuditLog }) {
	const rows = fieldChanges(log.changes);
	return (
		<div className="grid items-start gap-3 px-4 py-3 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]">
			<div className="min-w-0 overflow-hidden rounded-lg border border-border bg-panel">
				{rows.length ? (
					<table className="w-full table-fixed border-collapse text-[12px]">
						<colgroup>
							<col style={{ width: '28%' }} />
							<col style={{ width: '36%' }} />
							<col style={{ width: '36%' }} />
						</colgroup>
						<thead>
							<tr className="bg-bg text-left text-t3">
								<th className="!h-[30px] !px-2.5 font-medium">Field</th>
								<th className="!h-[30px] !px-2.5 font-medium">Before</th>
								<th className="!h-[30px] !px-2.5 font-medium">After</th>
							</tr>
						</thead>
						<tbody>
							{rows.map((r) => (
								<tr key={r.field} className="border-t border-border-soft align-top">
									<td className="mono !h-auto !px-2.5 !py-1.5 !align-top !text-t1">{r.field}</td>
									<td className="mono !h-auto !whitespace-pre-wrap [overflow-wrap:anywhere] !px-2.5 !py-1.5 !align-top !text-red-t">
										{r.before ?? <span className="text-t4">—</span>}
									</td>
									<td className="mono !h-auto !whitespace-pre-wrap [overflow-wrap:anywhere] !px-2.5 !py-1.5 !align-top !text-green-t">
										{r.after ?? <span className="text-t4">—</span>}
									</td>
								</tr>
							))}
						</tbody>
					</table>
				) : (
					<p className="px-3 py-2.5 text-t3">No field changes recorded.</p>
				)}
			</div>
			<div className="min-w-0 rounded-lg border border-border bg-panel">
				<RawJson value={log} />
			</div>
		</div>
	);
}

export function AuditLogs({ appId, modelType }: { appId: string; modelType: AuditModelType }) {
	const [page, setPage] = useState(1);
	const [pageSize, setPageSize] = useState(20);
	const [search, setSearch] = useState('');
	const [action, setAction] = useState('');
	const [objectType, setObjectType] = useState('');
	const [range, setRange] = useState(ANY_TIME);
	const debounced = useDebounced(search.trim());

	const filters = useMemo(
		() => ({ page, pageSize, search: debounced, modelType, action, objectType, range: rangeFor(range) }),
		[page, pageSize, debounced, modelType, action, objectType, range],
	);
	const { data, isLoading, isFetching, error, refetch } = useAuditLogs(appId, filters);

	// Any filter change goes back to the first page.
	const filter =
		<V,>(set: (v: V) => void) =>
		(v: V) => {
			set(v);
			setPage(1);
		};

	const columns: LogColumn<AuditLog>[] = [
		{ key: 'time', header: 'Time', className: 'mono text-t3', cell: (l) => l.timestamp },
		{
			key: 'action',
			header: 'Action',
			cell: (l) => (
				<Badge tone={ACTION_TONE[l.action] ?? 'gray'} dot>
					{l.action}
				</Badge>
			),
		},
		{
			key: 'object',
			header: 'Object',
			cell: (l) => (
				<span className="mono block max-w-[200px] truncate text-t1" title={l.object_type}>
					{l.object_type}
					{l.object_id != null && <span className="text-t3"> #{l.object_id}</span>}
				</span>
			),
		},
		{
			key: 'changes',
			header: 'Changes',
			cell: (l) => (
				<span className="block max-w-[280px] truncate text-t1" title={summary(l.changes, l.action)}>
					{summary(l.changes, l.action)}
				</span>
			),
		},
		{
			key: 'actor',
			header: 'Actor',
			cell: (l) => (
				<span
					className="block max-w-[180px] truncate text-t2"
					title={`${l.actor ?? 'System'}${l.actor_type ? ` · ${ACTOR_TYPE[l.actor_type] ?? l.actor_type}` : ''}`}
				>
					{l.actor ?? 'System'}
					{l.actor_type && (
						<span className="ml-1.5 text-[11.5px] text-t4">
							{ACTOR_TYPE[l.actor_type] ?? l.actor_type}
						</span>
					)}
				</span>
			),
		},
	];
	const stats = data?.total_stats;
	const filtered = !!(debounced || action || objectType || range.preset !== 'any');

	return (
		<>
			<Toolbar>
				<SearchInput
					value={search}
					onChange={filter(setSearch)}
					placeholder="Search actor, object or changes"
				/>
				<FilterSelect
					label="Action"
					allLabel="All actions"
					value={action}
					onChange={filter(setAction)}
					options={data?.dropdown_options?.action}
				/>
				<FilterSelect
					label="Object type"
					allLabel="All objects"
					value={objectType}
					onChange={filter(setObjectType)}
					options={data?.dropdown_options?.object_type}
				/>
				<TimeRange value={range} onChange={filter(setRange)} />
				<span className="ml-auto flex items-center gap-2 text-[12px] text-t3">
					{isFetching && !isLoading && <Spinner />}
					{stats && (
						<span className="num">
							{stats.total_created.toLocaleString()} created ·{' '}
							{stats.total_updated.toLocaleString()} updated ·{' '}
							{stats.total_deleted.toLocaleString()} deleted
						</span>
					)}
				</span>
			</Toolbar>
			<LogTable
				columns={columns}
				rows={data?.audit_logs.records}
				rowKey={(l) => l.id}
				detail={(l) => <AuditDetail log={l} />}
				loading={isLoading}
				error={error}
				onRetry={() => refetch()}
				empty={
					filtered ? (
						<EmptyState title="No events match">Try a different filter or time range.</EmptyState>
					) : (
						<EmptyState title="No audit events yet">
							Changes to records appear here as they happen.
						</EmptyState>
					)
				}
				footer={
					data && (
						<Pagination
							page={page}
							pageSize={pageSize}
							totalRecords={data.audit_logs.total_records}
							totalPages={data.audit_logs.total_pages}
							onPage={setPage}
							onPageSize={filter(setPageSize)}
							noun="events"
						/>
					)
				}
			/>
		</>
	);
}
