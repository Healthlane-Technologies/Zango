import { useEffect, useMemo, useState } from 'react';
import {
	money,
	useAgents,
	useInvocationStats,
	useInvocations,
	useProviders,
	type Invocation,
	type InvocationFilters,
	type InvocationGroup,
	type InvocationStatus,
	type RunGroup,
	type StandaloneGroup,
} from '@/api/ai';
import {
	Badge,
	Button,
	cx,
	EmptyState,
	FilterSelect,
	Icon,
	Pagination,
	Table,
	Toolbar,
	type Column,
} from '@/ui';
import { fmtDate, fmtInt, fmtMs, RunStatus, StatStrip } from './parts';
import { RunDrawer } from './RunDrawer';

const PAGE_SIZE = 20;

const EMPTY_FILTERS: InvocationFilters = {
	agent_id: '',
	provider_id: '',
	status: '',
	triggered_by: '',
	has_session: '',
	start_date: '',
	end_date: '',
};

/** One table row: a session, a multi-round run, or a single LLM call. */
interface Row {
	key: string;
	depth: number;
	kind: 'session' | 'run' | 'call';
	label: string;
	first: Invocation;
	calls: Invocation[];
	/** Set on call rows. */
	inv?: Invocation;
	expandable: boolean;
	runs?: number;
}

function summarize(calls: Invocation[]) {
	const sum = (f: (i: Invocation) => number) => calls.reduce((s, i) => s + f(i), 0);
	const bad = calls.find((c) => c.status !== 'success');
	return {
		tokensIn: sum((i) => i.input_tokens),
		tokensOut: sum((i) => i.output_tokens),
		cost: sum((i) => Number(i.cost_usd)),
		latency: sum((i) => i.latency_ms ?? 0),
		status: (bad?.status ?? calls[calls.length - 1]?.status) as InvocationStatus,
	};
}

const callsOf = (g: RunGroup | StandaloneGroup) => (g.type === 'run' ? g.rounds : [g.inv]);

function flatten(groups: InvocationGroup[], open: Set<string>): Row[] {
	const rows: Row[] = [];
	const pushRun = (g: RunGroup | StandaloneGroup, depth: number, prefix: string) => {
		if (g.type === 'standalone' || g.rounds.length === 1) {
			const inv = g.type === 'standalone' ? g.inv : g.rounds[0];
			rows.push({
				key: `${prefix}c${inv.id}`,
				depth,
				kind: 'call',
				label: g.type === 'run' && g.run_label ? g.run_label : `#${inv.id}`,
				first: inv,
				calls: [inv],
				inv,
				expandable: false,
			});
			return;
		}
		const key = `${prefix}r${g.run_id}`;
		rows.push({
			key,
			depth,
			kind: 'run',
			label: g.run_label ?? `Run #${g.rounds[0].id}`,
			first: g.rounds[0],
			calls: g.rounds,
			expandable: true,
		});
		if (open.has(key))
			for (const r of g.rounds)
				rows.push({
					key: `${key}c${r.id}`,
					depth: depth + 1,
					kind: 'call',
					label: `Round ${r.round_number ?? '?'}`,
					first: r,
					calls: [r],
					inv: r,
					expandable: false,
				});
	};
	for (const g of groups) {
		if (g.type !== 'session') {
			pushRun(g, 0, '');
			continue;
		}
		const key = `s${g.session_id}`;
		const calls = g.runs.flatMap(callsOf);
		if (!calls.length) continue;
		rows.push({
			key,
			depth: 0,
			kind: 'session',
			label: g.session_id,
			first: calls[0],
			calls,
			expandable: true,
			runs: g.runs.length,
		});
		if (open.has(key)) for (const r of g.runs) pushRun(r, 1, key);
	}
	return rows;
}

const dayISO = (offsetDays: number) => {
	const d = new Date();
	d.setDate(d.getDate() - offsetDays);
	return d.toISOString().slice(0, 10);
};

