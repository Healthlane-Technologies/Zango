import { useState } from 'react';

import { useApiMutation } from '@/api/hooks';

import { updateUser, userKeys, useUsers, type AppUser, type UserFilters } from '@/api/users';

import {
	Avatar,
	Badge,
	Button,
	ConfirmModal,
	EmptyState,
	Field,
	Input,
	Modal,
	Pagination,
	RowMenu,
	SearchInput,
	Segmented,
	Select,
	Table,
	Toolbar,
	useDebounced,
	type Column,
} from '@/ui';

import { UserDrawer } from './UserDrawer';

const PAGE_SIZE = 20;

type Status = NonNullable<UserFilters['active']>;

function ResetPasswordModal({
	app,
	user,
	onClose,
}: {
	app: string;
	user: AppUser | null;
	onClose: () => void;
}) {
	const [password, setPassword] = useState('');
	const [error, setError] = useState<string>();
	const mutation = useApiMutation({
		fn: (pw: string) => updateUser(app, user!.id, { password: pw }),
		invalidate: [userKeys.all(app)],
		success: 'Password updated',
		onSuccess: onClose,
	});
	return (
		<Modal
			open={!!user}
			onOpenChange={(o) => {
				if (!o) {
					setPassword('');
					setError(undefined);
					onClose();
				}
			}}
			title="Reset password"
			subtitle={user ? `Set a new password for ${user.name}.` : undefined}
			footer={
				<>
					<Button onClick={onClose}>Cancel</Button>
					<Button
						variant="primary"
						loading={mutation.isPending}
						onClick={() =>
							password ? mutation.mutate(password) : setError('Enter a new password')
						}
					>
						Set password
					</Button>
				</>
			}
		>
			<Field label="New password" error={error} hint="Must meet the app's password policy.">
				{(p) => (
					<Input
						{...p}
						type="password"
						autoComplete="new-password"
						autoFocus
						value={password}
						onChange={(e) => setPassword(e.target.value)}
					/>
				)}
			</Field>
		</Modal>
	);
}

