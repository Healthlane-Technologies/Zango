import { useEffect, useState } from 'react';
import {
	money,
	useAgentList,
	useDeleteAgent,
	useDuplicateAgent,
	useToggleAgent,
	type Agent,
} from '@/api/ai';
import {
	Button,
	ConfirmModal,
	EmptyState,
	Pagination,
	RowMenu,
	SearchInput,
	Segmented,
	Switch,
	Table,
	Toolbar,
	useDebounced,
	type Column,
} from '@/ui';
import { AgentDrawer } from './AgentDrawer';
import { serviceLabel, StatStrip } from './parts';

type Status = '' | 'active' | 'disabled';
const PAGE_SIZE = 20;

export function AgentsTab({ appId }: { appId: string }) {
	const [q, setQ] = useState('');
	const search = useDebounced(q, 300);
	const [status, setStatus] = useState<Status>('');
	const [page, setPage] = useState(1);
	useEffect(() => setPage(1), [search, status]);

	const list = useAgentList(appId, { page, pageSize: PAGE_SIZE, search, status });
	const toggle = useToggleAgent(appId);
	const duplicate = useDuplicateAgent(appId);
	const remove = useDeleteAgent(appId);

	const [drawer, setDrawer] = useState<number | 'new' | null>(null);
	const [confirm, setConfirm] = useState<{ a: Agent; action: 'disable' | 'delete' } | null>(null);

	const rows = list.data?.agents.records;
	const stats = list.data?.stats;

	const columns: Column<Agent>[] = [
		{
			key: 'n',
			header: 'Agent',
			cell: (a) => (
				<div className="nm">
					<div className="min-w-0">
						<b className="mono">{a.name}</b>
						{a.description && <small className="max-w-[340px] truncate">{a.description}</small>}
					</div>
				</div>
			),
		},
		{
			key: 'm',
			header: 'Model',
			cell: (a) =>
				a.provider_name ? (
					<div className="min-w-0">
						<div className="mono text-[12.5px]">{a.model || '—'}</div>
						<small className="text-t3">
							{a.provider_name} · {serviceLabel(a.provider_slug)}
						</small>
					</div>
				) : (
					<span className="text-amber-t">No provider</span>
				),
		},
		{
			key: 'o',
			header: 'Output',
			cell: (a) => (
				<span className="text-t2">
					{a.output_schema}
					{a.tools.length > 0 && (
						<span className="text-t3">
							{' '}
							· {a.tools.length} tool{a.tools.length > 1 ? 's' : ''}
						</span>
					)}
					{a.short_term_memory && <span className="text-t3"> · memory</span>}
				</span>
			),
		},
		{
			key: 'r',
			header: 'Runs (24h)',
			cell: (a) => <span className="num">{a.metrics?.invocations24h ?? '—'}</span>,
		},
		{
			key: 'c',
			header: 'Cost',
			cell: (a) => <span className="num">{money(a.metrics?.totalCost ?? a.total_cost_usd)}</span>,
		},
		{
			key: 'e',
			header: 'On',
			cell: (a) => (
				<span onClick={(e) => e.stopPropagation()}>
					<Switch
						label={a.is_enabled ? `Disable ${a.name}` : `Enable ${a.name}`}
						checked={a.is_enabled}
						onChange={(v) =>
							v ? toggle.mutate({ id: a.id, is_enabled: true }) : setConfirm({ a, action: 'disable' })
						}
					/>
				</span>
			),
		},
		{
			key: 'a',
			header: '',
			align: 'right',
			cell: (a) => (
				<RowMenu
					label={`Actions for ${a.name}`}
					items={[
						{ label: 'Open', icon: 'pen', onSelect: () => setDrawer(a.id) },
						{ label: 'Duplicate', icon: 'copy', onSelect: () => duplicate.mutate({ id: a.id }) },
						null,
						{
							label: 'Delete',
							icon: 'x',
							danger: true,
							onSelect: () => setConfirm({ a, action: 'delete' }),
						},
					]}
				/>
			),
		},
	];

	return (
		<>
			<StatStrip
				items={[
					['Agents', stats?.total_agents],
					['Enabled', stats?.active_agents],
					['Disabled', stats ? stats.total_agents - stats.active_agents : undefined],
					[
						'Runs (24h)',
						rows ? rows.reduce((s, a) => s + (a.metrics?.invocations24h ?? 0), 0) : undefined,
					],
				]}
			/>
			<Toolbar>
				<SearchInput value={q} onChange={setQ} placeholder="Search agents" />
				<Segmented
					label="Filter by status"
					value={status}
					onChange={setStatus}
					options={[
						{ value: '', label: 'All' },
						{ value: 'active', label: 'Enabled' },
						{ value: 'disabled', label: 'Disabled' },
					]}
				/>
				<Button variant="primary" icon="plus" className="ml-auto" onClick={() => setDrawer('new')}>
					New agent
				</Button>
			</Toolbar>
			<Table
				columns={columns}
				rows={rows}
				rowKey={(a) => a.id}
				loading={list.isLoading}
				error={list.error}
				onRetry={() => list.refetch()}
				onRowClick={(a) => setDrawer(a.id)}
				footer={
					list.data && list.data.agents.total_pages > 1 ? (
						<Pagination
							page={page}
							pageSize={PAGE_SIZE}
							totalRecords={list.data.agents.total_records}
							totalPages={list.data.agents.total_pages}
							onPage={setPage}
							noun="agents"
							busy={list.isFetching}
						/>
					) : undefined
				}
				empty={
					search || status ? (
						<EmptyState title="No agents match">Try another search or filter.</EmptyState>
					) : (
						<EmptyState
							title="No agents yet"
							action={
								<Button variant="primary" icon="plus" onClick={() => setDrawer('new')}>
									New agent
								</Button>
							}
						>
							An agent is a named LLM setup (provider, model, prompts, tools) that app code runs
							with <span className="mono">get_agent("name").run(...)</span>.
						</EmptyState>
					)
				}
			/>

			{drawer != null && (
				<AgentDrawer
					key={String(drawer)}
					appId={appId}
					agentId={drawer === 'new' ? null : drawer}
					onClose={() => setDrawer(null)}
					onCreated={(id) => setDrawer(id)}
				/>
			)}

			<ConfirmModal
				open={confirm != null}
				onOpenChange={(o) => !o && setConfirm(null)}
				title={confirm?.action === 'delete' ? 'Delete agent' : 'Disable agent'}
				confirmLabel={confirm?.action === 'delete' ? 'Delete' : 'Disable'}
				danger
				loading={toggle.isPending || remove.isPending}
				onConfirm={() => {
					if (!confirm) return;
					const done = { onSettled: () => setConfirm(null) };
					if (confirm.action === 'delete') remove.mutate({ id: confirm.a.id }, done);
					else toggle.mutate({ id: confirm.a.id, is_enabled: false }, done);
				}}
			>
				{confirm?.action === 'delete' ? (
					confirm.a.total_invocations > 0 ? (
						<p className="text-t2">
							<b className="mono">{confirm.a.name}</b> has run history, so it will be disabled
							and renamed rather than removed.
						</p>
					) : (
						<p className="text-t2">
							Delete <b className="mono">{confirm?.a.name}</b>? This can't be undone.
						</p>
					)
				) : (
					<ul className="grid list-disc gap-1.5 pl-5 text-t2">
						{(confirm?.a.metrics?.invocations24h ?? 0) > 0 && (
							<li>
								It ran {confirm?.a.metrics?.invocations24h} times in the last 24 hours. Those
								callers will start failing.
							</li>
						)}
						<li>
							Code calling <span className="mono">get_agent("{confirm?.a.name}")</span> will raise{' '}
							<span className="mono">AgentDisabled</span>.
						</li>
						{confirm?.a.short_term_memory && (
							<li>Memory sessions are kept, and come back when it's enabled again.</li>
						)}
					</ul>
				)}
			</ConfirmModal>
		</>
	);
}
