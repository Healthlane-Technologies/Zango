import { Fragment, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ApiError } from '@/api/client';
import {
	fetchLogs,
	fetchLogTail,
	usePlatformLogComponents,
	usePlatformLogTenants,
	type LogFilters,
	type LogLine,
} from '@/api/logConnectors';
import { formatDateTime } from '@/format/time';
import {
	Badge,
	Button,
	cx,
	EmptyState,
	ErrorState,
	SearchInput,
	Select,
	Skeleton,
	Toolbar,
	useDebounced,
	type Tone,
} from '@/ui';

const WINDOWS = [
	{ minutes: 15, label: 'Last 15 minutes' },
	{ minutes: 60, label: 'Last hour' },
	{ minutes: 360, label: 'Last 6 hours' },
	{ minutes: 1440, label: 'Last 24 hours' },
	{ minutes: 10080, label: 'Last 7 days' },
];
const LEVELS: Array<{ value: string; label: string; tone: Tone }> = [
	{ value: 'debug', label: 'Debug', tone: 'line' },
	{ value: 'info', label: 'Info', tone: 'gray' },
	{ value: 'warning', label: 'Warn', tone: 'amber' },
	{ value: 'error', label: 'Error', tone: 'red' },
	{ value: 'critical', label: 'Critical', tone: 'red' },
];
const DEFAULT_LEVELS = ['info', 'warning', 'error', 'critical'];
const TAIL_MS = 10_000;
const MAX_LINES = 2000;

// Verbose-format lines start with "[schema:domain] ".
const TENANT_PREFIX = /^\[([^:\]]+):([^\]]*)\]\s*/;

function splitTenant(message: string): { tenant?: string; text: string } {
	const m = TENANT_PREFIX.exec(message);
	return m ? { tenant: m[1], text: message.slice(m[0].length) } : { text: message };
}

function levelTone(level: string): Tone {
	return LEVELS.find((l) => l.value === level)?.tone ?? 'line';
}

function clock(iso: string): string {
	const d = new Date(iso);
	return `${d.toLocaleTimeString(undefined, { hour12: false })}.${String(d.getMilliseconds()).padStart(3, '0')}`;
}

function describe(err: unknown): string {
	if (err instanceof ApiError && err.status === 503)
		return 'The log source is throttling requests. Retrying shortly.';
	return (err as Error).message;
}

