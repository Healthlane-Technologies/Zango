import { useMemo, useState } from 'react';

import { useAppId, useApiMutation } from '@/api/hooks';

import { policyKeys, syncPolicies, usePolicies, type Policy } from '@/api/policies';

import {
	Badge,
	Button,
	EmptyState,
	Page,
	PageHeader,
	SearchInput,
	Segmented,
	Select,
	Table,
	Toolbar,
	usePaged,
	type Column,
} from '@/ui';

import { PolicyDrawer } from './policies/PolicyDrawer';

type TypeFilter = 'all' | 'user' | 'system';

const MAX_ROLE_CHIPS = 2;

export function RoleChips({ roles }: { roles: Policy['roles'] }) {
	if (!roles.length) return <span className="text-t4">No roles</span>;
	const extra = roles.length - MAX_ROLE_CHIPS;
	return (
		<div className="flex items-center gap-1">
			{roles.slice(0, MAX_ROLE_CHIPS).map((r) => (
				<Badge key={r.id} tone="line">
					{r.name}
				</Badge>
			))}
			{extra > 0 && (
				<span
					className="text-[12px] text-t3"
					title={roles
						.slice(MAX_ROLE_CHIPS)
						.map((r) => r.name)
						.join(', ')}
				>
					+{extra}
				</span>
			)}
		</div>
	);
}

export function PoliciesPage() {
	const appId = useAppId();
	const { data, isLoading, error, refetch } = usePolicies(appId);
	const [q, setQ] = useState('');
	const [type, setType] = useState<TypeFilter>('all');
	const [role, setRole] = useState('');
	const [module, setModule] = useState('');
	const [openId, setOpenId] = useState<number | null>(null);

	const sync = useApiMutation({
		fn: () => syncPolicies(appId),
		invalidate: [policyKeys.all(appId)],
		success: 'Policies synced from app code',
	});

	const policies = data?.policies;
	const modules = useMemo(
		() => [...new Set((policies ?? []).map((p) => p.path).filter((p): p is string => !!p))].sort(),
		[policies],
	);

	const filtered = useMemo(() => {
		const needle = q.trim().toLowerCase();
		return (policies ?? []).filter(
			(p) =>
				(type === 'all' || p.type === type) &&
				(!role || p.roles.some((r) => String(r.id) === role)) &&
				(!module || p.path === module) &&
				(!needle || `${p.name} ${p.description ?? ''} ${p.id}`.toLowerCase().includes(needle)),
		);
	}, [policies, q, type, role, module]);

	const paged = usePaged(filtered, `${q}|${type}|${role}|${module}`);
	const open = policies?.find((p) => p.id === openId);

	const columns: Column<Policy>[] = [
		{
			key: 'name',
			header: 'Policy',
			cell: (p) => (
				<div className="nm">
					<div className="min-w-0">
						<b>{p.name}</b>
						{p.description && <small className="max-w-[380px] truncate">{p.description}</small>}
					</div>
				</div>
			),
		},
		{ key: 'module', header: 'Module', cell: (p) => <span className="mono">{p.path ?? '—'}</span> },
		{
			key: 'type',
			header: 'Type',
			cell: (p) => (
				<Badge tone={p.type === 'system' ? 'gray' : 'accent'}>
					{p.type === 'system' ? 'System' : 'App'}
				</Badge>
			),
		},
		{ key: 'roles', header: 'Roles', cell: (p) => <RoleChips roles={p.roles} /> },
		{
			key: 'created',
			header: 'Created',
			cell: (p) => <span className="text-t3">{p.created_at}</span>,
		},
	];

	return (
		<Page>
			<PageHeader
				title="Policies"
				description="Permissions granted to roles. App policies come from each module's policies.json; sync to pick up changes."
				actions={
					<Button icon="up" loading={sync.isPending} onClick={() => sync.mutate()}>
						Sync policies
					</Button>
				}
			/>
			<Toolbar>
				<SearchInput value={q} onChange={setQ} placeholder="Search policies" />
				<Segmented
					label="Filter by type"
					value={type}
					onChange={setType}
					options={[
						{ value: 'all', label: 'All' },
						{ value: 'user', label: 'App' },
						{ value: 'system', label: 'System' },
					]}
				/>
				<Select
					aria-label="Filter by role"
					className="!w-auto min-w-[150px]"
					value={role}
					onChange={(e) => setRole(e.target.value)}
				>
					<option value="">All roles</option>
					{data?.roles.map((r) => (
						<option key={r.id} value={r.id}>
							{r.label}
						</option>
					))}
				</Select>
				{modules.length > 0 && (
					<Select
						aria-label="Filter by module"
						className="!w-auto min-w-[150px]"
						value={module}
						onChange={(e) => setModule(e.target.value)}
					>
						<option value="">All modules</option>
						{modules.map((m) => (
							<option key={m} value={m}>
								{m}
							</option>
						))}
					</Select>
				)}
				{policies && (
					<span className="ml-auto text-[12px] text-t3 num">
						{filtered.length} of {policies.length}
					</span>
				)}
			</Toolbar>
			<Table
				columns={columns}
				rows={paged.rows}
				rowKey={(p) => p.id}
				loading={isLoading}
				error={error}
				onRetry={() => refetch()}
				onRowClick={(p) => setOpenId(p.id)}
				footer={paged.footer}
				empty={
					policies?.length ? (
						<EmptyState title="No policies match">Try another search or filter.</EmptyState>
					) : (
						<EmptyState title="No policies yet">
							Sync to load the policies declared in the app's modules.
						</EmptyState>
					)
				}
			/>
			{open && data && (
				<PolicyDrawer
					appId={appId}
					policy={open}
					roleOptions={data.roles}
					onClose={() => setOpenId(null)}
				/>
			)}
		</Page>
	);
}