export function UsersTab({
	app,
	inviteOpen,
	setInviteOpen,
}: {
	app: string;
	inviteOpen: boolean;
	setInviteOpen: (o: boolean) => void;
}) {
	const [search, setSearch] = useState('');
	const [status, setStatus] = useState<Status>('all');
	const [role, setRole] = useState('');
	const [page, setPage] = useState(1);
	const debounced = useDebounced(search.trim());
	const filters: UserFilters = {
		page,
		pageSize: PAGE_SIZE,
		search: debounced,
		active: status,
		role,
	};
	const { data, isLoading, isFetching, error, refetch } = useUsers(app, filters);

	const [editing, setEditing] = useState<AppUser | null>(null);
	const [resetting, setResetting] = useState<AppUser | null>(null);
	const [toggling, setToggling] = useState<AppUser | null>(null);

	const toggleActive = useApiMutation({
		fn: (u: AppUser) => updateUser(app, u.id, { is_active: !u.is_active }),
		invalidate: [userKeys.all(app)],
		success: (_, u) => `${u.name} ${u.is_active ? 'deactivated' : 'activated'}`,
		onSuccess: () => setToggling(null),
	});

	const resetPage =
		<T,>(fn: (v: T) => void) =>
		(v: T) => {
			fn(v);
			setPage(1);
		};

	const users = data?.users;
	const roleOptions = data?.dropdown_options.roles ?? [];
	const filtered = !!debounced || status !== 'all' || !!role;

	const columns: Column<AppUser>[] = [
		{
			key: 'name',
			header: 'Name',
			cell: (u) => (
				<div className="nm">
					<Avatar name={u.name || u.email || '?'} />
					<div className="min-w-0">
						<b>{u.name}</b>
						<small>{[u.email, u.mobile].filter(Boolean).join(' · ') || '—'}</small>
					</div>
				</div>
			),
		},
		{
			key: 'roles',
			header: 'Roles',
			cell: (u) =>
				u.roles.length ? (
					<div className="flex max-w-[260px] flex-wrap gap-1">
						{u.roles.map((r) => (
							<Badge key={r.id} tone="line">
								{r.name}
							</Badge>
						))}
					</div>
				) : (
					<span className="text-t4">None</span>
				),
		},
		{
			key: 'mfa',
			header: '2FA',
			cell: (u) =>
				u.auth_config?.two_factor_auth?.required ? (
					<span className="text-t3">Required</span>
				) : (
					<span className="text-t4">Off</span>
				),
		},
		{
			key: 'status',
			header: 'Status',
			cell: (u) =>
				u.is_active ? (
					<Badge tone="green" dot>
						Active
					</Badge>
				) : (
					<Badge tone="gray">Inactive</Badge>
				),
		},
		{
			key: 'last',
			header: 'Last sign-in',
			cell: (u) => <span className="text-t3">{u.last_login ?? 'Never'}</span>,
		},
		{
			key: 'actions',
			header: '',
			align: 'right',
			cell: (u) => (
				<RowMenu
					label={`Actions for ${u.name}`}
					items={[
						{ label: 'Edit', icon: 'cog', onSelect: () => setEditing(u) },
						{ label: 'Reset password', icon: 'key', onSelect: () => setResetting(u) },
						null,
						u.is_active
							? { label: 'Deactivate', icon: 'x', danger: true, onSelect: () => setToggling(u) }
							: { label: 'Activate', icon: 'check', onSelect: () => setToggling(u) },
					]}
				/>
			),
		},
	];

	const total = users?.total_records ?? 0;

	return (
		<>
			<Toolbar>
				<SearchInput value={search} onChange={resetPage(setSearch)} placeholder="Search users" />
				<Segmented
					label="Filter by status"
					value={status}
					onChange={resetPage(setStatus)}
					options={[
						{ value: 'all', label: 'All' },
						{ value: 'active', label: 'Active' },
						{ value: 'inactive', label: 'Inactive' },
					]}
				/>
				<Select
					aria-label="Filter by role"
					className="!w-[180px]"
					value={role}
					onChange={(e) => resetPage(setRole)(e.target.value)}
				>
					<option value="">All roles</option>
					{roleOptions.map((r) => (
						<option key={r.id} value={r.label}>
							{r.label}
						</option>
					))}
				</Select>
				{users && (
					<span className="num ml-auto text-[12px] text-t3">
						{users.active_count} active · {users.inactive_count} inactive
					</span>
				)}
			</Toolbar>
			<Table
				columns={columns}
				rows={users?.records}
				rowKey={(u) => u.id}
				loading={isLoading}
				error={error}
				onRetry={() => refetch()}
				onRowClick={setEditing}
				empty={
					filtered ? (
						<EmptyState title="No users match">Try another search or filter.</EmptyState>
					) : (
						<EmptyState
							title="No users yet"
							action={
								<Button size="sm" icon="plus" onClick={() => setInviteOpen(true)}>
									Invite user
								</Button>
							}
						>
							Add the people who will sign in to this app.
						</EmptyState>
					)
				}
				footer={
					total > 0 && (
						<Pagination
							page={page}
							pageSize={PAGE_SIZE}
							totalRecords={total}
							totalPages={Math.max(1, Math.ceil(total / PAGE_SIZE))}
							onPage={setPage}
							noun="users"
							busy={isFetching && !isLoading}
						/>
					)
				}
			/>

			<UserDrawer
				app={app}
				open={inviteOpen || !!editing}
				onOpenChange={(o) => {
					if (!o) {
						setInviteOpen(false);
						setEditing(null);
					}
				}}
				user={editing}
				roleOptions={roleOptions}
				defaultDialCode={data?.pn_country_code ?? '+91'}
			/>
			<ResetPasswordModal app={app} user={resetting} onClose={() => setResetting(null)} />
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
					? 'They will no longer be able to sign in. You can activate them again later.'
					: 'They will be able to sign in again with their existing roles.'}
			</ConfirmModal>
		</>
	);
}
