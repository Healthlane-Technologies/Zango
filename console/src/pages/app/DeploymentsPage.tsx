import { useMemo, useState } from 'react';

import { useAppId } from '@/api/hooks';

import { useReleases, type Release } from '@/api/releases';

import {
	Badge,
	EmptyState,
	FilterSelect,
	Page,
	PageHeader,
	Pagination,
	SearchInput,
	Spinner,
	Table,
	Toolbar,
	useDebounced,
	type Column,
	type Tone,
} from '@/ui';

const STATUS: Record<string, [Tone, string]> = {
	released: ['green', 'Released'],
	failed: ['red', 'Failed'],
	in_progress: ['amber', 'In progress'],
	initiated: ['gray', 'Initiated'],
	archived: ['line', 'Archived'],
};

function ReleaseStatus({ status }: { status: string }) {
	const [tone, label] = STATUS[status] ?? ['gray', status];
	return (
		<Badge tone={tone} dot busy={status === 'in_progress'}>
			{label}
		</Badge>
	);
}

const PAGE_SIZE = 20;

export function DeploymentsPage() {
	const appId = useAppId();
	const [page, setPage] = useState(1);
	const [q, setQ] = useState('');
	const [status, setStatus] = useState('');
	const [version, setVersion] = useState('');
	const search = useDebounced(q.trim());

	const filters = useMemo(
		() => ({ page, pageSize: PAGE_SIZE, search, status, version }),
		[page, search, status, version],
	);
	const { data, isLoading, isFetching, error, refetch } = useReleases(appId, filters);
	const reset = (set: (v: string) => void) => (v: string) => {
		set(v);
		setPage(1);
	};
	const releases = data?.releases;
	const filtered = !!(search || status || version);

	const columns: Column<Release>[] = [
		{
			key: 'version',
			header: 'Version',
			cell: (r) => {
				const desc = r.description && r.description !== 'NA' ? r.description : null;
				return (
					<div className="nm">
						<div className="min-w-0">
							<b className="mono" style={{ fontSize: 12.5 }}>
								v{r.version}
							</b>
							{desc && <small className="max-w-[420px] truncate">{desc}</small>}
						</div>
					</div>
				);
			},
		},
		{ key: 'status', header: 'Status', cell: (r) => <ReleaseStatus status={r.status} /> },
		{
			key: 'commit',
			header: 'Commit',
			cell: (r) =>
				r.last_git_hash ? (
					<span className="mono" title={r.last_git_hash}>
						{r.last_git_hash.slice(0, 8)}
					</span>
				) : (
					<span className="text-t4">—</span>
				),
		},
		{
			key: 'created',
			header: 'Created',
			cell: (r) => <span className="text-t3">{r.created_at}</span>,
		},
	];

	return (
		<Page>
			<PageHeader title="Deployments" description="Every release of this app, newest first." />
			<Toolbar>
				<SearchInput value={q} onChange={reset(setQ)} placeholder="Search version or description" />
				<FilterSelect
					label="Status"
					allLabel="All statuses"
					value={status}
					onChange={reset(setStatus)}
					options={data?.dropdown_options?.status}
				/>
				<FilterSelect
					label="Version"
					allLabel="All versions"
					value={version}
					onChange={reset(setVersion)}
					options={data?.dropdown_options?.version}
				/>
				{isFetching && !isLoading && (
					<span className="ml-auto text-t3">
						<Spinner />
					</span>
				)}
			</Toolbar>
			<Table
				columns={columns}
				rows={releases?.records}
				rowKey={(r) => r.id}
				loading={isLoading}
				error={error}
				onRetry={() => refetch()}
				empty={
					filtered ? (
						<EmptyState title="No releases match">Try another search or filter.</EmptyState>
					) : (
						<EmptyState title="No releases yet">
							Releases appear here when the app is released with{' '}
							<span className="mono">zango release</span> or built by the agent.
						</EmptyState>
					)
				}
				footer={
					releases &&
					releases.total_records > 0 && (
						<Pagination
							page={page}
							pageSize={PAGE_SIZE}
							totalRecords={releases.total_records}
							totalPages={releases.total_pages}
							onPage={setPage}
							noun={releases.total_records === 1 ? 'release' : 'releases'}
						/>
					)
				}
			/>
		</Page>
	);
}
