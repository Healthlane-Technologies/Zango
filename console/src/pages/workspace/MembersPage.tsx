import { useEffect, useState } from 'react';
import { ApiError } from '@/api/client';
import { useMembers, type Member, type MemberStatus } from '@/api/members';
import { useMe } from '@/api/me';
import { formatDateTime, timeAgo } from '@/format/time';
import {
	Avatar,
	Badge,
	Button,
	EmptyState,
	Page,
	PageHeader,
	Pagination,
	RowMenu,
	SearchInput,
	Segmented,
	Table,
	Toolbar,
	useDebounced,
	type Column,
} from '@/ui';
import { MemberDrawer, ResetPasswordModal, StatusModal } from './members/MemberDialogs';

const PAGE_SIZE = 20;

type Dialog = { kind: 'add' } | { kind: 'edit' | 'reset' | 'status'; member: Member } | null;

function AppList({ apps }: { apps: Member['apps'] }) {
	if (apps.length === 0) return <span className="text-t4">—</span>;
	const first = apps.slice(0, 2).map((a) => a.name);
	return (
		<span className="block max-w-[260px] truncate" title={apps.map((a) => a.name).join(', ')}>
			{first.join(', ')}
			{apps.length > 2 && <span className="text-t3"> +{apps.length - 2}</span>}
		</span>
	);
}

export function MembersPage() {
	const { data: me } = useMe();
	const [search, setSearch] = useState('');
	const [status, setStatus] = useState<MemberStatus>('all');
	const [page, setPage] = useState(1);
	const [dialog, setDialog] = useState<Dialog>(null);
	const debounced = useDebounced(search.trim());

	useEffect(() => setPage(1), [debounced, status]);

	const { data, isLoading, isFetching, error, refetch } = useMembers({
		page,
		pageSize: PAGE_SIZE,
		search: debounced,
		status,
	});
	const list = data?.platform_users;
	const appOptions = data?.dropdown_options?.apps ?? [];
	const forbidden = error instanceof ApiError && error.status === 403;

	const columns: Column<Member>[] = [
		{
			key: 'name',
			header: 'Name',
			cell: (m) => (
				<div className="nm">
					<Avatar name={m.name || m.email} />
					<div className="min-w-0">
						<b>
							{m.name || '—'}
							{m.id === me?.id && <span className="ml-1.5 font-normal text-t3">(you)</span>}
						</b>
						<small>{m.email}</small>
					</div>
				</div>
			),
		},
		{
			key: 'role',
			header: 'Role',
			cell: (m) =>
				m.is_superadmin ? (
					<Badge tone="accent">Super admin</Badge>
				) : (
					<Badge tone="line">Member</Badge>
				),
		},
		{
			key: 'apps',
			header: 'Apps',
			cell: (m) =>
				m.is_superadmin ? <span className="text-t3">All apps</span> : <AppList apps={m.apps} />,
		},
		{
			key: 'status',
			header: 'Status',
			cell: (m) => (
				<Badge tone={m.is_active ? 'green' : 'gray'} dot>
					{m.is_active ? 'Active' : 'Inactive'}
				</Badge>
			),
		},
		{
			key: 'login',
			header: 'Last sign-in',
			cell: (m) => (
				<span title={formatDateTime(m.last_login)}>
					{m.last_login ? timeAgo(m.last_login) : 'Never'}
				</span>
			),
		},
		{
			key: 'joined',
			header: 'Added',
			cell: (m) => <span title={formatDateTime(m.created_at)}>{timeAgo(m.created_at)}</span>,
		},
		{
			key: 'actions',
			header: '',
			align: 'right',
			cell: (m) => (
				// The menu renders in a portal, but React still bubbles its clicks through the
				// component tree to the row; stop them here so a menu choice doesn't also open Edit.
				<RowMenu
					label={`Actions for ${m.name || m.email}`}
					items={[
						{
							label: 'Edit details',
							icon: 'cog',
							onSelect: () => setDialog({ kind: 'edit', member: m }),
						},
						{
							label: 'Reset password',
							icon: 'key',
							onSelect: () => setDialog({ kind: 'reset', member: m }),
						},
						// You can't deactivate yourself.
						...(m.id === me?.id
							? []
							: [
									null,
									m.is_active
										? {
												label: 'Deactivate',
												icon: 'lock' as const,
												danger: true,
												onSelect: () => setDialog({ kind: 'status', member: m }),
											}
										: {
												label: 'Activate',
												icon: 'check' as const,
												onSelect: () => setDialog({ kind: 'status', member: m }),
											},
								]),
					]}
				/>
			),
		},
	];

	return (
		<Page>
			<PageHeader
				title="Members"
				description="People who can sign in to this platform, and the apps they can manage."
				actions={
					!forbidden && (
						<Button
							variant="primary"
							icon="plus"
							onClick={() => setDialog({ kind: 'add' })}
							disabled={!data}
						>
							Add member
						</Button>
					)
				}
			/>
			{forbidden ? (
				<div className="card">
					<EmptyState title="Only super admins can manage members">
						Ask a super admin to add people or change their access.
					</EmptyState>
				</div>
			) : (
				<>
					<Toolbar>
						<SearchInput
							value={search}
							onChange={setSearch}
							placeholder="Search by name, email or app"
						/>
						<Segmented
							label="Filter by status"
							value={status}
							onChange={setStatus}
							options={[
								{ value: 'all', label: 'All' },
								{ value: 'active', label: 'Active' },
								{ value: 'inactive', label: 'Inactive' },
							]}
						/>
						{isFetching && !isLoading && <span className="spin text-t4" aria-label="Refreshing" />}
					</Toolbar>
					<Table
						columns={columns}
						rows={list?.records}
						rowKey={(m) => m.id}
						loading={isLoading}
						error={error}
						onRetry={() => refetch()}
						onRowClick={(m) => setDialog({ kind: 'edit', member: m })}
						empty={
							debounced || status !== 'all' ? (
								<EmptyState title="No members match">Try another search or filter.</EmptyState>
							) : (
								<EmptyState title="No members yet" />
							)
						}
						footer={
							list && list.total_records > 0 ? (
								<Pagination
									page={page}
									pageSize={PAGE_SIZE}
									totalRecords={list.total_records}
									totalPages={list.total_pages}
									onPage={setPage}
									noun="members"
								/>
							) : undefined
						}
					/>
				</>
			)}
			{(dialog?.kind === 'add' || dialog?.kind === 'edit') && (
				<MemberDrawer
					key={dialog.kind === 'edit' ? dialog.member.id : 'new'}
					open
					onOpenChange={(o) => !o && setDialog(null)}
					member={dialog.kind === 'edit' ? dialog.member : undefined}
					appOptions={appOptions}
				/>
			)}
			{dialog?.kind === 'reset' && (
				<ResetPasswordModal member={dialog.member} onClose={() => setDialog(null)} />
			)}
			{dialog?.kind === 'status' && (
				<StatusModal member={dialog.member} onClose={() => setDialog(null)} />
			)}
		</Page>
	);
}
