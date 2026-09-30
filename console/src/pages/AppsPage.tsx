import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApps, type App } from '@/api/apps';
import { formatDateTime, timeAgo } from '@/format/time';
import { appPath } from '@/shell/nav';
import {
	AppIcon,
	Badge,
	ButtonLink,
	EmptyState,
	Page,
	PageHeader,
	RowMenu,
	SearchInput,
	Segmented,
	Table,
	TemplateBadge,
	Toolbar,
	type Column,
	type Tone,
} from '@/ui';

const STATUS: Record<string, [Tone, string]> = {
	deployed: ['green', 'Deployed'],
	staged: ['amber', 'Staged'],
	suspended: ['gray', 'Suspended'],
	deleted: ['red', 'Deleted'],
};

type Filter = 'all' | 'deployed' | 'staged';

export function StatusBadge({ status }: { status: string }) {
	const [tone, label] = STATUS[status] ?? ['gray', status];
	return (
		<Badge tone={tone} dot busy={status === 'staged'}>
			{label}
		</Badge>
	);
}

export function AppsPage() {
	const navigate = useNavigate();
	const { data: apps, isLoading, error, refetch } = useApps();
	const [q, setQ] = useState('');
	const [filter, setFilter] = useState<Filter>('all');

	const rows = useMemo(() => {
		const needle = q.trim().toLowerCase();
		return (apps ?? [])
			.filter((a) => filter === 'all' || a.status === filter)
			.filter(
				(a) =>
					!needle ||
					`${a.name} ${a.domain_url ?? ''} ${a.description ?? ''}`.toLowerCase().includes(needle),
			)
			.sort((a, b) => Date.parse(b.modified_at) - Date.parse(a.modified_at));
	}, [apps, q, filter]);

	const staged = apps?.find((a) => a.status === 'staged');

	const columns: Column<App>[] = [
		{
			key: 'name',
			header: 'Name',
			cell: (a) => (
				<div className="nm">
					<AppIcon name={a.name} />
					<div className="min-w-0">
						<b>{a.name}</b>
						{a.description && <small className="max-w-[360px] truncate">{a.description}</small>}
					</div>
				</div>
			),
		},
		{ key: 'status', header: 'Status', cell: (a) => <StatusBadge status={a.status} /> },
		{
			key: 'domain',
			header: 'Domain',
			cell: (a) => <span className="mono">{a.domain_url ?? '—'}</span>,
		},
		{
			key: 'template',
			header: 'Template',
			cell: (a) =>
				a.template ? <TemplateBadge template={a.template} /> : <span className="text-t4">—</span>,
		},
		{
			key: 'release',
			header: 'Release',
			cell: (a) => <span className="mono">{a.last_released_version ?? '—'}</span>,
		},
		{
			key: 'updated',
			header: 'Updated',
			cell: (a) => <span title={formatDateTime(a.modified_at)}>{timeAgo(a.modified_at)}</span>,
		},
		{
			key: 'actions',
			header: '',
			align: 'right',
			cell: (a) => (
				<RowMenu
					label={`Actions for ${a.name}`}
					items={[
						{ label: 'Open', icon: 'home', onSelect: () => navigate(appPath(a.uuid)) },
						...(a.domain_url
							? [
									{
										label: 'Visit app',
										icon: 'ext' as const,
										onSelect: () => window.open(`//${a.domain_url}`, '_blank', 'noopener'),
									},
								]
							: []),
						null,
						{
							label: 'Open in classic view',
							icon: 'back',
							onSelect: () => window.location.assign(`/platform/apps/${a.uuid}/dashboard`),
						},
					]}
				/>
			),
		},
	];

	return (
		<Page>
			<PageHeader
				title="Apps"
				description="Each app runs as an isolated tenant on Zango."
				actions={
					<ButtonLink to="/apps/new" variant="primary" icon="plus">
						New app
					</ButtonLink>
				}
			/>
			{staged && (
				<div className="banner">
					<span className="spin text-amber" />
					<span>
						<b>{staged.name}</b> is being set up
					</span>
				</div>
			)}
			<Toolbar>
				<SearchInput value={q} onChange={setQ} placeholder="Search apps" />
				<Segmented
					label="Filter by status"
					value={filter}
					onChange={setFilter}
					options={[
						{ value: 'all', label: 'All' },
						{ value: 'deployed', label: 'Deployed' },
						{ value: 'staged', label: 'Staged' },
					]}
				/>
				{apps && (
					<span className="ml-auto text-[12px] text-t3 num">
						{rows.length} of {apps.length}
					</span>
				)}
			</Toolbar>
			<Table
				columns={columns}
				rows={rows}
				rowKey={(a) => a.uuid}
				loading={isLoading}
				error={error}
				onRetry={() => refetch()}
				onRowClick={(a) => navigate(appPath(a.uuid))}
				empty={
					apps?.length ? (
						<EmptyState title="No apps match">Try another search or filter.</EmptyState>
					) : (
						<EmptyState title="No apps yet">Create your first app to get started.</EmptyState>
					)
				}
			/>
		</Page>
	);
}
