import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import useApi from '../../../../hooks/useApi';
import EditorModal from './EditorModal';
import ExecutionDetail from './ExecutionDetail';
import ConfirmModal from './ConfirmModal';
import Spinner from './Spinner';

// Phase 1 frontend for Code Execution.
// Three views inside one tab — switched via local state:
//   - 'list'   : paginated list of snippets with last-run summary
//   - 'detail' : a single execution's logs / files / source / metadata
// EditorModal overlays the list and is used both for "Add New" and "Edit".

const STATUS_BADGES = {
	success:  { dot: 'bg-emerald-500', bg: 'bg-emerald-50', text: 'text-emerald-700', label: 'Success' },
	failed:   { dot: 'bg-rose-500',    bg: 'bg-rose-50',    text: 'text-rose-700',    label: 'Failed' },
	running:  { dot: 'bg-amber-500',   bg: 'bg-amber-50',   text: 'text-amber-700',   label: 'Running' },
	queued:   { dot: 'bg-slate-400',   bg: 'bg-slate-50',   text: 'text-slate-700',   label: 'Queued' },
	timeout:  { dot: 'bg-rose-500',    bg: 'bg-rose-50',    text: 'text-rose-700',    label: 'Timed out' },
	aborted:  { dot: 'bg-slate-500',   bg: 'bg-slate-100',  text: 'text-slate-700',   label: 'Aborted' },
	draft:    { dot: 'bg-violet-500',  bg: 'bg-violet-50',  text: 'text-violet-700',  label: 'Draft' },
};

