import { useState } from 'react';
import {
	useSyncTools,
	useTool,
	useToolSections,
	useTools,
	type Tool,
	type ToolListParams,
} from '@/api/ai';
import {
	Badge,
	Button,
	CodeBlock,
	Drawer,
	EmptyState,
	ErrorState,
	KeyValues,
	SearchInput,
	SectionTitle,
	Skeleton,
	Table,
	Toolbar,
	useDebounced,
	type Column,
} from '@/ui';
import { EnabledBadge, fmtDate, fmtInt, fmtMs, SafetyBadge, StatStrip } from './parts';

export function ToolsTab({ appId }: { appId: string }) {
	const [q, setQ] = useState('');
	const search = useDebounced(q, 300);
	const [section, setSection] = useState('');
	const [safety, setSafety] = useState<ToolListParams['safety']>('');
	const [isActive, setIsActive] = useState<ToolListParams['isActive']>('');
	const list = useTools(appId, { search, section, safety, isActive });
	const sections = useToolSections(appId);
	const sync = useSyncTools(appId);
	const [openId, setOpenId] = useState<number | null>(null);

	const filtered = !!(search || section || safety || isActive);
	const rows = list.data?.tools.records;

	const columns: Column<Tool>[] = [
		{
			key: 'n',
			header: 'Tool',
			cell: (t) => (
				<div className="nm">
					<div className="min-w-0">
						<b className="mono">{t.name}</b>
						<small className="max-w-[360px] truncate">{t.description}</small>
					</div>
				</div>
			),
		},
		{ key: 's', header: 'Module', cell: (t) => <Badge tone="line">{t.section}</Badge> },
		{ key: 'f', header: 'Safety', cell: (t) => <SafetyBadge safety={t.safety} /> },
		{ key: 'p', header: 'Params', cell: (t) => <span className="num">{t.params_count}</span> },
		{ key: 'c', header: 'Calls', cell: (t) => <span className="num">{fmtInt(t.total_calls)}</span> },
		{
			key: 't',
			header: 'Avg time',
			cell: (t) => (
				<span
					className={
						!t.avg_execution_ms
							? 'text-t4'
							: t.avg_execution_ms <= 100
								? 'text-green-t'
								: t.avg_execution_ms <= 500
									? 'text-amber-t'
									: 'text-red-t'
					}
				>
					{t.avg_execution_ms ? fmtMs(t.avg_execution_ms) : '—'}
				</span>
			),
		},
		{
			key: 'a',
			header: 'Status',
			cell: (t) =>
				t.is_active ? <EnabledBadge enabled /> : <Badge tone="gray" dot>Removed from code</Badge>,
		},
	];

	return (
		<>
			<StatStrip
				items={[
					['Active tools', list.data?.stats.active_tools],
					['Modules', list.data?.stats.sections],
				]}
			/>
			<Toolbar>
				<SearchInput value={q} onChange={setQ} placeholder="Search tools" />
				<select
					className="select w-auto min-w-[140px]"
					aria-label="Module"
					value={section}
					onChange={(e) => setSection(e.target.value)}
				>
					<option value="">All modules</option>
					{sections.data?.map((s) => (
						<option key={s.section} value={s.section}>
							{s.section} ({s.active_count})
						</option>
					))}
				</select>
				<select
					className="select w-auto"
					aria-label="Safety"
					value={safety}
					onChange={(e) => setSafety(e.target.value as ToolListParams['safety'])}
				>
					<option value="">Any safety</option>
					<option value="read_only">Read only</option>
					<option value="write">Write</option>
					<option value="external">External</option>
				</select>
				<select
					className="select w-auto"
					aria-label="Status"
					value={isActive}
					onChange={(e) => setIsActive(e.target.value as ToolListParams['isActive'])}
				>
					<option value="">Any status</option>
					<option value="true">Active</option>
					<option value="false">Removed</option>
				</select>
				<Button icon="up" className="ml-auto" loading={sync.isPending} onClick={() => sync.mutate()}>
					Sync tools
				</Button>
			</Toolbar>
			<Table
				columns={columns}
				rows={rows}
				rowKey={(t) => t.id}
				loading={list.isLoading}
				error={list.error}
				onRetry={() => list.refetch()}
				onRowClick={(t) => setOpenId(t.id)}
				empty={
					filtered ? (
						<EmptyState title="No tools match">Try another search or filter.</EmptyState>
					) : (
						<EmptyState title="No tools registered">
							Define functions with <span className="mono">@tool</span> in the app's{' '}
							<span className="mono">tools.py</span>, then press Sync tools.
						</EmptyState>
					)
				}
			/>
			{openId != null && <ToolDrawer appId={appId} id={openId} onClose={() => setOpenId(null)} />}
		</>
	);
}