export function RunsTab({ appId }: { appId: string }) {
	const [f, setF] = useState<InvocationFilters>(EMPTY_FILTERS);
	const [page, setPage] = useState(1);
	useEffect(() => setPage(1), [f]);
	const set = (k: keyof InvocationFilters, v: string) => setF((cur) => ({ ...cur, [k]: v }));

	const stats = useInvocationStats(appId);
	const list = useInvocations(appId, { ...f, page, pageSize: PAGE_SIZE });
	const agents = useAgents(appId);
	const providers = useProviders(appId);

	const [open, setOpen] = useState<Set<string>>(new Set());
	const [detail, setDetail] = useState<number | null>(null);
	const rows = useMemo(() => flatten(list.data?.records ?? [], open), [list.data, open]);
	const toggle = (key: string) =>
		setOpen((cur) => {
			const next = new Set(cur);
			if (next.has(key)) next.delete(key);
			else next.add(key);
			return next;
		});

	const anyFilter = Object.values(f).some(Boolean);
	const quick = (days: number) =>
		f.start_date === dayISO(days) && f.end_date === dayISO(0);

	const columns: Column<Row>[] = [
		{
			key: 'l',
			header: 'Run',
			cell: (r) => (
				<div className="flex items-center gap-1.5" style={{ paddingLeft: r.depth * 18 }}>
					{r.expandable ? (
						<Icon
							name="back"
							className={cx('shrink-0 text-t3 transition-transform', open.has(r.key) ? '-rotate-90' : 'rotate-180')}
						/>
					) : (
						<span className="w-[14px]" />
					)}
					<span className={cx('mono truncate text-[12.5px]', r.kind === 'session' && 'max-w-[160px]')} title={r.label}>
						{r.label}
					</span>
					{r.kind === 'session' && (
						<Badge tone="violet">
							{r.runs} run{r.runs === 1 ? '' : 's'}
						</Badge>
					)}
					{r.kind === 'run' && <Badge tone="line">{r.calls.length} rounds</Badge>}
				</div>
			),
		},
		{
			key: 't',
			header: 'Started',
			cell: (r) => <span className="text-t3">{fmtDate(r.first.created_at)}</span>,
		},
		{
			key: 'a',
			header: 'Agent',
			cell: (r) => <span className="mono">{r.first.agent_name || '—'}</span>,
		},
		{
			key: 'm',
			header: 'Model',
			cell: (r) => (
				<div className="min-w-0">
					<div className="mono truncate text-[12.5px]">{r.first.model}</div>
					<small className="text-t3">{r.first.provider_name}</small>
				</div>
			),
		},
		{
			key: 'k',
			header: 'Tokens in / out',
			cell: (r) => {
				const s = summarize(r.calls);
				return (
					<span className="num">
						{fmtInt(s.tokensIn)} / {fmtInt(s.tokensOut)}
					</span>
				);
			},
		},
		{
			key: 'c',
			header: 'Cost',
			cell: (r) => <span className="num">{money(summarize(r.calls).cost, 4)}</span>,
		},
		{
			key: 'd',
			header: 'Time',
			cell: (r) => (
				<span className="num">{r.kind === 'session' ? '—' : fmtMs(summarize(r.calls).latency)}</span>
			),
		},
		{
			key: 'g',
			header: 'Trigger',
			cell: (r) => <span className="text-t2">{r.first.triggered_by}</span>,
		},
		{ key: 's', header: 'Status', cell: (r) => <RunStatus status={summarize(r.calls).status} /> },
	];

	return (
		<>
			<StatStrip
				items={[
					['Calls', stats.data ? fmtInt(stats.data.total_runs) : undefined],
					['Today', stats.data ? fmtInt(stats.data.today) : undefined],
					[
						'Errors (24h)',
						stats.data ? fmtInt(stats.data.errors_24h) : undefined,
						stats.data && stats.data.errors_24h > 0 ? 'red' : undefined,
					],
					['Cost today', stats.data ? money(stats.data.cost_today) : undefined],
				]}
			/>
			<Toolbar>
				<FilterSelect
					label="Agent"
					allLabel="All agents"
					value={f.agent_id}
					onChange={(v) => set('agent_id', v)}
					options={agents.data?.map((a) => ({ id: a.id, label: a.name }))}
				/>
				<FilterSelect
					label="Provider"
					allLabel="All providers"
					value={f.provider_id}
					onChange={(v) => set('provider_id', v)}
					options={providers.data?.map((p) => ({ id: p.id, label: p.name }))}
				/>
				<FilterSelect
					label="Status"
					allLabel="Any status"
					value={f.status}
					onChange={(v) => set('status', v)}
					options={[
						{ id: 'success', label: 'Success' },
						{ id: 'error', label: 'Error' },
						{ id: 'timeout', label: 'Timeout' },
						{ id: 'rate_limited', label: 'Rate limited' },
						{ id: 'budget_exceeded', label: 'Over budget' },
					]}
				/>
				<FilterSelect
					label="Trigger"
					allLabel="Any trigger"
					value={f.triggered_by}
					onChange={(v) => set('triggered_by', v)}
					options={[
						{ id: 'user', label: 'User' },
						{ id: 'celery', label: 'Celery' },
						{ id: 'cron', label: 'Cron' },
						{ id: 'system', label: 'System (tests)' },
					]}
				/>
				<FilterSelect
					label="Memory"
					allLabel="Memory: any"
					value={f.has_session}
					onChange={(v) => set('has_session', v)}
					options={[
						{ id: 'yes', label: 'With memory' },
						{ id: 'no', label: 'Without memory' },
					]}
				/>
				<Button size="xs" variant="ghost" icon="pulse" loading={list.isFetching && !list.isLoading} onClick={() => { void list.refetch(); void stats.refetch(); }}>
					Refresh
				</Button>
			</Toolbar>
			<div className="mb-3 flex flex-wrap items-center gap-2 text-[12.5px]">
				<span className="text-t3">From</span>
				<input
					type="date"
					aria-label="From date"
					className="input h-8 w-auto"
					value={f.start_date}
					max={f.end_date || undefined}
					onChange={(e) => set('start_date', e.target.value)}
				/>
				<span className="text-t3">to</span>
				<input
					type="date"
					aria-label="To date"
					className="input h-8 w-auto"
					value={f.end_date}
					min={f.start_date || undefined}
					onChange={(e) => set('end_date', e.target.value)}
				/>
				{(
					[
						['Today', 0],
						['7 days', 6],
						['30 days', 29],
					] as const
				).map(([label, days]) => (
					<Button
						key={label}
						size="xs"
						variant={quick(days) ? 'primary' : 'secondary'}
						onClick={() => setF((cur) => ({ ...cur, start_date: dayISO(days), end_date: dayISO(0) }))}
					>
						{label}
					</Button>
				))}
				{anyFilter && (
					<Button size="xs" variant="ghost" onClick={() => setF(EMPTY_FILTERS)}>
						Clear filters
					</Button>
				)}
			</div>
			<Table
				columns={columns}
				rows={rows}
				rowKey={(r) => r.key}
				loading={list.isLoading}
				error={list.error}
				onRetry={() => list.refetch()}
				onRowClick={(r) => (r.expandable ? toggle(r.key) : r.inv && setDetail(r.inv.id))}
				footer={
					list.data && list.data.total_records > 0 ? (
						<Pagination
							page={Math.min(page, list.data.total_pages)}
							pageSize={PAGE_SIZE}
							totalRecords={list.data.total_records}
							totalPages={list.data.total_pages}
							onPage={setPage}
							noun="runs"
							busy={list.isFetching}
						/>
					) : undefined
				}
				empty={
					anyFilter ? (
						<EmptyState title="No runs match">Try other filters.</EmptyState>
					) : (
						<EmptyState title="No runs yet">
							Every agent call is logged here: what was sent, what came back, tools used, time
							and cost.
						</EmptyState>
					)
				}
			/>
			{detail != null && <RunDrawer appId={appId} id={detail} onClose={() => setDetail(null)} />}
		</>
	);
}
