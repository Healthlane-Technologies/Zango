import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import useApi from '../../../hooks/useApi';

function StatusBadge({ status }) {
	const styles = {
		success: 'text-[#10B981]',
		error: 'text-[#EF4444]',
		timeout: 'text-[#F59E0B]',
		rate_limited: 'text-[#D97706]',
		budget_exceeded: 'text-[#EF4444]',
	};
	return (
		<span className={`flex items-center gap-[4px] font-lato text-[12px] font-medium ${styles[status] || 'text-[#6B7280]'}`}>
			<span className={`inline-block h-[6px] w-[6px] rounded-full ${status === 'success' ? 'bg-[#10B981]' : status === 'error' ? 'bg-[#EF4444]' : 'bg-[#F59E0B]'}`} />
			{status.charAt(0).toUpperCase() + status.slice(1).replace('_', ' ')}
		</span>
	);
}

function StatCard({ icon, label, value, color }) {
	return (
		<div className="flex items-center gap-[8px]">
			<span className="text-[16px]">{icon}</span>
			<span className="font-lato text-[13px] text-[#6B7280]">{label}</span>
			<span className={`font-lato text-[14px] font-bold ${color || 'text-[#111827]'}`}>{value}</span>
		</div>
	);
}

function JsonBlock({ data, maxHeight = '200px' }) {
	if (!data) return <span className="font-lato text-[13px] text-[#9CA3AF]">-</span>;
	const formatted = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
	return (
		<div className={`rounded-[6px] bg-[#1F2937] p-[12px] overflow-auto`} style={{ maxHeight }}>
			<pre className="whitespace-pre-wrap break-words font-mono text-[12px] leading-[20px] text-[#D1D5DB]">{formatted}</pre>
		</div>
	);
}