function ToolDrawer({ appId, id, onClose }: { appId: string; id: number; onClose: () => void }) {
	const { data: t, isLoading, error, refetch } = useTool(appId, id);
	return (
		<Drawer
			open
			wide
			onOpenChange={(o) => !o && onClose()}
			title={<span className="mono">{t?.name ?? 'Tool'}</span>}
			subtitle={t?.description}
		>
			{isLoading && <Skeleton height={200} />}
			{error && <ErrorState error={error} onRetry={() => refetch()} />}
			{t && (
				<>
					<div className="mb-4 flex flex-wrap gap-2">
						<SafetyBadge safety={t.safety} />
						<Badge tone="line">{t.section}</Badge>
						{t.is_active ? <EnabledBadge enabled /> : <Badge tone="gray">Removed from code</Badge>}
					</div>
					<KeyValues
						items={[
							['Python path', <span className="mono">{t.python_path}</span>],
							['Returns', t.return_type && <span className="mono">{t.return_type}</span>],
							['Timeout', `${t.timeout_seconds}s`],
							['Rate limit', t.rate_limit_rpm ? `${t.rate_limit_rpm}/min` : 'Unlimited'],
							[
								'Memory',
								t.memory_policy === 'exclude'
									? 'Results are left out of session memory'
									: 'Results are kept in session memory',
							],
							['Schema hash', <span className="mono">{t.schema_hash}</span>],
						]}
					/>

					<SectionTitle>Parameters</SectionTitle>
					{t.parameters_display.length ? (
						<div className="overflow-hidden rounded-lg border border-border">
							<table className="w-full text-[12.5px]">
								<thead className="bg-subtle text-left text-t3">
									<tr>
										<th className="px-3 py-1.5 font-medium">Name</th>
										<th className="px-3 py-1.5 font-medium">Type</th>
										<th className="px-3 py-1.5 font-medium">Required</th>
										<th className="px-3 py-1.5 font-medium">Description</th>
									</tr>
								</thead>
								<tbody>
									{t.parameters_display.map((p) => (
										<tr key={p.name} className="border-t border-border-soft">
											<td className="mono px-3 py-1.5">{p.name}</td>
											<td className="mono px-3 py-1.5 text-t2">
												{p.type}
												{p.enum ? ` [${p.enum.join(', ')}]` : ''}
											</td>
											<td className="px-3 py-1.5">{p.required ? 'Yes' : '—'}</td>
											<td className="px-3 py-1.5 text-t2">{p.description}</td>
										</tr>
									))}
								</tbody>
							</table>
						</div>
					) : (
						<p className="text-t3">No parameters.</p>
					)}

					<SectionTitle>Usage</SectionTitle>
					<KeyValues
						items={[
							['Calls', fmtInt(t.total_calls)],
							['Errors', fmtInt(t.total_errors)],
							['Timeouts', fmtInt(t.total_timeouts)],
							['Avg time', t.avg_execution_ms ? fmtMs(t.avg_execution_ms) : '—'],
							['Last called', fmtDate(t.last_called_at)],
						]}
					/>

					<SectionTitle>JSON schema sent to the model</SectionTitle>
					<CodeBlock maxHeight={260}>{JSON.stringify(t.parameters_schema, null, 2)}</CodeBlock>
				</>
			)}
		</Drawer>
	);
}
