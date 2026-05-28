import React, { useEffect, useRef, useState, useCallback } from 'react';
import toast from 'react-hot-toast';
import useApi from '../../../../hooks/useApi';
import ConfirmModal from './ConfirmModal';

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

export default function ExecutionDetail({ appId, executionId, onBack, onEditSnippet, onSelectExecution }) {
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
		if (!execution?.snippet_id) return;
		if (mode === 'append' && historyLoadingMoreRef.current) return;
		const targetPage = mode === 'replace' ? 1 : historyPageRef.current + 1;
		if (mode === 'append') historyLoadingMoreRef.current = true;
		setHistoryLoading(true);
		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/code-execution/executions/?snippet_id=${execution.snippet_id}&page=${targetPage}&page_size=${HISTORY_PAGE_SIZE}`,
			type: 'GET',
			loader: false,
		});
		if (success && response?.executions?.records) {
			const records = response.executions.records;
			if (mode === 'replace') {
				setHistory(records);
			} else {
				setHistory((prev) => {
					const seen = new Set(prev.map((r) => r.id));
					return [...prev, ...records.filter((r) => !seen.has(r.id))];
				});
			}
			setHistoryTotalPages(response.executions.total_pages || 1);
			setHistoryTotalRecords(response.executions.total_records || 0);
			historyPageRef.current = targetPage;
		}
		setHistoryLoading(false);
		if (mode === 'append') historyLoadingMoreRef.current = false;
	}, [appId, execution?.snippet_id, triggerApi]);

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
		if (execution?.snippet_id) fetchHistory('replace');
	}, [execution?.snippet_id]); // eslint-disable-line react-hooks/exhaustive-deps

	// Auto-fetch the runs list as soon as we know the snippet id, and refresh
	// after the current run reaches a terminal state so durations show up.
	useEffect(() => { fetchHistory(); }, [execution?.snippet_id]); // eslint-disable-line react-hooks/exhaustive-deps
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
		{ id: 'meta', label: 'Metadata', count: null },
	];

	// Files come back with a `download_url` already — for S3 it's a presigned
	// URL with ResponseContentDisposition so the browser saves with the
	// original filename. We fall back to our backend redirect if the serializer
	// couldn't produce one (e.g., misconfigured storage).
	const downloadUrl = (f) =>
		f.download_url
		|| `/api/v1/apps/${appId}/code-execution/executions/${execution.id}/files/${f.id}/download/`;

	return (
		<div className="flex flex-col pb-24">
			<style>{`
				@keyframes codexecFadeIn {
					from { opacity: 0; transform: translateY(4px); }
					to   { opacity: 1; transform: translateY(0); }
				}
			`}</style>
			{/* Top */}
			<div className="px-7 py-5 border-b border-slate-200 bg-gradient-to-b from-slate-50/50 to-white">
				<div className="text-[10.5px] font-semibold uppercase tracking-[0.07em] text-slate-500 mb-1">
					<button onClick={onBack} className="hover:text-slate-700">Code Execution</button>
					<span className="text-slate-300 px-1.5">/</span>
					<button onClick={onBack} className="hover:text-slate-700">{execution.snippet_name}</button>
					<span className="text-slate-300 px-1.5">/</span>
					<span className="text-slate-900">Run {execution.id.slice(0, 6)}</span>
				</div>
				<div className="flex items-center justify-between">
					<div className="flex items-center gap-2.5">
						<div className="w-7 h-7 bg-indigo-50 text-indigo-600 rounded-md grid place-items-center font-mono text-[12px] font-semibold">py</div>
						<div className="text-[20px] font-bold text-slate-900 leading-tight tracking-tight">{execution.snippet_name}</div>
						<div className="ml-3"><StatusPill status={execution.status} /></div>
					</div>
					<div className="flex gap-2">
						<button onClick={onBack} className="px-3 h-9 rounded-md text-[12.5px] font-medium bg-white border border-slate-300 text-slate-800 hover:border-slate-400">← Back</button>
						<button
							onClick={() => onEditSnippet?.(execution.snippet_id)}
							className="px-3 h-9 rounded-md text-[12.5px] font-medium bg-white border border-slate-300 text-slate-800 hover:border-slate-400"
						>
							✎ Edit snippet
						</button>
						{(execution.status === 'queued' || execution.status === 'running') && (
							<button
								onClick={askAbort}
								className="px-3 h-9 rounded-md text-[12.5px] font-medium bg-slate-900 text-white hover:bg-slate-800 transition-all active:scale-[0.98]"
							>
								⊗ Abort
							</button>
						)}
					</div>
				</div>

				<div className="grid grid-cols-5 gap-px bg-slate-200 border border-slate-200 rounded-md overflow-hidden mt-4">
					<div className="bg-white px-3.5 py-2.5">
						<div className="text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-500 mb-1">Run ID</div>
						<div className="text-[12px] font-mono text-slate-900">{execution.id.slice(0, 8)}</div>
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
							const isCurrent = r.id === execution.id;
							return (
								<button
									key={r.id}
									onClick={() => { if (!isCurrent) onSelectExecution?.(r.id); }}
									className={`block w-full text-left px-4 py-3 border-b border-slate-200/70 last:border-0 transition-colors ${
										isCurrent
											? 'bg-indigo-50 border-l-2 border-l-indigo-600 -ml-px'
											: 'hover:bg-slate-100 border-l-2 border-l-transparent -ml-px'
									}`}
								>
									<div className="flex items-center justify-between mb-1">
										<StatusPill status={r.status} />
										<span className="font-mono text-[10.5px] text-slate-400">{r.id.slice(0, 6)}</span>
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
							onClick={() => setTab(t.id)}
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
			<div key={tab} className="px-7 py-5 animate-[fadeIn_180ms_ease-out]" style={{ animation: 'codexecFadeIn 180ms ease-out' }}>
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
									<div key={f.id} className="grid items-center gap-2 py-1.5" style={{ gridTemplateColumns: '22px 1fr auto auto' }}>
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
									<div key={f.id} className="grid items-center gap-2 py-1.5" style={{ gridTemplateColumns: '22px 1fr auto auto' }}>
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
		</div>
	);
}
