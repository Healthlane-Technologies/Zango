import React, { useEffect, useRef, useState, useCallback } from 'react';
import toast from 'react-hot-toast';
import useApi from '../../../../hooks/useApi';
import ConfirmModal from './ConfirmModal';
import RunConfirmModal from './RunConfirmModal';

const STATUS = {
	success:  { bg: 'bg-emerald-50', text: 'text-emerald-700', dot: 'bg-emerald-500', label: 'Success' },
	failed:   { bg: 'bg-rose-50',    text: 'text-rose-700',    dot: 'bg-rose-500',    label: 'Failed' },
	running:  { bg: 'bg-amber-50',   text: 'text-amber-700',   dot: 'bg-amber-500',   label: 'Running' },
	queued:   { bg: 'bg-slate-100',  text: 'text-slate-700',   dot: 'bg-slate-400',   label: 'Queued' },
	timeout:  { bg: 'bg-rose-50',    text: 'text-rose-700',    dot: 'bg-rose-500',    label: 'Timed out' },
	aborted:  { bg: 'bg-slate-100',  text: 'text-slate-700',   dot: 'bg-slate-500',   label: 'Aborted' },
};

function StatusPill({ status }) {
	const s = STATUS[status] || STATUS.queued;
	const anim = status === 'running' || status === 'queued';
	return (
		<span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${s.bg} ${s.text}`}>
			<span className={`w-1.5 h-1.5 rounded-full ${s.dot} ${anim ? 'animate-pulse' : ''}`}></span>
			{s.label}
		</span>
	);
}

function formatBytes(n) {
	if (n == null) return '—';
	if (n < 1024) return `${n} B`;
	if (n < 1024 * 1024) return `${(n / 1024).toFixed(0)} KB`;
	return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

function formatDuration(ms) {
	if (ms == null) return '—';
	if (ms < 1000) return `${ms} ms`;
	return `${(ms / 1000).toFixed(1)} s`;
}

function formatRelative(ts) {
	if (!ts) return '—';
	const diff = Date.now() - new Date(ts).getTime();
	if (diff < 60_000) return 'just now';
	if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
	if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
	return new Date(ts).toLocaleDateString();
}

function extOf(name) {
	const i = (name || '').lastIndexOf('.');
	return i === -1 ? '' : name.substring(i + 1).slice(0, 4);
}

export default function ExecutionDetail({ appId, executionId, onBack, onEditSnippet, onSelectExecution, onRunCurrent, onRunVersion }) {
	const triggerApi = useApi();
	const [execution, setExecution] = useState(null);
	const [tab, setTab] = useState('logs');
	const [loading, setLoading] = useState(true);
	// Log lines arrive in batches once the run commits (no live streaming today).
	// Initial load: latest 100 lines (before_seq=huge). Forward polling catches
	// late-arriving lines after the run commits. "Load earlier" prepends older
	// batches via before_seq=oldest.
	const [logLines, setLogLines] = useState([]);
	const [logStatus, setLogStatus] = useState(null);
	const [logTotal, setLogTotal] = useState(0);
	const [hasOlderLogs, setHasOlderLogs] = useState(false);
	const [loadingOlder, setLoadingOlder] = useState(false);
	const nextSeqRef = useRef(0);
	const oldestSeqRef = useRef(null);

	const fetchExecution = useCallback(async () => {
		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/code-execution/executions/${executionId}/`,
			type: 'GET',
			loader: false,
		});
		if (success && response?.execution) {
			setExecution(response.execution);
		}
		setLoading(false);
	}, [appId, executionId, triggerApi]);

	// Initial load: most-recent 100 lines via the backward-page endpoint.
	const fetchLogsInitial = useCallback(async () => {
		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/code-execution/executions/${executionId}/log-tail/?before_seq=999999999&limit=100`,
			type: 'GET',
			loader: false,
		});
		if (success && response) {
			const lines = response.lines || [];
			setLogLines(lines);
			oldestSeqRef.current = response.oldest_seq;
			nextSeqRef.current = response.newest_seq || 0;
			setLogTotal(response.total || 0);
			setHasOlderLogs(Boolean(response.has_more_before));
			setLogStatus(response.status);
			return response.is_terminal;
		}
		return false;
	}, [appId, executionId, triggerApi]);

	// Forward incremental poll — appends lines with seq > nextSeqRef.
	const fetchLogTail = useCallback(async () => {
		const after = nextSeqRef.current;
		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/code-execution/executions/${executionId}/log-tail/?after_seq=${after}&limit=200`,
			type: 'GET',
			loader: false,
		});
		if (success && response) {
			if ((response.lines || []).length) {
				setLogLines((prev) => [...prev, ...response.lines]);
				nextSeqRef.current = response.newest_seq ?? response.next_seq;
				if (oldestSeqRef.current == null) oldestSeqRef.current = response.oldest_seq;
				setLogTotal(response.total || 0);
			}
			setLogStatus(response.status);
			return response.is_terminal;
		}
		return false;
	}, [appId, executionId, triggerApi]);

	// "Load earlier" — prepend older lines via before_seq=<currentOldest>.
	const loadEarlierLogs = useCallback(async () => {
		if (loadingOlder || oldestSeqRef.current == null || oldestSeqRef.current <= 1) return;
		setLoadingOlder(true);
		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/code-execution/executions/${executionId}/log-tail/?before_seq=${oldestSeqRef.current}&limit=100`,
			type: 'GET',
			loader: false,
		});
		if (success && response?.lines) {
			setLogLines((prev) => [...response.lines, ...prev]);
			if (response.oldest_seq != null) oldestSeqRef.current = response.oldest_seq;
			setHasOlderLogs(Boolean(response.has_more_before));
		}
		setLoadingOlder(false);
	}, [appId, executionId, loadingOlder, triggerApi]);

	useEffect(() => {
		// Reset log state when execution id changes.
		nextSeqRef.current = 0;
		oldestSeqRef.current = null;
		setLogLines([]);
		setLogStatus(null);
		setLogTotal(0);
		setHasOlderLogs(false);
		fetchExecution();
		fetchLogsInitial();
	}, [executionId]); // eslint-disable-line react-hooks/exhaustive-deps

	// Poll while in flight — log-tail every 1s, execution metadata every 3s.
	useEffect(() => {
		const status = logStatus || execution?.status;
		const inFlight = status === 'queued' || status === 'running';
		if (!inFlight) return;
		const tailTimer = setInterval(async () => {
			const terminal = await fetchLogTail();
			if (terminal) fetchExecution();
		}, 1000);
		const metaTimer = setInterval(fetchExecution, 3000);
		return () => { clearInterval(tailTimer); clearInterval(metaTimer); };
	}, [logStatus, execution?.status, fetchLogTail, fetchExecution]);

	const [confirmingAbort, setConfirmingAbort] = useState(false);
	// Run confirmation state — for both "Run latest" and "Re-run vN"
	const [runConfirm, setRunConfirm] = useState(null); // { mode, code, version, sourceHash, title, subtitle, payload }
	const [runConfirmLoading, setRunConfirmLoading] = useState(false);

	const askRunLatest = async () => {
		if (!execution?.snippet_object_uuid) return;
		setRunConfirmLoading(true);
		// Fetch the snippet's current code
		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/code-execution/snippets/${execution.snippet_object_uuid}/`,
			type: 'GET',
			loader: false,
			showErrorModal: false,
		});
		setRunConfirmLoading(false);
		if (success && response?.snippet) {
			const s = response.snippet;
			setRunConfirm({
				mode: 'latest',
				code: s.code,
				version: s.version,
				sourceHash: s.code_hash,
				title: 'Run latest code',
				subtitle: `${s.name} · current snippet code`,
			});
		} else {
			toast.error('Could not load the snippet code.');
		}
	};

	const askReRunThisVersion = () => {
		setRunConfirm({
			mode: 'this',
			code: execution.source_snapshot,
			version: execution.snippet_version,
			sourceHash: execution.source_hash,
			title: `Re-run v${execution.snippet_version}`,
			subtitle: `${execution.snippet_name} · code frozen on this run`,
		});
	};

	const askRunVersionFromTab = (version, sourceSnapshot, sourceHash, isCurrent) => {
		setRunConfirm({
			mode: isCurrent ? 'latest' : 'version',
			code: sourceSnapshot,
			version,
			sourceHash,
			title: isCurrent ? 'Run latest code' : `Re-run v${version}`,
			subtitle: `${execution.snippet_name}${isCurrent ? ' · current snippet code' : ` · v${version} frozen code`}`,
		});
	};

	const confirmedRun = async () => {
		if (!runConfirm) return;
		setRunConfirmLoading(true);
		try {
			if (runConfirm.mode === 'latest') {
				await onRunCurrent?.(execution.snippet_object_uuid);
			} else {
				await onRunVersion?.(execution.snippet_object_uuid, runConfirm.code, runConfirm.version);
			}
			setRunConfirm(null);
		} finally {
			setRunConfirmLoading(false);
		}
	};
	// Version history state
	const [versions, setVersions] = useState([]);
	const [versionsLoading, setVersionsLoading] = useState(false);
	const [expandedVersion, setExpandedVersion] = useState(null);

	const fetchVersions = useCallback(async () => {
		if (!execution?.snippet_object_uuid) return;
		setVersionsLoading(true);
		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/code-execution/snippets/${execution.snippet_object_uuid}/versions/`,
			type: 'GET',
			loader: false,
			showErrorModal: false,
		});
		if (success && response?.versions) {
			setVersions(response.versions);
		}
		setVersionsLoading(false);
	}, [appId, execution?.snippet_object_uuid, triggerApi]);
	const [history, setHistory] = useState([]);
	const [historyLoading, setHistoryLoading] = useState(false);
	const [historyTotalPages, setHistoryTotalPages] = useState(1);
	const [historyTotalRecords, setHistoryTotalRecords] = useState(0);
	const HISTORY_PAGE_SIZE = 15;
	const historyPageRef = useRef(1);
	const historyLoadingMoreRef = useRef(false);
	const historySentinelRef = useRef(null);

	// Fetch a specific page. mode='replace' clears the list first; 'append'
	// pushes onto the end (for infinite scroll).
	const fetchHistory = useCallback(async (mode = 'replace') => {
		if (!execution?.snippet_object_uuid) return;
		if (mode === 'append' && historyLoadingMoreRef.current) return;
		const targetPage = mode === 'replace' ? 1 : historyPageRef.current + 1;
		if (mode === 'append') historyLoadingMoreRef.current = true;
		setHistoryLoading(true);
		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/code-execution/executions/?snippet_uuid=${execution.snippet_object_uuid}&page=${targetPage}&page_size=${HISTORY_PAGE_SIZE}`,
			type: 'GET',
			loader: false,
		});
		if (success && response?.executions?.records) {
			const records = response.executions.records;
			if (mode === 'replace') {
				setHistory(records);
			} else {
				setHistory((prev) => {
					const seen = new Set(prev.map((r) => r.object_uuid));
					return [...prev, ...records.filter((r) => !seen.has(r.object_uuid))];
				});
			}
			setHistoryTotalPages(response.executions.total_pages || 1);
			setHistoryTotalRecords(response.executions.total_records || 0);
			historyPageRef.current = targetPage;
		}
		setHistoryLoading(false);
		if (mode === 'append') historyLoadingMoreRef.current = false;
	}, [appId, execution?.snippet_object_uuid, triggerApi]);

	const hasMoreHistory = historyPageRef.current < historyTotalPages;

	// IntersectionObserver — when the sentinel at the end of the runs list
	// becomes visible, auto-fetch the next page.
	useEffect(() => {
		if (!historySentinelRef.current) return;
		const sentinel = historySentinelRef.current;
		const io = new IntersectionObserver((entries) => {
			if (entries[0]?.isIntersecting && historyPageRef.current < historyTotalPages) {
				fetchHistory('append');
			}
		}, { root: sentinel.closest('.codexec-runs-scroll'), rootMargin: '120px' });
		io.observe(sentinel);
		return () => io.disconnect();
	}, [historyTotalPages, fetchHistory]);

	// Reset to page 1 whenever the snippet changes.
	useEffect(() => {
		historyPageRef.current = 1;
		setHistory([]);
		if (execution?.snippet_object_uuid) fetchHistory('replace');
	}, [execution?.snippet_object_uuid]); // eslint-disable-line react-hooks/exhaustive-deps

	// Auto-fetch the runs list as soon as we know the snippet id, and refresh
	// after the current run reaches a terminal state so durations show up.
	useEffect(() => { fetchHistory(); }, [execution?.snippet_object_uuid]); // eslint-disable-line react-hooks/exhaustive-deps
	useEffect(() => {
		if (execution?.status && !['queued', 'running'].includes(execution.status)) {
			fetchHistory();
		}
	}, [execution?.status]); // eslint-disable-line react-hooks/exhaustive-deps

	const askAbort = () => setConfirmingAbort(true);

	const confirmedAbort = async () => {
		setConfirmingAbort(false);
		const { success, response } = await triggerApi({
			url: `/api/v1/apps/${appId}/code-execution/executions/${executionId}/abort/`,
			type: 'POST',
			payload: {},
			loader: false,
		});
		if (success) {
			toast.success('Aborted');
			fetchExecution();
			fetchLogTail();
		} else {
			toast.error(response?.message || 'Abort failed.');
		}
	};

	if (loading) return <div className="text-slate-400 text-sm p-8">Loading run…</div>;
	if (!execution) return <div className="text-rose-500 text-sm p-8">Execution not found.</div>;

	const inputs = (execution.files || []).filter((f) => f.kind === 'input');
	const outputs = (execution.files || []).filter((f) => f.kind === 'output');
	const tabs = [
		{ id: 'logs', label: 'Logs', count: null },
		{ id: 'return', label: 'Return value', count: null },
		{ id: 'files', label: 'Files', count: `${inputs.length} + ${outputs.length}` },
		{ id: 'source', label: 'Source at run', count: null },
		{ id: 'versions', label: 'Versions', count: versions.length || null },
		{ id: 'meta', label: 'Metadata', count: null },
	];

	// Files come back with a `download_url` already — for S3 it's a presigned
	// URL with ResponseContentDisposition so the browser saves with the
	// original filename. We fall back to our backend redirect if the serializer
	// couldn't produce one (e.g., misconfigured storage).
	const downloadUrl = (f) =>
		f.download_url
		|| `/api/v1/apps/${appId}/code-execution/executions/${execution.object_uuid}/files/${f.object_uuid}/download/`;

	return (
		<div className="flex flex-col pb-24">
			<style>{`
				@keyframes codexecFadeIn {
					from { opacity: 0; transform: translateY(4px); }
					to   { opacity: 1; transform: translateY(0); }
				}
				@keyframes codexecSlideInRight {
					from { opacity: 0; transform: translateX(8px); }
					to   { opacity: 1; transform: translateX(0); }
				}
				@keyframes codexecVersionRowIn {
					from { opacity: 0; transform: translateY(4px) scale(0.99); }
					to   { opacity: 1; transform: translateY(0) scale(1); }
				}
				.codexec-tab-content { animation: codexecFadeIn 260ms cubic-bezier(0.22, 1, 0.36, 1) both; }
				.codexec-side-row { transition: all 180ms cubic-bezier(0.22, 1, 0.36, 1); }
				.codexec-side-row:hover { transform: translateX(2px); }
				.codexec-version-row { animation: codexecVersionRowIn 280ms cubic-bezier(0.22, 1, 0.36, 1) both; }
				.codexec-pill { transition: all 200ms cubic-bezier(0.22, 1, 0.36, 1); }
			`}</style>
			{/* Top */}
			<div className="px-7 py-5 border-b border-slate-200 bg-gradient-to-b from-slate-50/50 to-white">
				<div className="text-[10.5px] font-semibold uppercase tracking-[0.07em] text-slate-500 mb-1">
					<button onClick={onBack} className="hover:text-slate-700">Code Execution</button>
					<span className="text-slate-300 px-1.5">/</span>
					<button onClick={onBack} className="hover:text-slate-700">{execution.snippet_name}</button>
					<span className="text-slate-300 px-1.5">/</span>
					<span className="text-slate-900">Run {execution.object_uuid.slice(0, 6)}</span>
				</div>
				<div className="flex items-center justify-between">
					<div className="flex items-center gap-2.5">
						<div className="w-7 h-7 bg-indigo-50 text-indigo-600 rounded-md grid place-items-center font-mono text-[12px] font-semibold">py</div>
						<div className="text-[20px] font-bold text-slate-900 leading-tight tracking-tight">{execution.snippet_name}</div>
						<div className="ml-3"><StatusPill status={execution.status} /></div>
					</div>
					<div className="flex gap-2">
						<button
							onClick={onBack}
							className="px-3 h-9 rounded-md text-[12.5px] font-medium bg-white border border-slate-300 text-slate-800 hover:border-slate-400 hover:shadow-sm transition-all active:scale-[0.98]"
						>
							← Back
						</button>
						<button
							onClick={() => onEditSnippet?.(execution.snippet_object_uuid)}
							title="Edit the snippet's current (latest) code"
							className="px-3 h-9 rounded-md text-[12.5px] font-medium bg-white border border-slate-300 text-slate-800 hover:border-slate-400 hover:shadow-sm transition-all active:scale-[0.98]"
						>
							✎ Edit latest
						</button>
						<button
							onClick={askReRunThisVersion}
							title={`Re-run the exact code that this run executed (v${execution.snippet_version})`}
							className="px-3 h-9 rounded-md text-[12.5px] font-medium bg-white border border-emerald-300 text-emerald-700 hover:bg-emerald-50 hover:shadow-sm transition-all active:scale-[0.98] inline-flex items-center gap-1.5"
						>
							<span style={{ fontSize: 10 }}>↻</span> Re-run v{execution.snippet_version}
						</button>
						<button
							onClick={askRunLatest}
							disabled={runConfirmLoading}
							title="Run the snippet's current code (latest version)"
							className="px-3 h-9 rounded-md text-[12.5px] font-medium bg-emerald-600 text-white shadow-sm hover:bg-emerald-700 hover:shadow disabled:opacity-50 transition-all active:scale-[0.98] inline-flex items-center gap-1.5"
						>
							<span style={{ fontSize: 10 }}>▸</span> Run latest
						</button>
						{(execution.status === 'queued' || execution.status === 'running') && (
							<button
								onClick={askAbort}
								className="px-3 h-9 rounded-md text-[12.5px] font-medium bg-slate-900 text-white hover:bg-slate-800 hover:shadow transition-all active:scale-[0.98]"
							>
								⊗ Abort
							</button>
						)}
					</div>
				</div>

				<div className="grid grid-cols-5 gap-px bg-slate-200 border border-slate-200 rounded-md overflow-hidden mt-4">
					<div className="bg-white px-3.5 py-2.5">
						<div className="text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-500 mb-1">Run ID</div>
						<div className="text-[12px] font-mono text-slate-900">{execution.object_uuid.slice(0, 8)}</div>
					</div>
					<div className="bg-white px-3.5 py-2.5">
						<div className="text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-500 mb-1">Started</div>
						<div className="text-[13px] text-slate-900">{execution.started_at ? new Date(execution.started_at).toLocaleString() : '—'}</div>
					</div>
					<div className="bg-white px-3.5 py-2.5">
						<div className="text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-500 mb-1">Duration</div>
						<div className="text-[13px] text-slate-900 font-mono">{formatDuration(execution.duration_ms)}</div>
					</div>
					<div className="bg-white px-3.5 py-2.5">
						<div className="text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-500 mb-1">Triggered by</div>
						<div className="text-[13px] text-slate-900">{execution.triggered_by || '—'}</div>
					</div>
					<div className="bg-white px-3.5 py-2.5">
						<div className="text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-500 mb-1">Version</div>
						<div className="text-[13px] text-slate-900 font-mono">v{execution.snippet_version} · {(execution.source_hash || '').slice(0, 6)}</div>
					</div>
				</div>
			</div>

			{/* Two-column body: sidebar of runs (left) + tabs/content (right) */}
			<div className="grid" style={{ gridTemplateColumns: '280px minmax(0, 1fr)' }}>

				{/* === Sidebar: runs list (always visible) === */}
				<aside className="border-r border-slate-200 bg-slate-50/40 min-h-[480px] flex flex-col">
					<div className="px-4 py-3 border-b border-slate-200 flex items-center justify-between">
						<div>
							<div className="text-[10.5px] font-semibold uppercase tracking-[0.08em] text-slate-500">All runs</div>
							<div className="text-[12px] text-slate-700 mt-0.5">
								{history.length} shown
								{historyTotalRecords > history.length && (
									<span className="text-slate-400"> of {historyTotalRecords}</span>
								)}
							</div>
						</div>
						<button
							onClick={() => { historyPageRef.current = 1; fetchHistory('replace'); }}
							title="Refresh"
							className="w-7 h-7 grid place-items-center rounded text-slate-400 hover:bg-slate-200 hover:text-slate-700 transition-colors"
						>
							<span style={{ fontSize: 13 }}>↻</span>
						</button>
					</div>
					<div className="overflow-y-auto flex-1 codexec-runs-scroll" style={{ maxHeight: 'calc(100vh - 340px)' }}>
						{historyLoading && history.length === 0 && (
							<div className="text-center text-slate-400 py-6 text-[12px]">Loading…</div>
						)}
						{!historyLoading && history.length === 0 && (
							<div className="text-center text-slate-400 py-6 text-[12px]">No runs yet.</div>
						)}
						{history.map((r) => {
							const isCurrent = r.object_uuid === execution.object_uuid;
							return (
								<button
									key={r.object_uuid}
									onClick={() => { if (!isCurrent) onSelectExecution?.(r.object_uuid); }}
									className={`codexec-side-row block w-full text-left px-4 py-3 border-b border-slate-200/70 last:border-0 ${
										isCurrent
											? 'bg-indigo-50 border-l-2 border-l-indigo-600 -ml-px'
											: 'hover:bg-slate-100 border-l-2 border-l-transparent -ml-px'
									}`}
								>
									<div className="flex items-center justify-between mb-1">
										<StatusPill status={r.status} />
										<span className="font-mono text-[10.5px] text-slate-400">{r.object_uuid.slice(0, 6)}</span>
									</div>
									<div className="text-[12px] text-slate-700 truncate">
										{formatRelative(r.queued_at)}
										<span className="text-slate-400 font-mono ml-1.5">· {formatDuration(r.duration_ms)}</span>
									</div>
									<div className="text-[10.5px] text-slate-400 mt-0.5 truncate">
										{r.triggered_by || '—'} · v{r.snippet_version}
									</div>
								</button>
							);
						})}
						{/* Infinite-scroll sentinel: when this scrolls into view, fetch next page. */}
						{hasMoreHistory && (
							<div ref={historySentinelRef} className="py-3 text-center text-[11px] text-slate-400">
								{historyLoading ? 'Loading more…' : '↓ Scroll for more'}
							</div>
						)}
						{!hasMoreHistory && history.length > 0 && (
							<div className="py-3 text-center text-[11px] text-slate-300">— end of history —</div>
						)}
					</div>
				</aside>

				{/* === Right side: tabs + content === */}
				<div className="min-w-0 flex flex-col">
			{/* Tabs */}
			<div className="px-7 border-b border-slate-200 bg-white">
				<div className="flex gap-0 items-center">
					{tabs.map((t) => (
						<button
							key={t.id}
							onClick={() => { setTab(t.id); if (t.id === 'versions' && versions.length === 0) fetchVersions(); }}
							className={`py-2.5 mr-6 text-[12.5px] font-medium border-b-2 flex items-center gap-1.5 transition-colors ${
								tab === t.id ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-600 hover:text-slate-900'
							}`}
						>
							{t.label}
							{t.count && <span className={`px-1.5 py-0.5 rounded-full text-[10.5px] font-mono ${tab === t.id ? 'bg-indigo-50 text-indigo-600' : 'bg-slate-100 text-slate-500'}`}>{t.count}</span>}
						</button>
					))}
				</div>
			</div>

			{/* Tab content */}
			<div key={tab} className="px-7 py-5 codexec-tab-content">
				{tab === 'logs' && (
					<div>
						<div className="flex items-center justify-between mb-3 text-[12px] text-slate-600">
							<div className="flex items-center gap-2">
								<span className="font-semibold text-slate-700">Log lines</span>
								<span className="text-slate-400">
									{logLines.length} shown
									{logTotal > logLines.length && <span> of {logTotal}</span>}
								</span>
							</div>
							{(execution.status === 'queued' || execution.status === 'running') && (
								<span className="inline-flex items-center gap-1.5 text-amber-600 font-medium" title="Logs commit when the run finishes — polling for completion">
									<span className="w-1.5 h-1.5 bg-amber-500 rounded-full animate-pulse"></span> Run in progress · checking every 1s
								</span>
							)}
						</div>
						<div className="bg-[#0F1117] text-slate-200 rounded-md p-3.5 font-mono text-[12px] overflow-auto" style={{ maxHeight: 420 }}>
							{hasOlderLogs && (
								<div className="text-center mb-2">
									<button
										onClick={loadEarlierLogs}
										disabled={loadingOlder}
										className="px-3 py-1 text-[11px] bg-slate-800 text-slate-200 rounded hover:bg-slate-700 disabled:opacity-50 transition-colors"
									>
										{loadingOlder ? 'Loading…' : '↑ Load earlier'}
									</button>
								</div>
							)}
							{logLines.length === 0 && !execution.stdout && !execution.stderr ? (
								<div className="text-slate-500">(no output yet)</div>
							) : logLines.length === 0 ? (
								<pre className="whitespace-pre-wrap text-emerald-300">{execution.stdout}{execution.stderr ? '\n\n' + execution.stderr : ''}</pre>
							) : (
								<div className="leading-[1.6]">
									{logLines.map((l) => {
										const color =
											l.level === 'err' ? 'text-rose-300' :
											l.level === 'warn' ? 'text-amber-300' :
											l.level === 'info' ? 'text-sky-300' :
											l.level === 'sys' ? 'text-violet-300 italic' :
											'text-emerald-300';
										const lvlLabel = (l.level || 'out').toUpperCase().padEnd(4);
										return (
											<div key={l.seq} className="grid items-baseline gap-3" style={{ gridTemplateColumns: '90px 40px 1fr' }}>
												<span className="text-slate-500 text-[11px]">{(l.ts || '').slice(11, 23)}</span>
												<span className={`text-[10.5px] font-semibold ${color}`}>{lvlLabel}</span>
												<span className={`whitespace-pre-wrap ${color}`}>{l.message}</span>
											</div>
										);
									})}
								</div>
							)}
						</div>
						{(execution.exception_type || execution.exception_message) && (
							(() => {
								const isSuspended = execution.exception_type === 'TenantSuspended';
								const palette = isSuspended
									? {
											labelColor: 'text-amber-800',
											boxBg: 'bg-amber-50',
											boxBorder: 'border-amber-200',
											boxText: 'text-amber-900',
											label: 'App suspended',
									  }
									: {
											labelColor: 'text-rose-700',
											boxBg: 'bg-rose-50',
											boxBorder: 'border-rose-200',
											boxText: 'text-rose-800',
											label: 'Reason',
									  };
								return (
									<>
										<div className={`mt-4 mb-2 text-[12px] font-semibold ${palette.labelColor}`}>
											{palette.label}
										</div>
										<div className={`${palette.boxBg} border ${palette.boxBorder} rounded-md p-3.5 text-[12px] ${palette.boxText}`}>
											{execution.exception_type && (
												<div className="font-mono text-[11px] font-semibold mb-1.5">
													{execution.exception_type}
												</div>
											)}
											{execution.exception_message && (
												<div className="whitespace-pre-wrap">
													{execution.exception_message}
												</div>
											)}
										</div>
									</>
								);
							})()
						)}
						{execution.exception_traceback && (
							<>
								<div className="mt-4 mb-2 text-[12px] font-semibold text-rose-700">Traceback</div>
								<div className="bg-rose-50 border border-rose-200 rounded-md p-3.5 font-mono text-[11.5px] text-rose-800 overflow-auto" style={{ maxHeight: 240 }}>
									<pre className="whitespace-pre-wrap">{execution.exception_traceback}</pre>
								</div>
							</>
						)}
					</div>
				)}

				{tab === 'return' && (
					<div>
						{execution.return_value == null ? (
							<div className="text-slate-400 text-[13px]">No return value. (Set <code className="font-mono bg-slate-100 px-1.5 py-0.5 rounded text-[11px]">codexec_result</code> in your snippet to record one.)</div>
						) : (
							<>
								{execution.return_value_truncated && (
									<div className="mb-2 text-[12px] text-amber-700 bg-amber-50 border border-amber-200 px-3 py-2 rounded">Truncated — value exceeded 64 KB.</div>
								)}
								<pre className="bg-slate-50 border border-slate-200 rounded-md p-3.5 font-mono text-[12px] text-slate-800 whitespace-pre-wrap">
									{JSON.stringify(execution.return_value, null, 2)}
								</pre>
							</>
						)}
					</div>
				)}

				{tab === 'files' && (
					<div className="grid grid-cols-2 gap-4">
						<div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
							<div className="px-4 py-3 border-b border-slate-200 bg-slate-50">
								<div className="text-[13px] font-semibold text-slate-900 flex items-center gap-2">
									<span className="w-1.5 h-1.5 bg-indigo-500 rounded-full"></span>
									Inputs <span className="text-slate-500 font-normal">· {inputs.length}</span>
								</div>
								<div className="text-[11.5px] text-slate-500 mt-0.5">Snapshotted from snippet at run trigger</div>
							</div>
							<div className="px-3 py-2">
								{inputs.length === 0 ? <div className="text-[12px] text-slate-400 py-2 text-center">(none)</div> : inputs.map((f) => (
									<div key={f.object_uuid} className="grid items-center gap-2 py-1.5" style={{ gridTemplateColumns: '22px 1fr auto auto' }}>
										<span className="w-[22px] h-[22px] bg-slate-100 text-slate-500 rounded font-mono text-[9.5px] uppercase font-semibold grid place-items-center">{extOf(f.name)}</span>
										<span className="text-[12.5px] text-slate-900">{f.name}</span>
										<span className="font-mono text-[11px] text-slate-500">{formatBytes(f.size_bytes)}</span>
										<a href={downloadUrl(f)} target="_blank" rel="noopener noreferrer" className="text-[11px] text-indigo-600 font-medium">⤓ Download</a>
									</div>
								))}
							</div>
						</div>

						<div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
							<div className="px-4 py-3 border-b border-slate-200 bg-emerald-50/50">
								<div className="text-[13px] font-semibold text-slate-900 flex items-center gap-2">
									<span className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></span>
									Outputs <span className="text-slate-500 font-normal">· {outputs.length}</span>
								</div>
								<div className="text-[11.5px] text-slate-500 mt-0.5">Auto-registered via <code className="font-mono">codexec.write(...)</code></div>
							</div>
							<div className="px-3 py-2">
								{outputs.length === 0 ? <div className="text-[12px] text-slate-400 py-2 text-center">(none)</div> : outputs.map((f) => (
									<div key={f.object_uuid} className="grid items-center gap-2 py-1.5" style={{ gridTemplateColumns: '22px 1fr auto auto' }}>
										<span className="w-[22px] h-[22px] bg-emerald-100 text-emerald-700 rounded font-mono text-[9.5px] uppercase font-semibold grid place-items-center">{extOf(f.name)}</span>
										<span className="text-[12.5px] text-slate-900">{f.name}</span>
										<span className="font-mono text-[11px] text-slate-500">{formatBytes(f.size_bytes)}</span>
										<a href={downloadUrl(f)} target="_blank" rel="noopener noreferrer" className="text-[11px] text-emerald-700 font-medium">⤓ Download</a>
									</div>
								))}
							</div>
						</div>
					</div>
				)}

				{tab === 'source' && (
					<div>
						<div className="mb-2 text-[12px] text-slate-600">
							v{execution.snippet_version} · <span className="font-mono">{execution.source_hash}</span>
						</div>
						<pre className="bg-[#0F1117] text-slate-200 rounded-md p-3.5 font-mono text-[12px] overflow-auto whitespace-pre" style={{ maxHeight: 480 }}>
							{execution.source_snapshot}
						</pre>
					</div>
				)}

				{tab === 'versions' && (
					<div>
						<div className="flex items-center justify-between mb-3">
							<div className="text-[13px] text-slate-700">
								Versions of <span className="font-semibold">{execution.snippet_name}</span> that have been run
								<span className="text-slate-400 font-mono ml-2">· {versions.length} total</span>
							</div>
							<button
								onClick={fetchVersions}
								className="text-[12px] text-slate-500 hover:text-slate-800 transition-colors"
							>
								↻ Refresh
							</button>
						</div>
						{versionsLoading && versions.length === 0 && (
							<div className="text-center text-slate-400 py-8 text-sm">Loading…</div>
						)}
						{!versionsLoading && versions.length === 0 && (
							<div className="text-center text-slate-400 py-8 text-sm">No version history yet.</div>
						)}
						<div className="flex flex-col gap-2">
							{versions.map((v, idx) => {
								const isExpanded = expandedVersion === v.version;
								return (
									<div
										key={v.version}
										style={{ animationDelay: `${Math.min(idx * 30, 240)}ms` }}
										className={`codexec-version-row bg-white border rounded-lg overflow-hidden ${
											v.version === execution.snippet_version
												? 'border-emerald-300 ring-1 ring-emerald-100'
												: v.is_current
													? 'border-indigo-200'
													: 'border-slate-200'
										}`}
									>
										<button
											onClick={() => setExpandedVersion(isExpanded ? null : v.version)}
											className="w-full text-left px-4 py-3 hover:bg-slate-50 transition-colors flex items-center justify-between"
										>
											<div className="flex items-center gap-3">
												<div className="font-mono text-[14px] font-semibold text-slate-900">v{v.version}</div>
												{v.is_current && (
													<span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-indigo-50 text-indigo-700">
														LATEST
													</span>
												)}
												{v.version === execution.snippet_version && (
													<span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-50 text-emerald-700">
														THIS RUN
													</span>
												)}
												<div className="font-mono text-[11px] text-slate-400">{(v.source_hash || '').slice(0, 8)}</div>
											</div>
											<div className="flex items-center gap-3 text-[12px] text-slate-600">
												<span>
													<span className="font-mono text-slate-900">{v.run_count}</span> run{v.run_count !== 1 ? 's' : ''}
												</span>
												{v.last_run_at && (
													<span className="text-slate-500">last: {formatRelative(v.last_run_at)}</span>
												)}
												<span
													role="button"
													onClick={(e) => {
														e.stopPropagation();
														if (v.source_snapshot) {
															askRunVersionFromTab(v.version, v.source_snapshot, v.source_hash, v.is_current);
														}
													}}
													title={v.is_current ? 'Run latest code' : `Re-run v${v.version}`}
													className="px-2 h-7 rounded-md text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100 hover:border-emerald-300 transition-all active:scale-[0.97] inline-flex items-center gap-1"
												>
													<span style={{ fontSize: 9 }}>▸</span> Run
												</span>
												<span className="text-slate-400 text-[14px]">{isExpanded ? '▾' : '▸'}</span>
											</div>
										</button>
										{isExpanded && (
											<div className="border-t border-slate-200 bg-slate-50/40">
												<div className="px-4 py-2 flex items-center justify-between text-[11.5px] text-slate-600">
													<div>
														{v.first_run_at && (
															<>First run: <span className="text-slate-800">{new Date(v.first_run_at).toLocaleString()}</span></>
														)}
														{!v.first_run_at && v.is_current && (
															<span className="text-amber-700">Current code · not yet executed</span>
														)}
													</div>
													{v.representative_execution_uuid && v.representative_execution_uuid !== execution.object_uuid && (
														<button
															onClick={() => onSelectExecution?.(v.representative_execution_uuid)}
															className="text-indigo-600 hover:text-indigo-800 font-medium transition-colors"
														>
															Open a run of v{v.version} →
														</button>
													)}
												</div>
												<pre className="bg-[#0F1117] text-slate-200 m-2 mt-0 rounded-md p-3.5 font-mono text-[12px] overflow-auto whitespace-pre" style={{ maxHeight: 360 }}>
													{v.source_snapshot || '(empty)'}
												</pre>
											</div>
										)}
									</div>
								);
							})}
						</div>
					</div>
				)}

				{tab === 'meta' && (
					<div className="grid grid-cols-2 gap-x-8 gap-y-2 text-[12.5px] max-w-[640px]">
						<div className="text-slate-500">Status</div><div className="text-slate-900"><StatusPill status={execution.status} /></div>
						<div className="text-slate-500">Trigger kind</div><div className="text-slate-900 font-mono">{execution.trigger_kind}</div>
						<div className="text-slate-500">Queued at</div><div className="text-slate-900">{execution.queued_at ? new Date(execution.queued_at).toLocaleString() : '—'}</div>
						<div className="text-slate-500">Started at</div><div className="text-slate-900">{execution.started_at ? new Date(execution.started_at).toLocaleString() : '—'}</div>
						<div className="text-slate-500">Ended at</div><div className="text-slate-900">{execution.ended_at ? new Date(execution.ended_at).toLocaleString() : '—'}</div>
						<div className="text-slate-500">Duration</div><div className="text-slate-900 font-mono">{formatDuration(execution.duration_ms)}</div>
						<div className="text-slate-500">Celery task</div><div className="text-slate-900 font-mono break-all">{execution.celery_task_id || '—'}</div>
						<div className="text-slate-500">Exception</div><div className="text-slate-900 font-mono">{execution.exception_type || '—'}</div>
						{execution.exception_message ? (
							<>
								<div className="text-slate-500">Message</div>
								<div className="text-slate-900 whitespace-pre-wrap">{execution.exception_message}</div>
							</>
						) : null}
					</div>
				)}
			</div>

				</div>{/* end right side */}
			</div>{/* end two-column grid */}

			<ConfirmModal
				open={confirmingAbort}
				title="Abort this run?"
				description="The celery worker will be terminated. Outputs written so far are preserved."
				confirmLabel="Abort"
				confirmTone="danger"
				onCancel={() => setConfirmingAbort(false)}
				onConfirm={confirmedAbort}
			/>

			<RunConfirmModal
				open={Boolean(runConfirm)}
				title={runConfirm?.title || ''}
				subtitle={runConfirm?.subtitle || ''}
				code={runConfirm?.code || ''}
				version={runConfirm?.version}
				sourceHash={runConfirm?.sourceHash}
				loading={runConfirmLoading}
				onCancel={() => setRunConfirm(null)}
				onConfirm={confirmedRun}
			/>
		</div>
	);
}