function StatusPill({ status }) {
	const s = STATUS_BADGES[status] || STATUS_BADGES.draft;
	const animate = status === 'running' || status === 'queued';
	return (
		<span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${s.bg} ${s.text}`}>
			<span className={`w-1.5 h-1.5 rounded-full ${s.dot} ${animate ? 'animate-pulse' : ''}`}></span>
			{s.label}
		</span>
	);
}

function formatRelative(ts) {
	if (!ts) return '—';
	const t = new Date(ts).getTime();
	const diff = Date.now() - t;
	if (diff < 60_000) return 'just now';
	if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
	if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
	return new Date(ts).toLocaleDateString();
}

function formatDuration(ms) {
	if (ms == null) return '—';
	if (ms < 1000) return `${ms} ms`;
	return `${(ms / 1000).toFixed(1)} s`;
}

export default function CodeExecution() {
	const { appId } = useParams();
	const triggerApi = useApi();

	const [view, setView] = useState('list');               // 'list' | 'detail'
	const [activeExecutionId, setActiveExecutionId] = useState(null);
	const [editorOpen, setEditorOpen] = useState(false);
	const [editingSnippet, setEditingSnippet] = useState(null);   // null = new
	const [confirmArchive, setConfirmArchive] = useState(null);   // snippet to archive
	const [busyRowId, setBusyRowId] = useState(null);             // snippet id whose run is being triggered
	const [openingDetailFor, setOpeningDetailFor] = useState(null); // snippet id whose row is fading out
	const [showSkeleton, setShowSkeleton] = useState(true);

	const [snippets, setSnippets] = useState([]);
	const [loading, setLoading] = useState(false);
	const [searchTerm, setSearchTerm] = useState('');
	const [page, setPage] = useState(1);
	const [pageSize] = useState(10);
	const [totalRecords, setTotalRecords] = useState(0);
	const [totalPages, setTotalPages] = useState(1);

	const fetchSnippets = useCallback(async () => {
		setLoading(true);
		try {
			const qs = new URLSearchParams({
				page: String(page),
				page_size: String(pageSize),
			});
			if (searchTerm) qs.set('search', searchTerm);
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/code-execution/snippets/?${qs.toString()}`,
				type: 'GET',
				loader: false,
			});
			if (success && response?.snippets) {
				setSnippets(response.snippets.records || []);
				setTotalRecords(response.snippets.total_records || 0);
				setTotalPages(response.snippets.total_pages || 1);
			}
		} catch (e) {
			console.error('codexec list fetch failed', e);
		} finally {
			setLoading(false);
			setShowSkeleton(false);
		}
	}, [appId, page, pageSize, searchTerm, triggerApi]);

	useEffect(() => { fetchSnippets(); }, [fetchSnippets]);

	// Poll while any row is in flight.
	const anyInFlight = useMemo(
		() => snippets.some((s) => s.last_status === 'queued' || s.last_status === 'running'),
		[snippets],
	);
	useEffect(() => {
		if (!anyInFlight) return;
		const t = setInterval(fetchSnippets, 5000);
		return () => clearInterval(t);
	}, [anyInFlight, fetchSnippets]);

	const openNew = () => { setEditingSnippet(null); setEditorOpen(true); };

	const openEdit = async (snippet) => {
		// Fetch the full snippet with code body
		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/code-execution/snippets/${snippet.id}/`,
			type: 'GET',
			loader: false,
		});
		if (success && response?.snippet) {
			setEditingSnippet(response.snippet);
			setEditorOpen(true);
		}
	};

	const handleRun = async (snippetId) => {
		setBusyRowId(snippetId);
		try {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/code-execution/snippets/${snippetId}/run/`,
				type: 'POST',
				payload: { trigger_kind: 'ui_run' },
				loader: false,
				showErrorModal: false,
			});
			if (success && response?.execution) {
				toast.success('Run queued');
				fetchSnippets();
				// Brief fade before swapping views.
				setOpeningDetailFor(snippetId);
				setTimeout(() => {
					setActiveExecutionId(response.execution.id);
					setView('detail');
					setOpeningDetailFor(null);
				}, 220);
			} else if (response?.violations) {
				toast.error('Code has validation errors — open editor to fix.');
			} else if (response?.execution_id) {
				toast(`Another run is in flight (id ${response.execution_id.slice(0, 8)}…)`);
			} else {
				toast.error(response?.message || 'Run failed.');
			}
		} catch (e) {
			toast.error('Run failed.');
		} finally {
			setBusyRowId(null);
		}
	};

	const askArchive = (snippet) => setConfirmArchive(snippet);

	const confirmedArchive = async () => {
		const snippetId = confirmArchive?.id;
		setConfirmArchive(null);
		if (!snippetId) return;
		const { success } = await triggerApi({
			url: `/api/v1/apps/${appId}/code-execution/snippets/${snippetId}/archive/`,
			type: 'POST',
			payload: {},
			loader: false,
		});
		if (success) {
			toast.success('Archived');
			fetchSnippets();
		}
	};

	const openLatestRun = async (snippet) => {
		setOpeningDetailFor(snippet.id);
		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/code-execution/executions/?snippet_id=${snippet.id}&page=1&page_size=1`,
			type: 'GET',
			loader: false,
		});
		const exec = response?.executions?.records?.[0];
		if (success && exec) {
			// Smooth swap with a brief fade.
			setTimeout(() => {
				setActiveExecutionId(exec.id);
				setView('detail');
				setOpeningDetailFor(null);
			}, 180);
		} else {
			setOpeningDetailFor(null);
			toast('No runs yet for this snippet.');
		}
	};

	if (view === 'detail' && activeExecutionId) {
		return (
			<ExecutionDetail
				appId={appId}
				executionId={activeExecutionId}
				onBack={() => { setView('list'); setActiveExecutionId(null); fetchSnippets(); }}
				onSelectExecution={(id) => setActiveExecutionId(id)}
				onEditSnippet={(snippetId) => {
					// Fetch the snippet then open the editor
					triggerApi({
						url: `/api/v1/apps/${appId}/code-execution/snippets/${snippetId}/`,
						type: 'GET',
						loader: false,
					}).then(({ response, success }) => {
						if (success && response?.snippet) {
							setEditingSnippet(response.snippet);
							setEditorOpen(true);
							setView('list');
						}
					});
				}}
			/>
		);
	}

	return (
		<div className="flex flex-col gap-6 pb-24">
			<style>{`
				@keyframes codexecFadeUp {
					from { opacity: 0; transform: translateY(6px); }
					to   { opacity: 1; transform: translateY(0); }
				}
				.codexec-row {
					animation: codexecFadeUp 280ms cubic-bezier(0.22, 1, 0.36, 1) both;
				}
			`}</style>
			{/* Header */}
			<div className="flex items-end justify-between">
				<div>
					<div className="text-[10.5px] font-semibold uppercase tracking-[0.08em] text-slate-500 mb-1">
						Code · Code Execution
					</div>
					<h2 className="text-[20px] font-bold text-slate-900 leading-tight tracking-tight">
						Code Execution
					</h2>
					<p className="text-[12.5px] text-slate-500 mt-1">
						Run ad-hoc Python snippets inside this tenant's workspace. All runs are logged.
					</p>
				</div>
				<button
					onClick={openNew}
					className="inline-flex items-center gap-1.5 h-9 px-3.5 rounded-md bg-[#346BD4] text-white text-[12.5px] font-medium shadow-sm hover:bg-[#2557C0] hover:shadow transition-all active:scale-[0.98]"
				>
					<span className="text-base leading-none">+</span> Add New
				</button>
			</div>

			{/* Filter bar */}
			<div className="flex gap-2 items-center">
				<div className="flex-1 flex items-center gap-2 bg-white border border-slate-200 rounded-md px-3 py-1.5">
					<svg width="14" height="14" viewBox="0 0 16 16" fill="none">
						<circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.5" />
						<path d="M11 11l3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
					</svg>
					<input
						value={searchTerm}
						onChange={(e) => { setSearchTerm(e.target.value); setPage(1); }}
						placeholder="Search snippets by name…"
						className="flex-1 text-[12.5px] outline-none placeholder:text-slate-400"
					/>
				</div>
			</div>

			{/* Table */}
			<div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
				<table className="w-full">
					<thead>
						<tr className="bg-slate-50 border-b border-slate-200">
							<th className="text-left px-4 py-2.5 text-[10.5px] font-semibold uppercase tracking-[0.07em] text-slate-500" style={{ width: '34%' }}>Snippet</th>
							<th className="text-left px-4 py-2.5 text-[10.5px] font-semibold uppercase tracking-[0.07em] text-slate-500">Last status</th>
							<th className="text-left px-4 py-2.5 text-[10.5px] font-semibold uppercase tracking-[0.07em] text-slate-500">Last run</th>
							<th className="text-left px-4 py-2.5 text-[10.5px] font-semibold uppercase tracking-[0.07em] text-slate-500">Runs</th>
							<th className="text-left px-4 py-2.5 text-[10.5px] font-semibold uppercase tracking-[0.07em] text-slate-500">Updated by</th>
							<th className="text-right px-4 py-2.5 text-[10.5px] font-semibold uppercase tracking-[0.07em] text-slate-500">Actions</th>
						</tr>
					</thead>
					<tbody>
						{loading && snippets.length === 0 && (
							<tr><td colSpan={6} className="text-center text-slate-400 py-12 text-sm">Loading…</td></tr>
						)}
						{!loading && snippets.length === 0 && (
							<tr>
								<td colSpan={6} className="text-center py-16">
									<div className="text-slate-400 text-sm mb-1">No snippets yet.</div>
									<button onClick={openNew} className="text-[13px] text-[#346BD4] font-medium hover:underline">
										Create your first snippet
									</button>
								</td>
							</tr>
						)}
						{snippets.map((s, idx) => (
							<tr
								key={s.id}
								onClick={() => openLatestRun(s)}
								className="codexec-row border-b border-slate-100 last:border-0 hover:bg-slate-50 cursor-pointer transition-colors"
								style={{ animationDelay: `${Math.min(idx * 30, 240)}ms` }}
							>
								<td className="px-4 py-3 align-middle">
									<div className="flex items-center gap-2.5">
										<div className="w-6 h-6 bg-indigo-50 text-indigo-600 rounded-md grid place-items-center font-mono text-[10px] font-semibold">py</div>
										<div>
											<div className="text-[13px] font-medium text-slate-900">{s.name}</div>
											<div className="text-[11px] text-slate-400 font-mono mt-0.5">
												{s.slug} · v{s.version}
											</div>
										</div>
									</div>
								</td>
								<td className="px-4 py-3">
									{s.last_status ? <StatusPill status={s.last_status} /> : <span className="text-slate-300 text-xs">—</span>}
								</td>
								<td className="px-4 py-3 text-[12.5px] text-slate-600">
									{formatRelative(s.last_run_at)}
									{s.last_run_duration_ms != null && (
										<span className="font-mono text-slate-400 ml-1.5">· {formatDuration(s.last_run_duration_ms)}</span>
									)}
								</td>
								<td className="px-4 py-3 text-[12.5px] text-slate-700 font-mono">{s.run_count ?? 0}</td>
								<td className="px-4 py-3 text-[12.5px] text-slate-600">{s.modified_by || '—'}</td>
								<td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
									<div className="flex gap-1 justify-end">
										<button
											onClick={() => handleRun(s.id)}
											title="Run"
											className="w-7 h-7 rounded grid place-items-center text-emerald-600 hover:bg-emerald-50 hover:border hover:border-emerald-200 transition-colors"
										>
											<span style={{ fontSize: 11 }}>▸</span>
										</button>
										<button
											onClick={() => openEdit(s)}
											title="Edit"
											className="w-7 h-7 rounded grid place-items-center text-slate-500 hover:bg-slate-100 transition-colors"
										>
											<svg width="12" height="12" viewBox="0 0 16 16" fill="none">
												<path d="M11.5 1.5L14.5 4.5L5 14H2V11L11.5 1.5Z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" />
											</svg>
										</button>
										<button
											onClick={() => askArchive(s)}
											title="Archive"
											className="w-7 h-7 rounded grid place-items-center text-slate-500 hover:bg-rose-50 hover:text-rose-600 transition-colors"
										>
											<svg width="12" height="12" viewBox="0 0 16 16" fill="none">
												<path d="M2 5H14M6 8V12M10 8V12M3 5L4 14H12L13 5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
											</svg>
										</button>
									</div>
								</td>
							</tr>
						))}
					</tbody>
				</table>
			</div>

			{/* Pagination — always visible so users can see paging exists */}
			<div className="flex items-center justify-between text-[12.5px] text-slate-500">
				<div>
					{totalRecords} snippet{totalRecords === 1 ? '' : 's'}
					<span className="text-slate-400 ml-2">· page {page} of {Math.max(1, totalPages)}</span>
				</div>
				<div className="flex gap-2">
					<button
						disabled={page === 1 || loading}
						onClick={() => setPage((p) => Math.max(1, p - 1))}
						className="px-3 py-1.5 border border-slate-200 rounded font-medium text-slate-700 bg-white hover:border-slate-400 disabled:opacity-40 transition-colors"
					>
						← Prev
					</button>
					<button
						disabled={page >= totalPages || loading}
						onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
						className="px-3 py-1.5 border border-slate-200 rounded font-medium text-slate-700 bg-white hover:border-slate-400 disabled:opacity-40 transition-colors"
					>
						Next →
					</button>
				</div>
			</div>

			{/* Editor modal */}
			{editorOpen && (
				<EditorModal
					appId={appId}
					snippet={editingSnippet}
					onClose={() => { setEditorOpen(false); setEditingSnippet(null); }}
					onSaved={(s, openRun) => {
						setEditorOpen(false);
						setEditingSnippet(null);
						fetchSnippets();
						if (openRun && s) {
							handleRun(s.id);
						}
					}}
				/>
			)}

			<ConfirmModal
				open={Boolean(confirmArchive)}
				title="Archive this snippet?"
				description={confirmArchive
					? `"${confirmArchive.name}" will be hidden from the list. Past run history is preserved.`
					: ''}
				confirmLabel="Archive"
				confirmTone="danger"
				onCancel={() => setConfirmArchive(null)}
				onConfirm={confirmedArchive}
			/>
		</div>
	);
}
