import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useApp } from '@/api/apps';
import { useAppId } from '@/api/hooks';
import { useRoles } from '@/api/roles';
import { useUsers } from '@/api/users';
import { Button, Page, PageHeader, Tabs } from '@/ui';
import { RolesTab } from './users/RolesTab';
import { UsersTab } from './users/UsersTab';

type Tab = 'users' | 'roles';

export function UsersPage() {
	const appId = useAppId();
	const { data: app } = useApp(appId);
	const [params, setParams] = useSearchParams();
	const tab: Tab = params.get('tab') === 'roles' ? 'roles' : 'users';
	const [inviteOpen, setInviteOpen] = useState(false);
	const [roleOpen, setRoleOpen] = useState(false);

	// Unfiltered totals for the tab counts; these share cache with the default tab views.
	const { data: usersData } = useUsers(appId, {
		page: 1,
		pageSize: 20,
		search: '',
		active: 'all',
		role: '',
	});
	const { data: rolesData } = useRoles(appId, { search: '', active: 'all' });

	return (
		<Page>
			<PageHeader
				title="Users & roles"
				description={`People who can sign in to ${app?.name ?? 'this app'} and what they can do.`}
				actions={
					tab === 'users' ? (
						<Button variant="primary" icon="plus" onClick={() => setInviteOpen(true)}>
							Invite user
						</Button>
					) : (
						<Button variant="primary" icon="plus" onClick={() => setRoleOpen(true)}>
							New role
						</Button>
					)
				}
			/>
			<Tabs
				className="mb-4 !px-0"
				value={tab}
				onChange={(t) => setParams(t === 'users' ? {} : { tab: t }, { replace: true })}
				items={[
					{ value: 'users', label: 'Users', count: usersData?.users.total_records },
					{ value: 'roles', label: 'Roles', count: rolesData?.roles.total_records },
				]}
			/>
			{tab === 'users' ? (
				<UsersTab app={appId} inviteOpen={inviteOpen} setInviteOpen={setInviteOpen} />
			) : (
				<RolesTab app={appId} createOpen={roleOpen} setCreateOpen={setRoleOpen} />
			)}
		</Page>
	);
}
