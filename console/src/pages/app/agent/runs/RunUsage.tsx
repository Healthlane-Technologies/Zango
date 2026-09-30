import type { RunDetail } from '@/api/agentRuns';
import { fmtCost, fmtDuration, fmtTokens } from './format';

const TOKEN_COLUMNS = [
	['inputTokens', 'In'],
	['outputTokens', 'Out'],
	['cacheReadInputTokens', 'Cache read'],
	['cacheCreationInputTokens', 'Cache write'],
] as const;

function Metric({
	label,
	value,
	title,
}: {
	label: string;
	value: string | number;
	title?: string;
}) {
	return (
		<div className="rp-metric min-w-0" title={title}>
			<small>{label}</small>
			<b className="truncate">{value}</b>
		</div>
	);
}

/**
 * What the run consumed: cost, turns, tokens, time, and per-model usage. `model_usage` is the
 * only record of which models ran — `model` is blank whenever the platform default is used.
 */
export function RunUsage({ run }: { run: RunDetail }) {
	const usage = run.model_usage && typeof run.model_usage === 'object' ? run.model_usage : null;
	const models = usage ? Object.keys(usage) : [];
	// A run that died before its result message has only message counts per model.
	const hasTokens = models.some((m) => TOKEN_COLUMNS.some(([k]) => usage![m]?.[k] !== undefined));
	const tools = Object.entries(run.tool_use_counts ?? {}).sort((a, b) => b[1] - a[1]);
	const totalTokens =
		(run.input_tokens ?? 0) +
		(run.output_tokens ?? 0) +
		(run.cache_read_tokens ?? 0) +
		(run.cache_creation_tokens ?? 0);

	const hasAnything =
		models.length ||
		tools.length ||
		totalTokens ||
		run.num_turns != null ||
		run.total_cost_usd != null ||
		run.duration_ms;
	if (!hasAnything) return <p className="text-t3">This run recorded no usage.</p>;

	const footnotes = [
		run.effort && `Effort: ${run.effort}`,
		run.max_turns && `Turn limit: ${run.max_turns}`,
		run.max_budget_usd && `Budget: ${fmtCost(run.max_budget_usd)}`,
		run.terminal_reason && `Ended: ${run.terminal_reason}`,
		run.api_error_status && `API status: ${run.api_error_status}`,
		run.session_id && `Session ${run.session_id.slice(0, 8)}`,
	].filter(Boolean) as string[];

	return (
		<div className="grid gap-4">
			<div className="grid grid-cols-4 gap-3">
				<Metric label="Cost" value={fmtCost(run.total_cost_usd)} />
				<Metric label="Turns" value={run.num_turns ?? '—'} />
				<Metric
					label="Tokens"
					value={totalTokens ? fmtTokens(totalTokens) : '—'}
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

			{models.length > 0 && (
				<div>
					<div className="rp-sec">{models.length > 1 ? 'Models used' : 'Model used'}</div>
					<div className="overflow-x-auto rounded-lg border border-border">
						<table className="rp-mini">
							<thead>
								<tr>
									<th>Model</th>
									{hasTokens ? (
										TOKEN_COLUMNS.map(([k, l]) => (
											<th key={k} className="ra">
												{l}
											</th>
										))
									) : (
										<th className="ra">Messages</th>
									)}
									{hasTokens && <th className="ra">Cost</th>}
								</tr>
							</thead>
							<tbody>
								{models.map((name) => {
									const u = usage![name] ?? {};
									return (
										<tr key={name}>
											<td className="mono">{name}</td>
											{hasTokens ? (
												TOKEN_COLUMNS.map(([k]) => (
													<td
														key={k}
														className="ra mono"
														title={u[k] != null ? Number(u[k]).toLocaleString() : undefined}
													>
														{fmtTokens(u[k])}
													</td>
												))
											) : (
												<td className="ra mono">{fmtTokens(u.messages)}</td>
											)}
											{hasTokens && <td className="ra mono">{fmtCost(u.costUSD)}</td>}
										</tr>
									);
								})}
							</tbody>
						</table>
					</div>
					{!hasTokens && (
						<p className="mt-1 text-[12px] text-t3">
							The run ended before reporting token usage, so only the models it called are known.
						</p>
					)}
				</div>
			)}

			{tools.length > 0 && (
				<div>
					<div className="rp-sec">Tool calls ({tools.reduce((n, [, c]) => n + c, 0)})</div>
					<div className="flex flex-wrap gap-1.5">
						{tools.map(([name, count]) => (
							<span key={name} className="rp-chip">
								{name} <span className="text-t3">{count}</span>
							</span>
						))}
					</div>
				</div>
			)}

			{footnotes.length > 0 && (
				<div className="flex flex-wrap gap-x-4 gap-y-1 text-[12px] text-t3">
					{footnotes.map((f) => (
						<span key={f}>{f}</span>
					))}
				</div>
			)}
		</div>
	);
}
