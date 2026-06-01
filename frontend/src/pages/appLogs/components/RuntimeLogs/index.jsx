import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import useApi from '../../../../hooks/useApi';
import FilterRail from './FilterRail';
import LogsTable from './LogsTable';
import useLogTail from './useLogTail';

const COMPONENTS = [
	{ key: 'app', label: 'App' },
	{ key: 'celery', label: 'Celery' },
	{ key: 'celery_beat', label: 'Celery beat' },
];

const PRESET_WINDOWS = [
	{ value: 15, label: 'Last 15 min' },
	{ value: 60, label: 'Last 1 hour' },
	{ value: 6 * 60, label: 'Last 6 hours' },
	{ value: 24 * 60, label: 'Last 24 hours' },
];

// Format a Date for an HTML <input type="datetime-local"> value (no seconds).
function toLocalInput(d) {
	const pad = (n) => String(n).padStart(2, '0');
	return (
		`${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` +
		`T${pad(d.getHours())}:${pad(d.getMinutes())}`
	);
}

function fromLocalInput(s) {
	if (!s) return null;
	// datetime-local is in local TZ, no offset → convert to absolute Date.
	return new Date(s);
}

export default function RuntimeLogs() {
	const { appId } = useParams();
	const triggerApi = useApi();

	const [component, setComponent] = useState(null);
	const [availableComponents, setAvailableComponents] = useState([]);

	// Time window. Either preset minutes OR a custom { from, to } pair.
	const [windowMinutes, setWindowMinutes] = useState(60); // preset
	const [customRange, setCustomRange] = useState(null); // { from: Date, to: Date } | null
	const [showCustomPicker, setShowCustomPicker] = useState(false);
	const [customDraft, setCustomDraft] = useState({
		from: toLocalInput(new Date(Date.now() - 60 * 60 * 1000)),
		to: toLocalInput(new Date()),
	});

	const [searchText, setSearchText] = useState('');
	const [debouncedSearch, setDebouncedSearch] = useState('');
	const [patternText, setPatternText] = useState('');
	const [levels, setLevels] = useState(['info', 'warning', 'error', 'critical']);
	const [selectedStreams, setSelectedStreams] = useState([]);
	const [streams, setStreams] = useState([]);
	const [intervalMs, setIntervalMs] = useState(10000);
	const [paused, setPaused] = useState(false);

	// View options — column visibility / wrap / hide rail.
	const [showStream, setShowStream] = useState(true);
	const [showLevel, setShowLevel] = useState(true);
	const [wrapMessage, setWrapMessage] = useState(false);
	const [showRail, setShowRail] = useState(true);
	const [showViewMenu, setShowViewMenu] = useState(false);

	// User's local timezone — surfaced in the feed-meta bar.
	const userTz = useMemo(() => {
		try {
			return Intl.DateTimeFormat().resolvedOptions().timeZone || 'local';
		} catch {
			return 'local';
		}
	}, []);

	// Debounce search (300ms) so each keystroke doesn't fire a CloudWatch call.
	const debounceTimer = useRef(null);
	useEffect(() => {
		if (debounceTimer.current) window.clearTimeout(debounceTimer.current);
		debounceTimer.current = window.setTimeout(() => {
			setDebouncedSearch(searchText);
		}, 300);
		return () => {
			if (debounceTimer.current) window.clearTimeout(debounceTimer.current);
		};
	}, [searchText]);

	// Discover components.
	useEffect(() => {
		(async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/logs/components/`,
				type: 'GET',
				loader: true,
				showErrorModal: false,
			});
			if (success && response) {
				setAvailableComponents(response.components || []);
				const firstConfigured = (response.components || []).find(
					(c) => c.configured
				);
				if (firstConfigured && !component) {
					setComponent(firstConfigured.key);
				}
			}
		})();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [appId]);

	const { since, until, windowLabel } = useMemo(() => {
		if (customRange?.from && customRange?.to) {
			return {
				since: customRange.from.toISOString(),
				until: customRange.to.toISOString(),
				windowLabel: `${customRange.from.toLocaleString()} → ${customRange.to.toLocaleString()}`,
			};
		}
		return {
			since: new Date(Date.now() - windowMinutes * 60 * 1000).toISOString(),
			until: null,
			windowLabel:
				PRESET_WINDOWS.find((p) => p.value === windowMinutes)?.label ||
				`Last ${windowMinutes} min`,
		};
	}, [windowMinutes, customRange]);

	// Refresh stream list.
	useEffect(() => {
		if (!component) return;
		(async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/logs/${component}/streams/?since=${encodeURIComponent(since)}`,
				type: 'GET',
				loader: false,
				showErrorModal: false,
			});
			if (success && response) {
				setStreams(response.streams || []);
			}
		})();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [appId, component, since]);

	const filters = useMemo(
		() => ({
			since,
			until,
			q: debouncedSearch,
			pattern: patternText,
			levels,
			streams: selectedStreams,
		}),
		[since, until, debouncedSearch, patternText, levels, selectedStreams]
	);

	const {
		lines,
		error,
		isPolling,
		initialLoading,
		loadingEarlier,
		hasMoreEarlier,
		loadEarlier,
	} = useLogTail({
		appId,
		component,
		filters,
		intervalMs,
		enabled: !!component,
		paused: paused || !!customRange,
	});

	const handleComponentChange = useCallback((key) => {
		setComponent(key);
		setSelectedStreams([]);
	}, []);

	const applyCustomRange = () => {
		const from = fromLocalInput(customDraft.from);
		const to = fromLocalInput(customDraft.to);
		if (!from || !to || from >= to) return;
		setCustomRange({ from, to });
		setShowCustomPicker(false);
		// Pause tail when looking at a frozen historical window.
		setPaused(true);
	};

	const clearCustomRange = () => {
		setCustomRange(null);
		setPaused(false);
	};

	if (availableComponents.length === 0) {
		return (
			<div className="rounded-[10px] border border-[#E3E6EF] bg-white p-[40px] text-center">
				<div className="text-[14px] font-semibold text-[#0B0D14]">
					No connectors configured
				</div>
				<div className="mt-[3px] text-[12.5px] text-[#5A607A]">
					A platform admin must wire up a Log connector at{' '}
					<code className="rounded bg-[#F0F2F7] px-[5px] py-[1px] font-mono text-[11.5px]">
						/platform/settings/log-connectors
					</code>{' '}
					before logs show up here.
				</div>
			</div>
		);
	}

	return (
		<div className="flex flex-col gap-[12px]">
			{/* Header strip */}
			<div className="flex flex-wrap items-center gap-[10px] rounded-[10px] border border-[#E3E6EF] bg-white px-[16px] py-[10px] shadow-sm">
				<div className="inline-flex overflow-hidden rounded-[8px] border border-[#D4D8E5]">
					{availableComponents.map((c, i) => (
						<button
							key={c.key}
							type="button"
							disabled={!c.configured}
							onClick={() => handleComponentChange(c.key)}
							className={`px-[12px] py-[6px] text-[12px] font-medium ${
								component === c.key
									? 'bg-[#EEF1FE] text-[#3938B5]'
									: c.configured
									? 'bg-white text-[#5A607A] hover:bg-[#F0F2F7]'
									: 'cursor-not-allowed bg-white text-[#C2C8D8]'
							} ${i < availableComponents.length - 1 ? 'border-r border-[#ECEEF5]' : ''}`}
						>
							{COMPONENTS.find((cc) => cc.key === c.key)?.label || c.key}
							{!c.configured && (
								<span className="ml-[5px] rounded-full bg-[#F0F2F7] px-[5px] text-[9px] uppercase tracking-[0.06em] text-[#8389A3]">
									off
								</span>
							)}
						</button>
					))}
				</div>

				{/* Time window — preset selector + custom range button */}
				<div className="relative inline-flex items-center">
					<select
						value={customRange ? '__custom__' : String(windowMinutes)}
						onChange={(e) => {
							if (e.target.value === '__custom__') {
								// Pre-fill the draft with the current window so opening
								// the picker feels continuous.
								setCustomDraft({
									from: toLocalInput(new Date(Date.now() - windowMinutes * 60 * 1000)),
									to: toLocalInput(new Date()),
								});
								setShowCustomPicker(true);
							} else {
								clearCustomRange();
								setWindowMinutes(Number(e.target.value));
							}
						}}
						className="rounded-[8px] border border-[#D4D8E5] bg-white px-[10px] py-[5px] text-[12px] text-[#2C3047]"
					>
						{PRESET_WINDOWS.map((w) => (
							<option key={w.value} value={String(w.value)}>
								{w.label}
							</option>
						))}
						<option value="__custom__">Custom range…</option>
					</select>
					{customRange && (
						<button
							type="button"
							onClick={clearCustomRange}
							className="ml-[6px] inline-flex items-center gap-[5px] rounded-full bg-[#EEF1FE] px-[8px] py-[2px] text-[10.5px] font-medium text-[#3938B5] hover:bg-[#DCE3FD]"
							title="Clear custom range"
						>
							{windowLabel}
							<span aria-hidden="true">×</span>
						</button>
					)}
				</div>

				<div className="relative flex-1" style={{ minWidth: '220px', maxWidth: '360px' }}>
					<input
						type="text"
						value={searchText}
						onChange={(e) => setSearchText(e.target.value)}
						placeholder="Search messages, tracebacks, request IDs…"
						className="w-full rounded-[8px] border border-[#E3E6EF] bg-[#F0F2F7] px-[12px] py-[5px] pr-[68px] text-[12.5px] focus:border-[#5961E5] focus:bg-white focus:outline-none"
					/>
					{searchText && searchText !== debouncedSearch && (
						<span className="absolute right-[10px] top-1/2 -translate-y-1/2 text-[10px] text-[#8389A3]">
							typing…
						</span>
					)}
				</div>

				<button
					type="button"
					onClick={() => setPaused((p) => !p)}
					disabled={!!customRange}
					className={`inline-flex items-center gap-[6px] rounded-[8px] border px-[11px] py-[5px] text-[12px] font-medium ${
						customRange
							? 'cursor-not-allowed border-[#E3E6EF] bg-[#F0F2F7] text-[#8389A3]'
							: !paused
							? 'border-[rgba(90,164,91,0.35)] bg-[#EFF7EE] text-[#36713A]'
							: 'border-[#D4D8E5] bg-white text-[#2C3047] hover:bg-[#F0F2F7]'
					}`}
					title={customRange ? 'Tail paused — viewing a frozen range' : undefined}
				>
					{!paused && !customRange && (
						<span
							className="h-[7px] w-[7px] rounded-full bg-[#5AA45B]"
							style={{ boxShadow: '0 0 0 3px rgba(90,164,91,0.22)' }}
						/>
					)}
					{customRange ? 'Tail off' : paused ? 'Resume tail' : 'Live tail'}
					{!paused && !customRange && (
						<span className="ml-[2px] border-l border-[rgba(90,164,91,0.25)] pl-[6px] font-mono text-[10px] opacity-90">
							{intervalMs / 1000}s
						</span>
					)}
				</button>

				{/* View options — column visibility / wrap / hide rail */}
				<div className="relative">
					<button
						type="button"
						onClick={() => setShowViewMenu((v) => !v)}
						className="inline-flex items-center gap-[6px] rounded-[8px] border border-[#D4D8E5] bg-white px-[11px] py-[5px] text-[12px] font-medium text-[#2C3047] hover:bg-[#F0F2F7]"
						title="Table view options"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							width="12"
							height="12"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							strokeWidth="2"
						>
							<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
							<circle cx="12" cy="12" r="3" />
						</svg>
						View
					</button>
					{showViewMenu && (
						<div className="absolute right-0 z-30 mt-[6px] w-[230px] rounded-[10px] border border-[#E3E6EF] bg-white py-[6px] shadow-lg transition-all duration-150">
							<div className="px-[14px] pb-[4px] pt-[6px] text-[9.5px] font-semibold uppercase tracking-[0.08em] text-[#8389A3]">
								Columns
							</div>
							<ViewToggle
								label="Level"
								checked={showLevel}
								onToggle={() => setShowLevel((v) => !v)}
							/>
							<ViewToggle
								label="Stream"
								checked={showStream}
								onToggle={() => setShowStream((v) => !v)}
							/>

							<div className="my-[4px] border-t border-[#ECEEF5]" />
							<div className="px-[14px] pb-[4px] pt-[2px] text-[9.5px] font-semibold uppercase tracking-[0.08em] text-[#8389A3]">
								Display
							</div>
							<ViewToggle
								label="Wrap long messages"
								checked={wrapMessage}
								onToggle={() => setWrapMessage((v) => !v)}
							/>
							<ViewToggle
								label="Show filter sidebar"
								checked={showRail}
								onToggle={() => setShowRail((v) => !v)}
							/>
						</div>
					)}
				</div>

				{/* Custom-range popover */}
				{showCustomPicker && (
					<div className="absolute z-20 mt-[42px] flex flex-col gap-[10px] rounded-[10px] border border-[#E3E6EF] bg-white p-[14px] shadow-lg">
						<div className="text-[10.5px] font-semibold uppercase tracking-[0.07em] text-[#8389A3]">
							Custom date range (local time)
						</div>
						<div className="flex items-center gap-[10px]">
							<label className="flex flex-col">
								<span className="mb-[3px] text-[10px] uppercase tracking-[0.07em] text-[#8389A3]">
									From
								</span>
								<input
									type="datetime-local"
									value={customDraft.from}
									onChange={(e) =>
										setCustomDraft((d) => ({ ...d, from: e.target.value }))
									}
									className="rounded-[6px] border border-[#D4D8E5] bg-white px-[8px] py-[4px] font-mono text-[11.5px]"
								/>
							</label>
							<label className="flex flex-col">
								<span className="mb-[3px] text-[10px] uppercase tracking-[0.07em] text-[#8389A3]">
									To
								</span>
								<input
									type="datetime-local"
									value={customDraft.to}
									onChange={(e) =>
										setCustomDraft((d) => ({ ...d, to: e.target.value }))
									}
									className="rounded-[6px] border border-[#D4D8E5] bg-white px-[8px] py-[4px] font-mono text-[11.5px]"
								/>
							</label>
						</div>
						<div className="flex gap-[6px]">
							<button
								type="button"
								onClick={() => setShowCustomPicker(false)}
								className="rounded-[6px] px-[10px] py-[4px] text-[11.5px] font-medium text-[#5A607A] hover:bg-[#F0F2F7]"
							>
								Cancel
							</button>
							<button
								type="button"
								onClick={applyCustomRange}
								className="rounded-[6px] bg-[#0B0D14] px-[10px] py-[4px] text-[11.5px] font-medium text-white hover:bg-[#14172A]"
							>
								Apply
							</button>
						</div>
					</div>
				)}
			</div>

			{error?.kind === 'throttled' && (
				<div className="rounded-[8px] border border-[#FCEAC4] border-l-[3px] border-l-[#DA9011] bg-[#FEF6E7] px-[14px] py-[10px] text-[12px] text-[#8A5A07]">
					<strong>CloudWatch throttled.</strong> Backing off for a moment — the
					tail will resume automatically.
				</div>
			)}
			{error?.kind === 'fetch_failed' && (
				<div className="rounded-[8px] border border-[#F8D5D9] border-l-[3px] border-l-[#D3424E] bg-[#FCEDEF] px-[14px] py-[10px] text-[12px] text-[#931F2A]">
					<strong>Failed to fetch logs.</strong>{' '}
					{error.detail || 'Check the connector configuration.'}
				</div>
			)}

			{/* Feed meta + grid */}
			<div className="flex flex-col gap-[8px] md:flex-row md:items-stretch">
				<div className="flex min-w-0 flex-1 flex-col gap-[6px]">
					<div className="flex flex-wrap items-center gap-[10px] rounded-[8px] border border-[#ECEEF5] bg-[#FAFBFD] px-[14px] py-[7px] text-[11.5px] text-[#5A607A]">
						<span>
							<strong className="text-[#0B0D14]">{lines.length}</strong> lines ·{' '}
							{streams.length} streams · window: {windowLabel}
						</span>
						<span className="text-[10.5px] text-[#8389A3]" title="Times displayed in your local timezone">
							TZ: {userTz}
						</span>
						<span className="ml-auto inline-flex items-center gap-[5px] rounded-full bg-[#EFF7EE] px-[8px] py-[2px] text-[10.5px] font-medium text-[#36713A]">
							<span className="h-[5px] w-[5px] rounded-full bg-[#5AA45B]" />
							{customRange
								? 'Historical view'
								: paused
								? 'Paused'
								: isPolling
								? 'Polling…'
								: `Tail live · every ${intervalMs / 1000}s`}
						</span>
					</div>
					<LogsTable
						lines={lines}
						initialLoading={initialLoading}
						loadingEarlier={loadingEarlier}
						hasMoreEarlier={hasMoreEarlier}
						onLoadEarlier={loadEarlier}
						showStream={showStream}
						showLevel={showLevel}
						wrapMessage={wrapMessage}
					/>
				</div>

				{showRail && (
					<FilterRail
						levels={levels}
						onLevelsChange={setLevels}
						streams={streams}
						selectedStreams={selectedStreams}
						onStreamsChange={setSelectedStreams}
						patternText={patternText}
						onPatternChange={setPatternText}
						paused={paused}
						onPausedToggle={setPaused}
						intervalMs={intervalMs}
						onIntervalChange={setIntervalMs}
					/>
				)}
			</div>
		</div>
	);
}

function ViewToggle({ label, checked, onToggle }) {
	return (
		<button
			type="button"
			onClick={onToggle}
			className="flex w-full items-center gap-[10px] px-[14px] py-[6px] text-left text-[12px] text-[#2C3047] hover:bg-[#F0F2F7]"
		>
			<span
				className={`flex h-[14px] w-[14px] flex-shrink-0 items-center justify-center rounded-[3px] border-[1.5px] transition-colors ${
					checked ? 'border-[#5961E5] bg-[#5961E5] text-white' : 'border-[#D4D8E5]'
				}`}
			>
				{checked && (
					<span className="text-[10px] font-bold leading-none">✓</span>
				)}
			</span>
			<span className="flex-1">{label}</span>
		</button>
	);
}
