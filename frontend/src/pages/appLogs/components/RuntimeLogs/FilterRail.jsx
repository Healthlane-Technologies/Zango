const LEVELS = ['debug', 'info', 'warning', 'error', 'critical'];
const INTERVAL_OPTIONS = [
	{ value: 1000, label: '1 s' },
	{ value: 2000, label: '2 s' },
	{ value: 5000, label: '5 s' },
	{ value: 10000, label: '10 s' },
];

export default function FilterRail({
	levels,
	onLevelsChange,
	streams,
	selectedStreams,
	onStreamsChange,
	patternText,
	onPatternChange,
	paused,
	onPausedToggle,
	intervalMs,
	onIntervalChange,
}) {
	const toggleLevel = (lvl) => {
		const next = new Set(levels);
		if (next.has(lvl)) next.delete(lvl);
		else next.add(lvl);
		onLevelsChange(Array.from(next));
	};

	const toggleStream = (name) => {
		const next = new Set(selectedStreams);
		if (next.has(name)) next.delete(name);
		else next.add(name);
		onStreamsChange(Array.from(next));
	};

	const resetLevels = () =>
		onLevelsChange(['info', 'warning', 'error', 'critical']);
	const resetStreams = () => onStreamsChange([]);

	return (
		<aside className="flex h-full w-[260px] flex-shrink-0 flex-col gap-[18px] overflow-y-auto border-l border-[#E3E6EF] bg-[#FAFBFD] px-[16px] py-[16px]">
			<Block title="Levels" onClear={resetLevels} clearLabel="Reset">
				{LEVELS.map((lvl) => (
					<Check
						key={lvl}
						checked={levels.includes(lvl)}
						label={lvl.toUpperCase()}
						onChange={() => toggleLevel(lvl)}
					/>
				))}
			</Block>

			<Block
				title="Streams"
				onClear={resetStreams}
				clearLabel={selectedStreams.length ? 'Group-wide' : ''}
			>
				{(!streams || streams.length === 0) && (
					<div className="px-[4px] py-[6px] text-[10.5px] text-[#8389A3]">
						No active streams in the last 24h.
					</div>
				)}
				{streams?.slice(0, 8).map((s) => (
					<StreamRow
						key={s.name}
						checked={selectedStreams.includes(s.name)}
						stream={s}
						onChange={() => toggleStream(s.name)}
					/>
				))}
			</Block>

			<Block title="Polling">
				<Check
					checked={!paused}
					label="Live tail"
					onChange={() => onPausedToggle(!paused)}
				/>
				<div className="mt-[8px]">
					<label className="mb-[4px] block text-[10px] font-semibold uppercase tracking-[0.07em] text-[#8389A3]">
						Interval
					</label>
					<select
						value={intervalMs}
						onChange={(e) => onIntervalChange(Number(e.target.value))}
						className="w-full rounded-[6px] border border-[#E3E6EF] bg-white px-[9px] py-[5px] text-[11.5px] text-[#0B0D14]"
					>
						{INTERVAL_OPTIONS.map((o) => (
							<option key={o.value} value={o.value}>
								{o.label}
							</option>
						))}
					</select>
				</div>
			</Block>

			<Block title="Native pattern">
				<textarea
					value={patternText}
					onChange={(e) => onPatternChange(e.target.value)}
					placeholder='[ERROR]  or  "DoesNotExist"'
					className="min-h-[56px] w-full resize-y rounded-[6px] border border-[#E3E6EF] bg-white px-[10px] py-[7px] font-mono text-[10.5px] text-[#0B0D14] focus:border-[#5961E5] focus:outline-none"
				/>
				<div className="mt-[4px] text-[10px] text-[#8389A3]">
					CloudWatch filter syntax. Combined with the toggles above.
				</div>
			</Block>
		</aside>
	);
}

function Block({ title, onClear, clearLabel, children }) {
	return (
		<section>
			<div className="mb-[8px] flex items-center justify-between">
				<div className="text-[10.5px] font-semibold uppercase tracking-[0.08em] text-[#8389A3]">
					{title}
				</div>
				{clearLabel && onClear && (
					<button
						type="button"
						onClick={onClear}
						className="text-[10.5px] text-[#5961E5] hover:underline"
					>
						{clearLabel}
					</button>
				)}
			</div>
			{children}
		</section>
	);
}

function Check({ checked, label, onChange }) {
	return (
		<label className="flex cursor-pointer items-center gap-[9px] rounded-[6px] px-[4px] py-[5px] text-[12px] text-[#2C3047] hover:bg-white">
			<span
				className={`flex h-[14px] w-[14px] flex-shrink-0 items-center justify-center rounded-[3px] border-[1.5px] ${
					checked ? 'border-[#5961E5] bg-[#5961E5] text-white' : 'border-[#D4D8E5]'
				}`}
			>
				{checked && <span className="text-[10px] font-bold leading-none">✓</span>}
			</span>
			<span className="flex-1">{label}</span>
			<input
				type="checkbox"
				checked={checked}
				onChange={onChange}
				className="hidden"
			/>
		</label>
	);
}

function StreamRow({ checked, stream, onChange }) {
	const last = stream.last_event_ts
		? new Date(stream.last_event_ts).toLocaleTimeString()
		: '';
	return (
		<label
			className={`flex cursor-pointer items-center gap-[6px] rounded-[6px] px-[4px] py-[4px] text-[10.5px] ${
				checked ? 'bg-[#EEF1FE]' : 'hover:bg-white'
			}`}
		>
			<span
				className={`flex h-[13px] w-[13px] flex-shrink-0 items-center justify-center rounded-[3px] border-[1.5px] ${
					checked ? 'border-[#5961E5] bg-[#5961E5] text-white' : 'border-[#D4D8E5]'
				}`}
			>
				{checked && <span className="text-[9px] font-bold leading-none">✓</span>}
			</span>
			<span className="flex-1 truncate font-mono text-[10.5px] text-[#0B0D14]">
				{stream.name}
			</span>
			<span className="whitespace-nowrap text-[9.5px] text-[#8389A3]">{last}</span>
			<input
				type="checkbox"
				checked={checked}
				onChange={onChange}
				className="hidden"
			/>
		</label>
	);
}