/* ─── Detail Tabs ─── */
function InvocationDetail({ invocation }) {
	const [activeTab, setActiveTab] = useState('request');

	if (!invocation) return null;

	const tabs = [
		{ id: 'request', label: 'Request / Response' },
		{ id: 'prompt', label: 'Prompt' },
		{ id: 'cost', label: 'Cost Breakdown' },
		{ id: 'metadata', label: 'Metadata' },
	];

	const promptInfo = invocation.prompt_info || {};
	const costInfo = invocation.cost_breakdown || {};

	return (
		<div>
			{/* Tab bar */}
			<div className="mb-[16px] flex gap-[24px] border-b border-[#E5E7EB]">
				{tabs.map((tab) => (
					<button
						key={tab.id}
						onClick={() => setActiveTab(tab.id)}
						className={`pb-[10px] font-lato text-[13px] font-medium border-b-[2px] transition-colors ${
							activeTab === tab.id
								? 'border-[#346BD4] text-[#346BD4]'
								: 'border-transparent text-[#6B7280] hover:text-[#111827]'
						}`}
					>
						{tab.label}
					</button>
				))}
			</div>

			{/* Request / Response */}
			{activeTab === 'request' && (
				<div className="flex flex-col gap-[16px]">
					{invocation.request_system && (
						<div>
							<span className="mb-[6px] block font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">System Prompt</span>
							<div className="rounded-[6px] bg-[#1F2937] p-[12px] max-h-[200px] overflow-auto">
								<pre className="whitespace-pre-wrap break-words font-mono text-[12px] leading-[20px] text-[#FCD34D]">{invocation.request_system}</pre>
							</div>
						</div>
					)}
					<div>
						<span className="mb-[6px] block font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Messages</span>
						<JsonBlock data={invocation.request_messages} maxHeight="300px" />
					</div>
					{invocation.request_tools && invocation.request_tools.length > 0 && (
						<div>
							<span className="mb-[6px] block font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
								Tools Sent to LLM ({invocation.request_tools.length})
							</span>
							<div className="flex flex-col gap-[8px]">
								{invocation.request_tools.map((t, i) => (
									<div key={i} className="rounded-[6px] border border-[#E5E7EB] bg-[#F9FAFB] p-[12px]">
										<div className="flex items-center gap-[8px] mb-[6px]">
											<span className="font-mono font-lato text-[13px] font-semibold text-[#111827]">{t.name}</span>
											<span className="font-lato text-[12px] text-[#6B7280]">{t.description?.slice(0, 80)}</span>
										</div>
										<JsonBlock data={t.input_schema} maxHeight="120px" />
									</div>
								))}
							</div>
						</div>
					)}
					<div className="grid grid-cols-2 gap-[16px]">
						<div>
							<span className="mb-[6px] block font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Response</span>
							<div className="rounded-[6px] bg-[#F0FDF4] border border-[#BBF7D0] p-[12px] max-h-[300px] overflow-auto">
								<pre className="whitespace-pre-wrap break-words font-lato text-[13px] leading-[22px] text-[#111827]">{invocation.response_content || '-'}</pre>
							</div>
						</div>
						{invocation.response_tool_calls && (
							<div>
								<span className="mb-[6px] block font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Tool Calls</span>
								<JsonBlock data={invocation.response_tool_calls} />
							</div>
						)}
					</div>
				</div>
			)}

			{/* Prompt */}
			{activeTab === 'prompt' && (
				<div className="flex flex-col gap-[16px]">
					<div className="grid grid-cols-2 gap-[16px]">
						<div className="rounded-[8px] border border-[#E5E7EB] bg-white p-[16px]">
							<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">System Prompt</span>
							<p className="mt-[4px] font-lato text-[14px] font-semibold text-[#111827]">
								{promptInfo.system_prompt_name || '-'}
								{promptInfo.system_prompt_version && <span className="ml-[6px] font-normal text-[#6B7280]">v{promptInfo.system_prompt_version}</span>}
							</p>
						</div>
						<div className="rounded-[8px] border border-[#E5E7EB] bg-white p-[16px]">
							<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">User Prompt</span>
							<p className="mt-[4px] font-lato text-[14px] font-semibold text-[#111827]">
								{promptInfo.user_prompt_name || '-'}
								{promptInfo.user_prompt_version && <span className="ml-[6px] font-normal text-[#6B7280]">v{promptInfo.user_prompt_version}</span>}
							</p>
						</div>
					</div>
					{promptInfo.rendered_system_prompt && (
						<div>
							<span className="mb-[6px] block font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Rendered System Prompt</span>
							<div className="rounded-[6px] bg-[#FEF3C7] border border-[#FCD34D] p-[12px] max-h-[300px] overflow-auto">
								<pre className="whitespace-pre-wrap break-words font-lato text-[13px] leading-[22px] text-[#92400E]">{promptInfo.rendered_system_prompt}</pre>
							</div>
						</div>
					)}
					{invocation.context_snapshot && (
						<div>
							<span className="mb-[6px] block font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Context Snapshot (variables passed at runtime)</span>
							<JsonBlock data={invocation.context_snapshot} />
						</div>
					)}
				</div>
			)}

			{/* Cost Breakdown */}
			{activeTab === 'cost' && (
				<div>
					<div className="rounded-[8px] border border-[#E5E7EB] overflow-hidden">
						<table className="w-full">
							<thead className="bg-[#F9FAFB]">
								<tr>
									<th className="px-[16px] py-[10px] text-left font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Metric</th>
									<th className="px-[16px] py-[10px] text-right font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Value</th>
								</tr>
							</thead>
							<tbody>
								{[
									['Stop Reason', costInfo.stop_reason || '-'],
									['Input Tokens', (costInfo.input_tokens || 0).toLocaleString()],
									['Output Tokens', (costInfo.output_tokens || 0).toLocaleString()],
									['Cache Creation Tokens', (costInfo.cache_creation_tokens || 0).toLocaleString()],
									['Cache Read Tokens', (costInfo.cache_read_tokens || 0).toLocaleString()],
									['Total Cost', `$${costInfo.cost_usd || '0'}`],
									['Latency', costInfo.latency_ms ? `${costInfo.latency_ms}ms` : '-'],
								].map(([label, val]) => (
									<tr key={label} className="border-t border-[#E5E7EB]">
										<td className="px-[16px] py-[10px] font-lato text-[13px] text-[#374151]">{label}</td>
										<td className="px-[16px] py-[10px] text-right font-mono font-lato text-[13px] text-[#111827]">{val}</td>
									</tr>
								))}
							</tbody>
						</table>
					</div>
				</div>
			)}

			{/* Metadata */}
			{activeTab === 'metadata' && (
				<div className="grid grid-cols-2 gap-[12px]">
					{[
						['Triggered By', invocation.triggered_by],
						['User ID', invocation.user_id_ref || '-'],
						['Celery Task ID', invocation.celery_task_id || '-'],
						['Agent', invocation.agent_name || '-'],
						['Provider', `${invocation.provider_name} (${invocation.provider_slug})`],
						['Model', invocation.model],
						['Status', invocation.status],
						['Error Type', invocation.error_type || '-'],
						['Created', new Date(invocation.created_at).toLocaleString()],
						['Time to First Token', invocation.time_to_first_token_ms ? `${invocation.time_to_first_token_ms}ms` : '-'],
					].map(([label, val]) => (
						<div key={label} className="flex">
							<span className="w-[140px] shrink-0 font-lato text-[13px] text-[#6B7280]">{label}</span>
							<span className="font-lato text-[13px] text-[#111827]">{val}</span>
						</div>
					))}
					{invocation.request_params && (
						<div className="col-span-2">
							<span className="mb-[6px] block font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Request Params</span>
							<JsonBlock data={invocation.request_params} maxHeight="120px" />
						</div>
					)}
					{invocation.error_message && (
						<div className="col-span-2">
							<span className="mb-[6px] block font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Error Message</span>
							<div className="rounded-[6px] bg-[#FEF2F2] border border-[#FECACA] p-[12px]">
								<pre className="whitespace-pre-wrap font-mono text-[12px] text-[#991B1B]">{invocation.error_message}</pre>
							</div>
						</div>
					)}
				</div>
			)}
		</div>
	);
}

