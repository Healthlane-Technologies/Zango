import { useMemo, useState } from 'react';

import { useAppId, useApiMutation } from '@/api/hooks';

import { syncTasks, taskKeys, useTasks, type AppTask } from '@/api/tasks';

import {
	Badge,
	Button,
	EmptyState,
	Page,
	PageHeader,
	SearchInput,
	Segmented,
	Table,
	Toolbar,
	usePaged,
	type Column,
} from '@/ui';

import { TaskDrawer } from './tasks/TaskDrawer';

type Filter = 'all' | 'enabled' | 'disabled';

/** "patient.tasks.send_reminder" → ["send_reminder", "patient.tasks"] */
export function splitTaskName(name: string): [string, string] {
	const i = name.lastIndexOf('.');
	return i < 0 ? [name, ''] : [name.slice(i + 1), name.slice(0, i)];
}

export function EnabledBadge({ enabled }: { enabled: boolean }) {
	return (
		<Badge tone={enabled ? 'green' : 'gray'} dot>
			{enabled ? 'Enabled' : 'Disabled'}
		</Badge>
	);
}

export function TasksPage() {
	const appId = useAppId();
	const { data: tasks, isLoading, error, refetch } = useTasks(appId);
	const [q, setQ] = useState('');
	const [filter, setFilter] = useState<Filter>('all');
	const [openId, setOpenId] = useState<number | null>(null);

	const sync = useApiMutation({
		fn: () => syncTasks(appId),
		invalidate: [taskKeys.all(appId)],
		success: 'Tasks synced from app code',
	});

	const filtered = useMemo(() => {
		const needle = q.trim().toLowerCase();
		return (tasks ?? []).filter(
			(t) =>
				(filter === 'all' || t.is_enabled === (filter === 'enabled')) &&
				(!needle ||
					`${t.name} ${t.id} ${t.attached_policies.map((p) => p.name).join(' ')}`
						.toLowerCase()
						.includes(needle)),
		);
	}, [tasks, q, filter]);

	const paged = usePaged(filtered, `${q}|${filter}`);
	const open = tasks?.find((t) => t.id === openId);

	const columns: Column<AppTask>[] = [
		{
			key: 'name',
			header: 'Task',
			cell: (t) => {
				const [fn, mod] = splitTaskName(t.name);
				return (
					<div className="nm">
						<div className="min-w-0">
							<b className="mono">{fn}</b>
							{mod && <small className="mono">{mod}</small>}
						</div>
					</div>
				);
			},
		},
		{
			key: 'schedule',
			header: 'Schedule',
			cell: (t) => <span className="mono">{t.schedule || '—'}</span>,
		},
		{ key: 'status', header: 'Status', cell: (t) => <EnabledBadge enabled={t.is_enabled} /> },
		{
			key: 'policies',
			header: 'Policies',
			cell: (t) =>
				t.attached_policies.length ? (
					<span title={t.attached_policies.map((p) => p.name).join(', ')}>
						{t.attached_policies.length}
					</span>
				) : (
					<span className="text-t4">—</span>
				),
		},
		{
			key: 'updated',
			header: 'Updated',
			cell: (t) => <span className="text-t3">{t.modified_at}</span>,
		},
	];

	return (
		<Page>
			<PageHeader
				title="Tasks"
				description="Scheduled background jobs declared in the app's modules. Sync to pick up new or removed tasks."
				actions={
					<Button icon="up" loading={sync.isPending} onClick={() => sync.mutate()}>
						Sync tasks
					</Button>
				}
			/>
			<Toolbar>
				<SearchInput value={q} onChange={setQ} placeholder="Search tasks" />
				<Segmented
					label="Filter by status"
					value={filter}
					onChange={setFilter}
					options={[
						{ value: 'all', label: 'All' },
						{ value: 'enabled', label: 'Enabled' },
						{ value: 'disabled', label: 'Disabled' },
					]}
				/>
				{tasks && (
					<span className="ml-auto text-[12px] text-t3 num">
						{filtered.length} of {tasks.length}
					</span>
				)}
			</Toolbar>
			<Table
				columns={columns}
				rows={paged.rows}
				rowKey={(t) => t.id}
				loading={isLoading}
				error={error}
				onRetry={() => refetch()}
				onRowClick={(t) => setOpenId(t.id)}
				footer={paged.footer}
				empty={
					tasks?.length ? (
						<EmptyState title="No tasks match">Try another search or filter.</EmptyState>
					) : (
						<EmptyState title="No tasks yet">
							Sync to load the tasks declared in the app's modules.
						</EmptyState>
					)
				}
			/>
			{open && <TaskDrawer appId={appId} task={open} onClose={() => setOpenId(null)} />}
		</Page>
	);
}
