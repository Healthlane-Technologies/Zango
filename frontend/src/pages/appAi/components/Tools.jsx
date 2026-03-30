import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import useApi from '../../../hooks/useApi';
import Modal from '../../../components/Modal';
import Toast from '../../../components/Notifications/Toast';

function notify(type, title, description) {
	toast.custom(
		(t) => <Toast type={type} toastRef={t} title={title} description={description} />,
		{ duration: 5000, position: 'bottom-left' }
	);
}

function SafetyBadge({ safety }) {
	const styles = {
		read_only: 'bg-[#ECFDF5] text-[#059669]',
		write: 'bg-[#FEF3C7] text-[#D97706]',
		external: 'bg-[#FEF2F2] text-[#DC2626]',
	};
	const labels = { read_only: 'READ', write: 'WRITE', external: 'EXTERNAL' };
	return (
		<span className={`rounded-[4px] px-[8px] py-[2px] font-lato text-[11px] font-bold ${styles[safety] || 'bg-[#F3F4F6] text-[#6B7280]'}`}>
			{labels[safety] || safety}
		</span>
	);
}

function ConfirmBadge({ requires }) {
	return requires ? (
		<span className="font-lato text-[12px] font-medium text-[#D97706]">Yes</span>
	) : (
		<span className="font-lato text-[12px] text-[#9CA3AF]">No</span>
	);
}

function LatencyColor({ ms }) {
	const val = ms || 0;
	let color = 'text-[#10B981]';
	if (val > 500) color = 'text-[#EF4444]';
	else if (val > 100) color = 'text-[#F59E0B]';
	const display = val >= 1000 ? `${(val / 1000).toFixed(1)}s` : `${val}ms`;
	return <span className={`font-mono font-lato text-[12px] ${color}`}>{val > 0 ? display : '-'}</span>;
}

function JsonBlock({ data, maxHeight = '200px' }) {
	if (!data) return <span className="font-lato text-[13px] text-[#9CA3AF]">-</span>;
	const formatted = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
	return (
		<div className="rounded-[6px] bg-[#1F2937] p-[12px] overflow-auto" style={{ maxHeight }}>
			<pre className="whitespace-pre-wrap break-words font-mono text-[12px] leading-[20px] text-[#D1D5DB]">{formatted}</pre>
		</div>
	);
}

/* ─── Pending Confirmations Banner ─── */
function PendingConfirmationsBanner({ confirmations, onDecide, deciding }) {
	if (!confirmations || confirmations.length === 0) return null;

	return (
		<div className="rounded-[12px] border border-[#F59E0B] bg-[#FFFBEB] p-[20px]">
			<div className="mb-[12px] flex items-center justify-between">
				<div className="flex items-center gap-[8px]">
					<span className="text-[16px]">&#9888;</span>
					<span className="font-lato text-[14px] font-semibold text-[#92400E]">
						{confirmations.length} Pending Tool Confirmation{confirmations.length > 1 ? 's' : ''}
					</span>
				</div>
			</div>
			<div className="flex flex-col gap-[8px]">
				{confirmations.map((c) => (
					<div key={c.id} className="flex items-center gap-[16px] rounded-[8px] border border-[#FDE68A] bg-white px-[16px] py-[12px]">
						<div className="flex-1 min-w-0">
							<div className="flex items-center gap-[8px]">
								<span className="font-mono font-lato text-[13px] font-semibold text-[#111827]">{c.tool_name}</span>
								{c.agent_name && (
									<span className="font-lato text-[12px] text-[#6B7280]">via {c.agent_name}</span>
								)}
							</div>
							<p className="mt-[2px] font-lato text-[12px] text-[#6B7280] truncate">
								{c.tool_input_display || JSON.stringify(c.tool_input).slice(0, 100)}
							</p>
						</div>
						<span className="flex-shrink-0 font-lato text-[12px] text-[#D97706]">
							{c.seconds_remaining > 0 ? `${Math.floor(c.seconds_remaining / 60)}m ${c.seconds_remaining % 60}s` : 'Expiring'}
						</span>
						<div className="flex gap-[6px]">
							<button
								onClick={() => onDecide(c.id, 'approved')}
								disabled={deciding}
								className="rounded-[6px] bg-[#10B981] px-[12px] py-[5px] font-lato text-[12px] font-medium text-white hover:bg-[#059669] disabled:opacity-50"
							>
								Approve
							</button>
							<button
								onClick={() => onDecide(c.id, 'denied')}
								disabled={deciding}
								className="rounded-[6px] border border-[#EF4444] px-[12px] py-[5px] font-lato text-[12px] font-medium text-[#EF4444] hover:bg-[#FEF2F2] disabled:opacity-50"
							>
								Deny
							</button>
						</div>
					</div>
				))}
			</div>
		</div>
	);
}

