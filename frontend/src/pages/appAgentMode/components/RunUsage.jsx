/**
 * What the run actually consumed: which models ran, tokens, turns, time, cost.
 *
 * Everything here is recorded on the run row; none of it was reachable from
 * the panel before. `model_usage` is the only record of *which* models ran —
 * the configured `model` field is blank whenever the platform default is used,
 * which is the common case.
 */

const TOKEN_COLUMNS = [
	{ key: 'inputTokens', label: 'In' },
	{ key: 'outputTokens', label: 'Out' },
	{ key: 'cacheReadInputTokens', label: 'Cache read' },
	{ key: 'cacheCreationInputTokens', label: 'Cache write' },
];

function fmtInt(n) {
	if (n === null || n === undefined || n === '') return '—';
	const v = Number(n);
	if (!Number.isFinite(v)) return '—';
	if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(v >= 10_000_000 ? 0 : 1)}M`;
	if (v >= 1_000) return `${(v / 1_000).toFixed(v >= 10_000 ? 0 : 1)}k`;
	return String(v);
}

function fmtCost(v) {
	if (v === null || v === undefined || v === '') return '—';
	const n = Number(v);
	if (!Number.isFinite(n)) return '—';
	// Sub-cent runs still cost something; don't round them away to $0.00.
	return `$${n < 0.01 && n > 0 ? n.toFixed(4) : n.toFixed(2)}`;
}

function fmtDuration(ms) {
	if (!ms && ms !== 0) return '—';
	const s = Math.round(Number(ms) / 1000);
	if (!Number.isFinite(s)) return '—';
	if (s < 60) return `${s}s`;
	const m = Math.floor(s / 60);
	if (m < 60) return `${m}m ${String(s % 60).padStart(2, '0')}s`;
	return `${Math.floor(m / 60)}h ${String(m % 60).padStart(2, '0')}m`;
}

function Metric({ label, value, title }) {
	return (
		<div className="min-w-0" title={title}>
			<div className="font-lato text-[10px] font-bold uppercase tracking-[0.06em] text-[#9CA3AF]">
				{label}
			</div>
			<div className="truncate font-lato text-[15px] font-semibold text-[#111827]">
				{value}
			</div>
		</div>
	);
}

function SectionLabel({ children }) {
	return (
		<div className="mb-[6px] font-lato text-[11px] font-bold uppercase tracking-[0.06em] text-[#6B7280]">
			{children}
		</div>
	);
}

export default function RunUsage({ run }) {
	if (!run) return null;

	const usage = run.model_usage && typeof run.model_usage === 'object' ? run.model_usage : null;
	const models = usage ? Object.keys(usage) : [];
	// A run that died before a ResultMessage has only the assistant-message
	// fallback: model names with a message count, no token columns.
	const hasTokenBreakdown = models.some((m) =>
		TOKEN_COLUMNS.some((c) => usage[m] && usage[m][c.key] !== undefined)
	);

	const tools = run.tool_use_counts && typeof run.tool_use_counts === 'object'
		? Object.entries(run.tool_use_counts).sort((a, b) => b[1] - a[1])
		: [];

	const totalTokens =
		(Number(run.input_tokens) || 0) +
		(Number(run.output_tokens) || 0) +
		(Number(run.cache_read_tokens) || 0) +
		(Number(run.cache_creation_tokens) || 0);

	const turns = run.num_turns ?? run.progress?.turns;
	const cost = run.total_cost_usd ?? run.progress?.cost_usd;

	// Render nothing rather than an empty "Usage" box when a run recorded none
	// of this — a failure before the first result leaves every field blank.
	const hasAnything =
		models.length ||
		tools.length ||
		totalTokens ||
		turns !== null && turns !== undefined ||
		cost !== null && cost !== undefined ||
		run.duration_ms;
	if (!hasAnything) return null;

	return (
		<div className="border-t border-[#F1F3F5] px-[20px] py-[14px]">
			<SectionLabel>Usage</SectionLabel>

			<div className="mb-[14px] grid grid-cols-2 gap-x-[16px] gap-y-[10px] sm:grid-cols-4">
				<Metric label="Cost" value={fmtCost(cost)} />
				<Metric label="Turns" value={turns ?? '—'} />
				<Metric
					label="Tokens"
					value={totalTokens ? fmtInt(totalTokens) : '—'}
					title={totalTokens ? `${totalTokens.toLocaleString()} tokens` : undefined}
				/>
				<Metric
					label="Duration"
					value={fmtDuration(run.duration_ms)}
					title={
						run.duration_api_ms
							? `${fmtDuration(run.duration_api_ms)} of it waiting on the model`
							: undefined
					}
				/>
			</div>

			{models.length ? (
				<div className="mb-[12px]">
					<SectionLabel>{models.length > 1 ? 'Models used' : 'Model used'}</SectionLabel>
					<div className="overflow-x-auto">
						<table className="w-full min-w-[440px] border-collapse">
							<thead>
								<tr className="border-b border-[#F1F3F5]">
									<th className="py-[4px] pr-[10px] text-left font-lato text-[10px] font-bold uppercase tracking-[0.06em] text-[#9CA3AF]">
										Model
									</th>
									{hasTokenBreakdown ? (
										TOKEN_COLUMNS.map((c) => (
											<th
												key={c.key}
												className="py-[4px] pl-[10px] text-right font-lato text-[10px] font-bold uppercase tracking-[0.06em] text-[#9CA3AF]"
											>
												{c.label}
											</th>
										))
									) : (
										<th className="py-[4px] pl-[10px] text-right font-lato text-[10px] font-bold uppercase tracking-[0.06em] text-[#9CA3AF]">
											Messages
										</th>
									)}
									{hasTokenBreakdown ? (
										<th className="py-[4px] pl-[10px] text-right font-lato text-[10px] font-bold uppercase tracking-[0.06em] text-[#9CA3AF]">
											Cost
										</th>
									) : null}
								</tr>
							</thead>
							<tbody>
								{models.map((name) => {
									const u = usage[name] || {};
									return (
										<tr key={name} className="border-b border-[#F8FAFC]">
											<td
												className="max-w-[240px] truncate py-[5px] pr-[10px] font-mono text-[11px] text-[#111827]"
												title={name}
											>
												{name}
											</td>
											{hasTokenBreakdown ? (
												TOKEN_COLUMNS.map((c) => (
													<td
														key={c.key}
														className="py-[5px] pl-[10px] text-right font-mono text-[11px] text-[#374151]"
														title={
															u[c.key] !== undefined && u[c.key] !== null
																? Number(u[c.key]).toLocaleString()
																: undefined
														}
													>
														{fmtInt(u[c.key])}
													</td>
												))
											) : (
												<td className="py-[5px] pl-[10px] text-right font-mono text-[11px] text-[#374151]">
													{fmtInt(u.messages)}
												</td>
											)}
											{hasTokenBreakdown ? (
												<td className="py-[5px] pl-[10px] text-right font-mono text-[11px] text-[#374151]">
													{fmtCost(u.costUSD)}
												</td>
											) : null}
										</tr>
									);
								})}
							</tbody>
						</table>
					</div>
					{!hasTokenBreakdown ? (
						<div className="mt-[5px] font-lato text-[11px] text-[#9CA3AF]">
							The run ended before reporting token usage, so only the models it
							called are known.
						</div>
					) : null}
				</div>
			) : null}

			{tools.length ? (
				<div className="mb-[12px]">
					<SectionLabel>Tool calls ({tools.reduce((a, [, n]) => a + n, 0)})</SectionLabel>
					<div className="flex flex-wrap gap-[6px]">
						{tools.map(([name, count]) => (
							<span
								key={name}
								className="rounded-[4px] bg-[#F3F4F6] px-[7px] py-[2px] font-mono text-[11px] text-[#374151]"
							>
								{name} <span className="text-[#6B7280]">{count}</span>
							</span>
						))}
					</div>
				</div>
			) : null}

			<div className="flex flex-wrap gap-x-[18px] gap-y-[3px] font-lato text-[11px] text-[#9CA3AF]">
				{run.effort ? <span>Effort: {run.effort}</span> : null}
				{run.max_turns ? <span>Turn limit: {run.max_turns}</span> : null}
				{run.max_budget_usd ? <span>Budget: {fmtCost(run.max_budget_usd)}</span> : null}
				{run.terminal_reason ? <span>Ended: {run.terminal_reason}</span> : null}
				{run.api_error_status ? <span>API status: {run.api_error_status}</span> : null}
				{run.duration_api_ms ? <span>Model time: {fmtDuration(run.duration_api_ms)}</span> : null}
				{run.session_id ? (
					<span className="font-mono" title={run.session_id}>
						Session: {String(run.session_id).slice(0, 8)}
					</span>
				) : null}
			</div>
		</div>
	);
}
