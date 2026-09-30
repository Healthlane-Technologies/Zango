import { useState } from 'react';

import { useApiMutation } from '@/api/hooks';

import {
	RESERVED_ROLES,
	roleKeys,
	updateRole,
	useRoles,
	type Role,
	type RoleFilters,
} from '@/api/roles';

import { formatDateTime, timeAgo } from '@/format/time';

import {
	Badge,
	Button,
	ConfirmModal,
	EmptyState,
	RowMenu,
	SearchInput,
	Segmented,
	Table,
	Toolbar,
	useDebounced,
	type Column,
} from '@/ui';

import { RoleDrawer } from './RoleDrawer';

type Status = NonNullable<RoleFilters['active']>;

export function RolesTab({
	app,
	createOpen,
	setCreateOpen,
}: {
	app: string;
	createOpen: boolean;
	setCreateOpen: (o: boolean) => void;
}) {
	const [search, setSearch] = useState('');
	const [status, setStatus] = useState<Status>('all');
	const debounced = useDebounced(search.trim());
	const { data, isLoading, error, refetch } = useRoles(app, { search: debounced, active: status });
	const [editing, setEditing] = useState<Role | null>(null);
	const [toggling, setToggling] = useState<Role | null>(null);

	const toggleActive = useApiMutation({
		fn: (r: Role) => updateRole(app, r.id, { is_active: !r.is_active }),
		invalidate: [roleKeys.all(app)],
		success: (_, r) => `${r.name} ${r.is_active ? 'deactivated' : 'activated'}`,
		onSuccess: () => setToggling(null),
	});

	const roles = data?.roles.records;
	const columns: Column<Role>[] = [
		{
			key: 'name',
			header: 'Role',
			cell: (r) => (
				<div className="flex items-center gap-2">
					<span className="font-[550] text-t1">{r.name}</span>
					{RESERVED_ROLES.includes(r.name) && <Badge tone="gray">Built-in</Badge>}
				</div>
			),
		},
		{
			key: 'users',
			header: 'Active users',
			cell: (r) => <span className="num">{r.users_count}</span>,
		},
		{
			key: 'policies',
			header: 'Policies',
			cell: (r) => (
				<span className="text-t3" title={r.attached_policies.map((p) => p.name).join(', ')}>
					{r.policies_count.total} {r.policies_count.total === 1 ? 'policy' : 'policies'}
				</span>
			),
		},
		{
			key: 'mfa',
			header: '2FA',
			cell: (r) =>
				r.auth_config?.two_factor_auth?.required ? (
					<span className="text-t3">Required</span>
				) : (
					<span className="text-t4">Off</span>
				),
		},
		{
			key: 'status',
			header: 'Status',
			cell: (r) =>
				r.is_active ? (
					<Badge tone="green" dot>
						Active
					</Badge>
				) : (
					<Badge tone="gray">Inactive</Badge>
				),
		},
		{
			key: 'updated',
			header: 'Updated',
			cell: (r) => <span title={formatDateTime(r.modified_at)}>{timeAgo(r.modified_at)}</span>,
		},
		{
			key: 'actions',
			header: '',
			align: 'right',
			cell: (r) => (
				<RowMenu
					label={`Actions for ${r.name}`}
					items={[
						{ label: 'Edit', icon: 'cog', onSelect: () => setEditing(r) },
						...(RESERVED_ROLES.includes(r.name)
							? []
							: [
									null,
									r.is_active
										? {
												label: 'Deactivate',
												icon: 'x' as const,
												danger: true,
												onSelect: () => setToggling(r),
											}
										: { label: 'Activate', icon: 'check' as const, onSelect: () => setToggling(r) },
								]),
					]}
				/>
			),
		},
	];

	return (
		<>
			<Toolbar>
				<SearchInput value={search} onChange={setSearch} placeholder="Search roles" />
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
			</Toolbar>
			<Table
				columns={columns}
				rows={roles}
				rowKey={(r) => r.id}
				loading={isLoading}
				error={error}
				onRetry={() => refetch()}
				onRowClick={setEditing}
				empty={
					debounced || status !== 'all' ? (
						<EmptyState title="No roles match">Try another search or filter.</EmptyState>
					) : (
						<EmptyState
							title="No roles yet"
							action={
								<Button size="sm" icon="plus" onClick={() => setCreateOpen(true)}>
									New role
								</Button>
							}
						/>
					)
				}
			/>
			<RoleDrawer
				app={app}
				open={createOpen || !!editing}
				onOpenChange={(o) => {
					if (!o) {
						setCreateOpen(false);
						setEditing(null);
					}
				}}
				role={editing}
				policies={data?.dropdown_options.policies ?? []}
			/>
			<ConfirmModal
				open={!!toggling}
				onOpenChange={(o) => !o && setToggling(null)}
				title={
					toggling?.is_active ? `Deactivate ${toggling?.name}?` : `Activate ${toggling?.name}?`
				}
				confirmLabel={toggling?.is_active ? 'Deactivate' : 'Activate'}
				danger={toggling?.is_active}
				loading={toggleActive.isPending}
				onConfirm={() => toggling && toggleActive.mutate(toggling)}
			>
				{toggling?.is_active
					? `Users with this role lose its permissions while it is inactive.`
					: `Users with this role get its permissions again.`}
			</ConfirmModal>
		</>
	);
}