/** Browse + live tail, mirroring the classic panel's useLogTail against /api/v1/platform/logs/. */
function useLogStream(component: string | undefined, filters: LogFilters, live: boolean) {
	const [lines, setLines] = useState<LogLine[]>([]);
	const [loading, setLoading] = useState(false);
	const [loadingEarlier, setLoadingEarlier] = useState(false);
	const [error, setError] = useState<string>();
	const [hasEarlier, setHasEarlier] = useState(false);
	const tailCursor = useRef<string | null>(null);
	const earlierCursor = useRef<string | null>(null);
	const key = JSON.stringify([component, filters]);

	useEffect(() => {
		if (!component) return;
		let cancelled = false;
		setLoading(true);
		setError(undefined);
		setLines([]);
		tailCursor.current = null;
		earlierCursor.current = null;
		fetchLogs(component, filters)
			.then((page) => {
				if (cancelled) return;
				setLines(page.lines);
				// Tail from just after the newest line (lines arrive newest first).
				if (page.lines[0]) tailCursor.current = String(new Date(page.lines[0].ts).getTime() + 1);
				else tailCursor.current = String(Date.now());
				earlierCursor.current = page.next_cursor?.token ?? null;
				setHasEarlier(!!earlierCursor.current);
			})
			.catch((e) => !cancelled && setError(describe(e)))
			.finally(() => !cancelled && setLoading(false));
		return () => {
			cancelled = true;
		};
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [key]);

	useEffect(() => {
		if (!component || !live) return;
		const poll = async () => {
			if (document.hidden || !tailCursor.current) return;
			try {
				const page = await fetchLogTail(component, filters, tailCursor.current);
				if (page.next_cursor?.token) tailCursor.current = page.next_cursor.token;
				if (page.lines.length) {
					// Tail pages are oldest first.
					setLines((prev) => [...[...page.lines].reverse(), ...prev].slice(0, MAX_LINES));
				}
				setError(undefined);
			} catch (e) {
				setError(describe(e));
			}
		};
		const id = window.setInterval(poll, TAIL_MS);
		return () => window.clearInterval(id);
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [key, live]);

	const loadEarlier = useCallback(async () => {
		if (!component || !earlierCursor.current) return;
		setLoadingEarlier(true);
		try {
			const page = await fetchLogs(component, filters, earlierCursor.current);
			setLines((prev) => [...prev, ...page.lines].slice(0, MAX_LINES));
			earlierCursor.current = page.lines.length ? (page.next_cursor?.token ?? null) : null;
			setHasEarlier(!!earlierCursor.current);
		} catch (e) {
			setError(describe(e));
		} finally {
			setLoadingEarlier(false);
		}
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [key]);

	return { lines, loading, loadingEarlier, error, hasEarlier, loadEarlier };
}

function LevelFilter({ value, onChange }: { value: string[]; onChange: (v: string[]) => void }) {
	return (
		<div className="seg" role="group" aria-label="Levels">
			{LEVELS.map((l) => {
				const on = value.includes(l.value);
				return (
					<button
						key={l.value}
						type="button"
						aria-pressed={on}
						className={cx(on && 'on')}
						onClick={() => onChange(on ? value.filter((v) => v !== l.value) : [...value, l.value])}
					>
						{l.label}
					</button>
				);
			})}
		</div>
	);
}

function LogRow({ line, open, onToggle }: { line: LogLine; open: boolean; onToggle: () => void }) {
	const { tenant, text } = splitTenant(line.message);
	return (
		<Fragment>
			<tr className="row" onClick={onToggle} aria-expanded={open}>
				<td className="mono !h-9 text-t3" title={formatDateTime(line.ts)}>
					{clock(line.ts)}
				</td>
				<td className="!h-9">
					<Badge tone={levelTone(line.level)}>{line.level.toUpperCase()}</Badge>
				</td>
				<td className="mono !h-9 text-t2">{tenant ?? <span className="text-t4">—</span>}</td>
				<td className="mono !h-9 max-w-0 w-full truncate text-t1">{text}</td>
			</tr>
			{open && (
				<tr>
					<td colSpan={4} className="!h-auto bg-bg !py-3">
						<pre className="mono whitespace-pre-wrap break-words text-t1">{text}</pre>
						<div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[12px] text-t3">
							<span>{formatDateTime(line.ts)}</span>
							<span className="mono">stream {line.stream}</span>
						</div>
						{line.structured != null && (
							<pre className="mono mt-2 overflow-x-auto rounded-md border border-border bg-panel p-2 text-t2">
								{JSON.stringify(line.structured, null, 2)}
							</pre>
						)}
					</td>
				</tr>
			)}
		</Fragment>
	);
}

export function PlatformLogsTab({ onConfigure }: { onConfigure: () => void }) {
	const components = usePlatformLogComponents();
	const configured = components.data?.components.filter((c) => c.configured) ?? [];
	const [component, setComponent] = useState<string>();
	const [windowMin, setWindowMin] = useState(60);
	const [levels, setLevels] = useState(DEFAULT_LEVELS);
	const [search, setSearch] = useState('');
	const [tenant, setTenant] = useState('');
	const [live, setLive] = useState(true);
	const [openRow, setOpenRow] = useState<string | null>(null);
	const q = useDebounced(search.trim());

	const active = component ?? configured[0]?.key;
	// `since` is fixed when the filters change, so the query key is stable between renders.
	const filters = useMemo<LogFilters>(
		() => ({
			since: new Date(Date.now() - windowMin * 60_000).toISOString(),
			levels,
			q,
			tenants: tenant ? [tenant] : [],
		}),
		[windowMin, levels, q, tenant],
	);
	const tenants = usePlatformLogTenants(active, filters.since);
	const stream = useLogStream(active, filters, live);

	if (components.isLoading) return <Skeleton height={200} />;
	if (components.error)
		return (
			<div className="card">
				<ErrorState error={components.error} onRetry={() => components.refetch()} />
			</div>
		);
	if (configured.length === 0)
		return (
			<div className="card">
				<EmptyState
					title="No log connector configured"
					action={
						<Button size="sm" variant="primary" onClick={onConfigure}>
							Configure a connector
						</Button>
					}
				>
					Connect a log source to browse runtime logs from every app here.
				</EmptyState>
			</div>
		);

	return (
		<>
			<Toolbar>
				{configured.length > 1 && (
					<Select
						aria-label="Component"
						className="!w-auto"
						value={active}
						onChange={(e) => setComponent(e.target.value)}
					>
						{configured.map((c) => (
							<option key={c.key} value={c.key}>
								{c.label}
							</option>
						))}
					</Select>
				)}
				<SearchInput value={search} onChange={setSearch} placeholder="Search messages" />
				<Select
					aria-label="Time range"
					className="!w-auto"
					value={windowMin}
					onChange={(e) => setWindowMin(Number(e.target.value))}
				>
					{WINDOWS.map((w) => (
						<option key={w.minutes} value={w.minutes}>
							{w.label}
						</option>
					))}
				</Select>
				<Select
					aria-label="App"
					className="!w-auto max-w-[200px]"
					value={tenant}
					onChange={(e) => setTenant(e.target.value)}
				>
					<option value="">All apps</option>
					{(tenants.data?.tenants ?? []).map((t) => (
						<option key={t} value={t}>
							{t}
						</option>
					))}
				</Select>
				<LevelFilter value={levels} onChange={setLevels} />
				<Button
					size="sm"
					className="ml-auto"
					variant={live ? 'secondary' : 'ghost'}
					onClick={() => setLive((l) => !l)}
					aria-pressed={live}
				>
					{live ? (
						<span className="inline-block h-2 w-2 rounded-full bg-green" />
					) : (
						<span className="inline-block h-2 w-2 rounded-full bg-border-2" />
					)}
					{live ? 'Live' : 'Paused'}
				</Button>
			</Toolbar>
			{stream.error && (
				<div role="alert" className="banner !border-red-soft !bg-red-soft text-red-t">
					{stream.error}
				</div>
			)}
			<div className="card tbl-wrap">
				<table className="t">
					<thead>
						<tr>
							<th style={{ width: 110 }}>Time</th>
							<th style={{ width: 90 }}>Level</th>
							<th style={{ width: 160 }}>App</th>
							<th>Message</th>
						</tr>
					</thead>
					<tbody>
						{stream.loading &&
							Array.from({ length: 8 }, (_, i) => (
								<tr key={i}>
									{[70, 40, 80, 60 + ((i * 13) % 35)].map((w, j) => (
										<td key={j} className="!h-9">
											<Skeleton width={j === 3 ? `${w}%` : w} />
										</td>
									))}
								</tr>
							))}
						{!stream.loading &&
							stream.lines.map((l, i) => {
								const id = `${l.ts}-${l.cursor_token}-${i}`;
								return (
									<LogRow
										key={id}
										line={l}
										open={openRow === id}
										onToggle={() => setOpenRow(openRow === id ? null : id)}
									/>
								);
							})}
					</tbody>
				</table>
				{!stream.loading && stream.lines.length === 0 && !stream.error && (
					<EmptyState title="No log lines">
						Nothing matches in this time range. Try a wider range or fewer filters.
					</EmptyState>
				)}
				<div className="tfoot">
					<span className="num">{stream.lines.length} lines</span>
					{live && <span>· refreshes every {TAIL_MS / 1000}s</span>}
					<div className="r">
						<Button
							size="xs"
							onClick={stream.loadEarlier}
							loading={stream.loadingEarlier}
							disabled={!stream.hasEarlier}
						>
							Load earlier
						</Button>
					</div>
				</div>
			</div>
		</>
	);
}