/* ─── Invocation Row ─── */
function InvocationRow({ inv, onExpand, isExpanded, detail, loadingDetail }) {
	return (
		<div className="border-b border-[#E5E7EB] bg-white">
			<div className="flex items-center px-[16px] py-[12px] cursor-pointer hover:bg-[#F9FAFB]" onClick={onExpand}>
				<button className="mr-[12px] text-[#6B7280]">
					<svg width="10" height="10" viewBox="0 0 10 10" className={`transition-transform ${isExpanded ? 'rotate-90' : ''}`}>
						<path d="M3 1L7 5L3 9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" fill="none"/>
					</svg>
				</button>
				<span className="mr-[16px] w-[70px] font-mono font-lato text-[12px] text-[#6B7280]">
					inv_{String(inv.id).padStart(4, '0')}
				</span>
				<span className="mr-[16px] w-[120px] font-lato text-[12px] text-[#374151]">
					{new Date(inv.created_at).toLocaleString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', month: 'short', day: 'numeric' })}
				</span>
				<span className="mr-[16px] w-[160px] font-lato text-[13px] font-medium text-[#111827] truncate">
					{inv.agent_name || '-'}
				</span>
				<span className="mr-[16px] w-[160px]">
					<span className="block font-lato text-[12px] text-[#111827]">{inv.provider_name}</span>
					<span className="block font-mono font-lato text-[11px] text-[#6B7280]">{inv.model}</span>
				</span>
				<span className="mr-[16px] w-[100px] font-mono font-lato text-[12px] text-[#374151]">
					{(inv.input_tokens || 0).toLocaleString()} / {(inv.output_tokens || 0).toLocaleString()}
				</span>
				<span className="mr-[16px] w-[70px] font-lato text-[12px] text-[#374151]">
					${parseFloat(inv.cost_usd || 0).toFixed(4)}
				</span>
				<span className="mr-[16px] w-[60px] font-lato text-[12px] text-[#346BD4]">
					{inv.latency_ms ? `${(inv.latency_ms / 1000).toFixed(1)}s` : '-'}
				</span>
				<span className="mr-[16px] w-[70px] font-lato text-[11px] text-[#6B7280] capitalize">
					{inv.triggered_by}
				</span>
				<span className="w-[80px]"><StatusBadge status={inv.status} /></span>
			</div>

			{isExpanded && (
				<div className="border-t border-[#E5E7EB] px-[24px] py-[16px] bg-[#FAFBFC]">
					{loadingDetail ? (
						<div className="flex items-center justify-center py-[32px]">
							<span className="inline-block h-[20px] w-[20px] animate-spin rounded-full border-[2px] border-[#346BD4] border-t-transparent" />
							<span className="ml-[8px] font-lato text-[13px] text-[#6B7280]">Loading details...</span>
						</div>
					) : (
						<InvocationDetail invocation={detail} />
					)}
				</div>
			)}
		</div>
	);
}

/* ─── Main Component ─── */
export default function InvocationLogs() {
	const { appId } = useParams();
	const triggerApi = useApi();

	const [invocations, setInvocations] = useState([]);
	const [stats, setStats] = useState({});
	const [agents, setAgents] = useState([]);
	const [providers, setProviders] = useState([]);
	const [expandedId, setExpandedId] = useState(null);
	const [detailData, setDetailData] = useState({});
	const [loadingDetail, setLoadingDetail] = useState(false);
	const [page, setPage] = useState(1);
	const [totalPages, setTotalPages] = useState(1);

	// Filters
	const [search, setSearch] = useState('');
	const [filterAgent, setFilterAgent] = useState('');
	const [filterProvider, setFilterProvider] = useState('');
	const [filterStatus, setFilterStatus] = useState('');
	const [filterTriggeredBy, setFilterTriggeredBy] = useState('');

	const fetchStats = useCallback(async () => {
		const { response, success } = await triggerApi({ url: `/api/v1/apps/${appId}/ai/invocations/stats/`, type: 'GET', loader: false });
		if (success && response) setStats(response);
	}, [appId, triggerApi]);

	const fetchInvocations = useCallback(async () => {
		const params = new URLSearchParams({ page: String(page) });
		if (search) params.set('search', search);
		if (filterAgent) params.set('agent_id', filterAgent);
		if (filterProvider) params.set('provider_id', filterProvider);
		if (filterStatus) params.set('status', filterStatus);
		if (filterTriggeredBy) params.set('triggered_by', filterTriggeredBy);

		const { response, success } = await triggerApi({ url: `/api/v1/apps/${appId}/ai/invocations/?${params}`, type: 'GET', loader: false });
		if (success && response) {
			const data = response.invocations || {};
			setInvocations(data.records || []);
			setTotalPages(data.total_pages || 1);
		}
	}, [appId, triggerApi, page, search, filterAgent, filterProvider, filterStatus, filterTriggeredBy]);

	const fetchDetail = async (id) => {
		if (detailData[id]) return;
		setLoadingDetail(true);
		const { response, success } = await triggerApi({ url: `/api/v1/apps/${appId}/ai/invocations/${id}/`, type: 'GET', loader: false });
		setLoadingDetail(false);
		if (success && response?.invocation) {
			setDetailData((prev) => ({ ...prev, [id]: response.invocation }));
		}
	};

	const fetchDropdowns = useCallback(async () => {
		const [agentRes, providerRes] = await Promise.all([
			triggerApi({ url: `/api/v1/apps/${appId}/ai/agents/`, type: 'GET', loader: false }),
			triggerApi({ url: `/api/v1/apps/${appId}/ai/providers/`, type: 'GET', loader: false }),
		]);
		if (agentRes.success) setAgents(agentRes.response?.agents?.records || agentRes.response?.agents || []);
		if (providerRes.success) setProviders(providerRes.response?.providers?.records || providerRes.response?.providers || []);
	}, [appId, triggerApi]);

	useEffect(() => { fetchStats(); fetchDropdowns(); }, [appId]);
	useEffect(() => { fetchInvocations(); }, [page, search, filterAgent, filterProvider, filterStatus, filterTriggeredBy]);

	const handleExpand = (id) => {
		if (expandedId === id) { setExpandedId(null); return; }
		setExpandedId(id);
		fetchDetail(id);
	};

	const selectClass = "rounded-[6px] border border-[#DDE2E5] px-[10px] py-[8px] font-lato text-[13px] text-[#374151] outline-none focus:border-[#5048ED] bg-white";

	return (
		<div className="flex flex-col gap-[24px]">
			{/* Header */}
			<div className="rounded-[16px] border border-[#E5E7EB] bg-white p-[24px]">
				<h2 className="font-source-sans-pro text-[18px] font-semibold text-[#111827]">Invocation Logs</h2>
				<p className="mb-[16px] font-lato text-[14px] text-[#6B7280]">
					Complete audit trail of every agent run — LLM calls, resolved prompts, cost breakdown
				</p>
				<div className="flex flex-wrap items-center gap-[20px]">
					<StatCard icon="🏃" label="Total Runs" value={stats.total_runs ?? '-'} />
					<div className="h-[16px] w-[1px] bg-[#E5E7EB]" />
					<StatCard icon="📅" label="Today" value={stats.today ?? '-'} />
					<div className="h-[16px] w-[1px] bg-[#E5E7EB]" />
					<StatCard icon="⚠" label="Errors (24h)" value={stats.errors_24h ?? '-'} color={stats.errors_24h > 0 ? 'text-[#EF4444]' : 'text-[#111827]'} />
					<div className="h-[16px] w-[1px] bg-[#E5E7EB]" />
					<StatCard icon="💰" label="Cost Today" value={stats.cost_today != null ? `$${parseFloat(stats.cost_today).toFixed(2)}` : '-'} />
				</div>
			</div>

			{/* Filters */}
			<div className="flex flex-wrap items-center gap-[10px]">
				<input
					value={search}
					onChange={(e) => { setSearch(e.target.value); setPage(1); }}
					placeholder="Search by agent, provider, or model..."
					className="w-[280px] rounded-[6px] border border-[#DDE2E5] px-[12px] py-[8px] font-lato text-[13px] outline-none focus:border-[#5048ED]"
				/>
				<select value={filterAgent} onChange={(e) => { setFilterAgent(e.target.value); setPage(1); }} className={selectClass}>
					<option value="">All Agents</option>
					{agents.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
				</select>
				<select value={filterProvider} onChange={(e) => { setFilterProvider(e.target.value); setPage(1); }} className={selectClass}>
					<option value="">All Providers</option>
					{providers.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
				</select>
				<select value={filterStatus} onChange={(e) => { setFilterStatus(e.target.value); setPage(1); }} className={selectClass}>
					<option value="">All Status</option>
					<option value="success">Success</option>
					<option value="error">Error</option>
					<option value="timeout">Timeout</option>
					<option value="rate_limited">Rate Limited</option>
					<option value="budget_exceeded">Budget Exceeded</option>
				</select>
				<select value={filterTriggeredBy} onChange={(e) => { setFilterTriggeredBy(e.target.value); setPage(1); }} className={selectClass}>
					<option value="">Triggered By</option>
					<option value="user">User</option>
					<option value="celery">Celery</option>
					<option value="cron">Cron</option>
					<option value="system">System</option>
				</select>
			</div>

			{/* Table */}
			<div className="rounded-[8px] border border-[#E5E7EB] bg-white overflow-hidden">
				{/* Table header */}
				<div className="flex items-center px-[16px] py-[10px] bg-[#F9FAFB] border-b border-[#E5E7EB] font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
					<span className="mr-[12px] w-[10px]" />
					<span className="mr-[16px] w-[70px]">ID</span>
					<span className="mr-[16px] w-[120px]">Timestamp</span>
					<span className="mr-[16px] w-[160px]">Agent</span>
					<span className="mr-[16px] w-[160px]">Provider / Model</span>
					<span className="mr-[16px] w-[100px]">Tokens</span>
					<span className="mr-[16px] w-[70px]">Cost</span>
					<span className="mr-[16px] w-[60px]">Latency</span>
					<span className="mr-[16px] w-[70px]">Trigger</span>
					<span className="w-[80px]">Status</span>
				</div>

				{invocations.length === 0 ? (
					<div className="px-[24px] py-[48px] text-center">
						<p className="font-lato text-[14px] text-[#9CA3AF]">No invocations found.</p>
					</div>
				) : (
					invocations.map((inv) => (
						<InvocationRow
							key={inv.id}
							inv={inv}
							isExpanded={expandedId === inv.id}
							onExpand={() => handleExpand(inv.id)}
							detail={detailData[inv.id]}
							loadingDetail={loadingDetail && expandedId === inv.id}
						/>
					))
				)}
			</div>

			{/* Pagination */}
			{totalPages > 1 && (
				<div className="flex items-center justify-center gap-[8px]">
					<button
						onClick={() => setPage((p) => Math.max(1, p - 1))}
						disabled={page === 1}
						className="rounded-[6px] border border-[#DDE2E5] px-[12px] py-[6px] font-lato text-[13px] text-[#374151] hover:bg-[#F9FAFB] disabled:opacity-40"
					>
						Previous
					</button>
					<span className="font-lato text-[13px] text-[#6B7280]">
						Page {page} of {totalPages}
					</span>
					<button
						onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
						disabled={page === totalPages}
						className="rounded-[6px] border border-[#DDE2E5] px-[12px] py-[6px] font-lato text-[13px] text-[#374151] hover:bg-[#F9FAFB] disabled:opacity-40"
					>
						Next
					</button>
				</div>
			)}
		</div>
	);
}