/* ─── Tool Detail (expanded row) ─── */
function ToolDetail({ tool, detail, loading }) {
	if (loading) {
		return (
			<div className="flex items-center justify-center py-[24px]">
				<span className="inline-block h-[16px] w-[16px] animate-spin rounded-full border-[2px] border-[#346BD4] border-t-transparent" />
				<span className="ml-[8px] font-lato text-[13px] text-[#6B7280]">Loading...</span>
			</div>
		);
	}

	const d = detail || tool;
	const params = d.parameters_display || [];

	return (
		<div className="flex gap-[32px]">
			{/* Left: metadata + params */}
			<div className="flex-1 min-w-0">
				<h4 className="mb-[12px] font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Tool Metadata</h4>
				<div className="mb-[16px] grid grid-cols-3 gap-[12px]">
					{[
						['Python Path', d.python_path],
						['Return Type', d.return_type || '-'],
						['Timeout', `${d.timeout_seconds}s`],
						['Rate Limit', d.rate_limit_rpm ? `${d.rate_limit_rpm}/min` : 'Unlimited'],
						['Display Func', d.has_display_func ? 'Yes' : 'No'],
						['Schema Hash', d.schema_hash],
					].map(([label, val]) => (
						<div key={label}>
							<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">{label}</span>
							<p className="mt-[2px] font-mono font-lato text-[13px] text-[#111827]">{val}</p>
						</div>
					))}
				</div>

				{/* Parameters table */}
				{params.length > 0 && (
					<div>
						<h4 className="mb-[8px] font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Parameters</h4>
						<div className="rounded-[8px] border border-[#E5E7EB] overflow-hidden">
							<table className="w-full">
								<thead className="bg-[#F9FAFB]">
									<tr>
										<th className="px-[12px] py-[8px] text-left font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Name</th>
										<th className="px-[12px] py-[8px] text-left font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Type</th>
										<th className="px-[12px] py-[8px] text-center font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Required</th>
										<th className="px-[12px] py-[8px] text-left font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Description</th>
									</tr>
								</thead>
								<tbody>
									{params.map((p) => (
										<tr key={p.name} className="border-t border-[#E5E7EB]">
											<td className="px-[12px] py-[8px] font-mono font-lato text-[12px] text-[#111827]">{p.name}</td>
											<td className="px-[12px] py-[8px] font-lato text-[12px] text-[#6B7280]">{p.type}</td>
											<td className="px-[12px] py-[8px] text-center font-lato text-[12px]">
												{p.required ? <span className="text-[#10B981]">&#10003;</span> : <span className="text-[#D1D5DB]">-</span>}
											</td>
											<td className="px-[12px] py-[8px] font-lato text-[12px] text-[#374151]">
												{p.description}
												{p.enum && (
													<span className="ml-[6px] text-[#9CA3AF]">
														[{p.enum.join(', ')}]
													</span>
												)}
											</td>
										</tr>
									))}
								</tbody>
							</table>
						</div>
					</div>
				)}

				{/* Raw schema */}
				{d.parameters_schema && (
					<div className="mt-[16px]">
						<h4 className="mb-[6px] font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">JSON Schema</h4>
						<JsonBlock data={d.parameters_schema} maxHeight="160px" />
					</div>
				)}
			</div>

			{/* Right: stats */}
			<div className="w-[280px] flex-shrink-0">
				<h4 className="mb-[12px] font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Usage Stats</h4>
				<div className="grid grid-cols-2 gap-[8px]">
					{[
						['Total Calls', (d.total_calls || 0).toLocaleString()],
						['Errors', (d.total_errors || 0).toLocaleString()],
						['Timeouts', (d.total_timeouts || 0).toLocaleString()],
						['Avg Time', d.avg_execution_ms > 0 ? `${d.avg_execution_ms}ms` : '-'],
					].map(([label, val]) => (
						<div key={label} className="rounded-[6px] border border-[#E5E7EB] bg-[#F9FAFB] px-[12px] py-[10px]">
							<span className="font-lato text-[10px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">{label}</span>
							<p className="mt-[2px] font-lato text-[16px] font-semibold text-[#111827]">{val}</p>
						</div>
					))}
				</div>
				{d.last_called_at && (
					<p className="mt-[8px] font-lato text-[11px] text-[#9CA3AF]">
						Last called: {new Date(d.last_called_at).toLocaleString()}
					</p>
				)}
			</div>
		</div>
	);
}

/* ─── Tool Row ─── */
function ToolRow({ tool, onExpand, isExpanded, detail, loadingDetail }) {
	return (
		<div className="border-b border-[#E5E7EB] bg-white">
			<div className="flex items-center px-[16px] py-[12px] cursor-pointer hover:bg-[#F9FAFB]" onClick={onExpand}>
				<button className="mr-[12px] text-[#6B7280]">
					<svg width="10" height="10" viewBox="0 0 10 10" className={`transition-transform ${isExpanded ? 'rotate-90' : ''}`}>
						<path d="M3 1L7 5L3 9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" fill="none"/>
					</svg>
				</button>
				<div className="mr-[16px] w-[200px]">
					<span className="block font-mono font-lato text-[13px] font-medium text-[#111827]">{tool.name}</span>
					<span className="block font-lato text-[11px] text-[#9CA3AF] truncate">{tool.python_path}</span>
				</div>
				<span className="mr-[16px] w-[90px]">
					<span className="rounded-[4px] bg-[#F3F4F6] px-[8px] py-[2px] font-lato text-[11px] font-medium text-[#6B7280]">{tool.section}</span>
				</span>
				<span className="mr-[16px] w-[220px] font-lato text-[12px] text-[#374151] truncate">{tool.description}</span>
				<span className="mr-[16px] w-[70px]"><SafetyBadge safety={tool.safety} /></span>
				<span className="mr-[16px] w-[50px]"><ConfirmBadge requires={tool.requires_confirmation} /></span>
				<span className="mr-[16px] w-[60px] font-lato text-[12px] text-[#374151]">{tool.params_count} params</span>
				<span className="mr-[16px] w-[50px] font-lato text-[12px] text-[#374151]">{(tool.total_calls || 0).toLocaleString()}</span>
				<span className="mr-[16px] w-[60px]"><LatencyColor ms={tool.avg_execution_ms} /></span>
				<span className="w-[60px]">
					{tool.is_active ? (
						<span className="flex items-center gap-[4px] font-lato text-[12px] font-medium text-[#10B981]">
							<span className="inline-block h-[6px] w-[6px] rounded-full bg-[#10B981]" /> Active
						</span>
					) : (
						<span className="flex items-center gap-[4px] font-lato text-[12px] text-[#6B7280]">
							<span className="inline-block h-[6px] w-[6px] rounded-full bg-[#D1D5DB]" /> Inactive
						</span>
					)}
				</span>
			</div>
			{isExpanded && (
				<div className="border-t border-[#E5E7EB] px-[24px] py-[16px] bg-[#FAFBFC]">
					<ToolDetail tool={tool} detail={detail} loading={loadingDetail} />
				</div>
			)}
		</div>
	);
}

/* ─── Main Tools Component ─── */
export default function Tools() {
	const { appId } = useParams();
	const triggerApi = useApi();

	const [tools, setTools] = useState([]);
	const [stats, setStats] = useState({});
	const [sections, setSections] = useState([]);
	const [confirmations, setConfirmations] = useState([]);
	const [expandedId, setExpandedId] = useState(null);
	const [detailData, setDetailData] = useState({});
	const [loadingDetail, setLoadingDetail] = useState(false);
	const [deciding, setDeciding] = useState(false);
	const [syncing, setSyncing] = useState(false);

	// Filters
	const [search, setSearch] = useState('');
	const [filterSection, setFilterSection] = useState('');
	const [filterSafety, setFilterSafety] = useState('');
	const [filterActive, setFilterActive] = useState('');

	const fetchTools = useCallback(async () => {
		const params = new URLSearchParams();
		if (search) params.set('search', search);
		if (filterSection) params.set('section', filterSection);
		if (filterSafety) params.set('safety', filterSafety);
		if (filterActive) params.set('is_active', filterActive);
		const { response, success } = await triggerApi({ url: `/api/v1/apps/${appId}/ai/tools/?${params}`, type: 'GET', loader: false });
		if (success && response) {
			setTools(response.tools?.records || response.tools || []);
			if (response.stats) setStats(response.stats);
		}
	}, [appId, triggerApi, search, filterSection, filterSafety, filterActive]);

	const fetchSections = useCallback(async () => {
		const { response, success } = await triggerApi({ url: `/api/v1/apps/${appId}/ai/tools/sections/`, type: 'GET', loader: false });
		if (success && response) setSections(response.sections || []);
	}, [appId, triggerApi]);

	const fetchConfirmations = useCallback(async () => {
		const { response, success } = await triggerApi({ url: `/api/v1/apps/${appId}/ai/confirmations/?status=pending`, type: 'GET', loader: false });
		if (success && response) setConfirmations(response.confirmations?.records || response.confirmations || []);
	}, [appId, triggerApi]);

	const fetchDetail = async (id) => {
		if (detailData[id]) return;
		setLoadingDetail(true);
		const { response, success } = await triggerApi({ url: `/api/v1/apps/${appId}/ai/tools/${id}/`, type: 'GET', loader: false });
		setLoadingDetail(false);
		if (success && response?.tool) setDetailData((prev) => ({ ...prev, [id]: response.tool }));
	};

	useEffect(() => { fetchTools(); fetchSections(); fetchConfirmations(); }, [appId]);
	useEffect(() => { fetchTools(); }, [search, filterSection, filterSafety, filterActive]);

	const handleExpand = (id) => {
		if (expandedId === id) { setExpandedId(null); return; }
		setExpandedId(id);
		fetchDetail(id);
	};

	const handleSync = async () => {
		setSyncing(true);
		const { response, success } = await triggerApi({ url: `/api/v1/apps/${appId}/ai/tools/sync/`, type: 'POST', loader: false });
		setSyncing(false);
		if (success) {
			const s = response.stats || {};
			notify('success', 'Sync Complete', `${s.created || 0} created, ${s.updated || 0} updated, ${s.deactivated || 0} deactivated`);
			fetchTools();
			fetchSections();
		}
	};

	const handleDecide = async (confirmationId, decision) => {
		setDeciding(true);
		const { success } = await triggerApi({
			url: `/api/v1/apps/${appId}/ai/confirmations/${confirmationId}/decide/`,
			type: 'POST', loader: false,
			payload: { decision },
		});
		setDeciding(false);
		if (success) {
			notify('success', decision === 'approved' ? 'Tool Approved' : 'Tool Denied', `Confirmation ${decision}.`);
			fetchConfirmations();
		}
	};

	const selectClass = "rounded-[6px] border border-[#DDE2E5] px-[10px] py-[8px] font-lato text-[13px] text-[#374151] outline-none focus:border-[#5048ED] bg-white";

	return (
		<div className="flex flex-col gap-[24px]">
			{/* Header */}
			<div className="rounded-[16px] border border-[#E5E7EB] bg-white p-[24px]">
				<div className="mb-[16px] flex items-center justify-between">
					<div>
						<h2 className="font-source-sans-pro text-[18px] font-semibold text-[#111827]">Tools</h2>
						<p className="font-lato text-[14px] text-[#6B7280]">
							Code-defined functions that agents can call during LLM interactions. Registered via <code className="rounded bg-[#F3F4F6] px-[4px] py-[1px] text-[12px]">@tool</code> decorator.
						</p>
					</div>
					<button
						onClick={handleSync}
						disabled={syncing}
						className="flex items-center gap-[6px] rounded-[8px] border border-[#DDE2E5] px-[14px] py-[8px] font-lato text-[13px] font-medium text-[#374151] hover:bg-[#F9FAFB] disabled:opacity-50"
					>
						{syncing ? (
							<span className="inline-block h-[12px] w-[12px] animate-spin rounded-full border-[2px] border-[#374151] border-t-transparent" />
						) : (
							<svg width="14" height="14" viewBox="0 0 14 14" fill="none">
								<path d="M1 7C1 3.686 3.686 1 7 1C9.21 1 11.117 2.277 12 4.14M13 7C13 10.314 10.314 13 7 13C4.79 13 2.883 11.723 2 9.86" stroke="#374151" strokeWidth="1.2" strokeLinecap="round"/>
								<path d="M12 1V4.14H8.86" stroke="#374151" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
								<path d="M2 13V9.86H5.14" stroke="#374151" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
							</svg>
						)}
						{syncing ? 'Syncing...' : 'Sync Tools'}
					</button>
				</div>
				<div className="flex flex-wrap items-center gap-[16px]">
					<div className="flex items-center gap-[8px]">
						<span className="font-lato text-[14px] text-[#6B7280]">Active Tools</span>
						<span className="font-lato text-[14px] font-semibold text-[#111827]">{stats.active_tools ?? 0}</span>
					</div>
					<div className="h-[16px] w-[1px] bg-[#E5E7EB]" />
					<div className="flex items-center gap-[8px]">
						<span className="font-lato text-[14px] text-[#6B7280]">Sections</span>
						<span className="font-lato text-[14px] font-semibold text-[#111827]">{stats.sections ?? 0}</span>
					</div>
					<div className="h-[16px] w-[1px] bg-[#E5E7EB]" />
					<div className="flex items-center gap-[8px]">
						<span className="font-lato text-[14px] text-[#6B7280]">Confirmable</span>
						<span className="font-lato text-[14px] font-semibold text-[#D97706]">{stats.confirmable ?? 0}</span>
					</div>
					{(stats.pending_confirmations || 0) > 0 && (
						<>
							<div className="h-[16px] w-[1px] bg-[#E5E7EB]" />
							<div className="flex items-center gap-[8px]">
								<span className="font-lato text-[14px] text-[#6B7280]">Pending</span>
								<span className="rounded-[4px] bg-[#FEF3C7] px-[6px] py-[1px] font-lato text-[14px] font-bold text-[#D97706]">{stats.pending_confirmations}</span>
							</div>
						</>
					)}
				</div>
			</div>

			{/* Pending Confirmations */}
			<PendingConfirmationsBanner confirmations={confirmations} onDecide={handleDecide} deciding={deciding} />

			{/* Filters */}
			<div className="flex flex-wrap items-center gap-[10px]">
				<input
					value={search}
					onChange={(e) => setSearch(e.target.value)}
					placeholder="Search by name or description..."
					className="w-[260px] rounded-[6px] border border-[#DDE2E5] px-[12px] py-[8px] font-lato text-[13px] outline-none focus:border-[#5048ED]"
				/>
				<select value={filterSection} onChange={(e) => setFilterSection(e.target.value)} className={selectClass}>
					<option value="">All Sections</option>
					{sections.map((s) => <option key={s.section} value={s.section}>{s.section} ({s.active_count})</option>)}
				</select>
				<select value={filterSafety} onChange={(e) => setFilterSafety(e.target.value)} className={selectClass}>
					<option value="">All Safety</option>
					<option value="read_only">Read Only</option>
					<option value="write">Write</option>
					<option value="external">External</option>
				</select>
				<select value={filterActive} onChange={(e) => setFilterActive(e.target.value)} className={selectClass}>
					<option value="">All Status</option>
					<option value="true">Active</option>
					<option value="false">Inactive</option>
				</select>
			</div>

			{/* Table */}
			<div className="rounded-[8px] border border-[#E5E7EB] bg-white overflow-hidden">
				<div className="flex items-center px-[16px] py-[10px] bg-[#F9FAFB] border-b border-[#E5E7EB] font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
					<span className="mr-[12px] w-[10px]" />
					<span className="mr-[16px] w-[200px]">Tool Name</span>
					<span className="mr-[16px] w-[90px]">Section</span>
					<span className="mr-[16px] w-[220px]">Description</span>
					<span className="mr-[16px] w-[70px]">Safety</span>
					<span className="mr-[16px] w-[50px]">Confirm</span>
					<span className="mr-[16px] w-[60px]">Params</span>
					<span className="mr-[16px] w-[50px]">Calls</span>
					<span className="mr-[16px] w-[60px]">Avg Time</span>
					<span className="w-[60px]">Status</span>
				</div>

				{tools.length === 0 ? (
					<div className="px-[24px] py-[48px] text-center">
						<p className="font-lato text-[14px] text-[#9CA3AF]">
							No tools registered. Define functions with <code className="rounded bg-[#F3F4F6] px-[4px] py-[1px] text-[12px]">@tool</code> in your workspace&apos;s <code className="rounded bg-[#F3F4F6] px-[4px] py-[1px] text-[12px]">tools.py</code>, then click &quot;Sync Tools&quot;.
						</p>
					</div>
				) : (
					tools.map((tool) => (
						<ToolRow
							key={tool.id}
							tool={tool}
							isExpanded={expandedId === tool.id}
							onExpand={() => handleExpand(tool.id)}
							detail={detailData[tool.id]}
							loadingDetail={loadingDetail && expandedId === tool.id}
						/>
					))
				)}
			</div>
		</div>
	);
}
