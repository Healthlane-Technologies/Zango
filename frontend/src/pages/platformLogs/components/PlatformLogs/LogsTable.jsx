import { Fragment, useState } from 'react';
import DetailCard from '../../../appLogs/components/RuntimeLogs/DetailCard';

const LEVEL_BADGE = {
	debug: 'bg-[#F4F5F8] text-[#3D4159]',
	info: 'bg-[#EEF1FE] text-[#3938B5]',
	warning: 'bg-[#FEF6E7] text-[#8A5A07]',
	error: 'bg-[#FCEDEF] text-[#931F2A]',
	critical: 'bg-[#F8D5D9] text-[#931F2A]',
	unknown: 'bg-[#F4F5F8] text-[#5A607A]',
};

// Verbose formatter prefixes every line with "[<schema>:<domain>] ".
// Pull the schema out so each row can show which tenant it came from.
const TENANT_RE = /^\[([^:\]]+):([^\]]*)\]\s*/;

function parseTenantPrefix(message) {
	if (!message) return { schema: null, rest: message || '' };
	const m = TENANT_RE.exec(message);
	if (!m) return { schema: null, rest: message };
	return { schema: m[1], domain: m[2], rest: message.slice(m[0].length) };
}

function formatTime(ts) {
	if (!ts) return '';
	try {
		const d = new Date(ts);
		const hh = String(d.getHours()).padStart(2, '0');
		const mm = String(d.getMinutes()).padStart(2, '0');
		const ss = String(d.getSeconds()).padStart(2, '0');
		const ms = String(d.getMilliseconds()).padStart(3, '0');
		return `${hh}:${mm}:${ss}.${ms}`;
	} catch {
		return ts;
	}
}

function rowKey(line, idx) {
	return `${line.ts}-${line.stream}-${line.cursor_token || idx}`;
}

function copyText(text) {
	if (navigator.clipboard) navigator.clipboard.writeText(text);
}

export default function LogsTable({
	lines,
	initialLoading,
	loadingEarlier,
	hasMoreEarlier,
	onLoadEarlier,
	showStream = true,
	showLevel = true,
	showTenant = true,
	wrapMessage = false,
}) {
	const [expandedKey, setExpandedKey] = useState(null);

	if (initialLoading && (!lines || lines.length === 0)) {
		return (
			<div className="flex flex-col items-center justify-center py-[60px] text-center">
				<div className="mb-[10px] h-[18px] w-[18px] animate-spin rounded-full border-2 border-[#5961E5] border-t-transparent" />
				<div className="text-[13px] text-[#5A607A]">Loading logs…</div>
			</div>
		);
	}

	if (!lines || lines.length === 0) {
		return (
			<div className="flex flex-col items-center justify-center py-[60px] text-center">
				<div className="mb-[10px] text-[36px] opacity-30">≡</div>
				<div className="text-[14px] font-semibold text-[#0B0D14]">
					No lines in this window yet
				</div>
				<div className="mt-[3px] text-[12px] text-[#5A607A]">
					Waiting for the next poll · widen the time range or pick another tenant.
				</div>
			</div>
		);
	}

	const colCount =
		1 +
		(showLevel ? 1 : 0) +
		(showTenant ? 1 : 0) +
		(showStream ? 1 : 0) +
		1;

	return (
		<div className="w-full overflow-auto rounded-[10px] border border-[#E3E6EF] bg-white">
			<table className="w-full table-fixed font-mono text-[11px]">
				<thead className="sticky top-0 z-10">
					<tr>
						<Th width="130px">Time</Th>
						{showLevel && <Th width="76px">Level</Th>}
						{showTenant && <Th width="130px">Tenant</Th>}
						{showStream && <Th width="130px">Stream</Th>}
						<Th>Message</Th>
					</tr>
				</thead>
				<tbody>
					{lines.map((line, idx) => {
						const key = rowKey(line, idx);
						const isExpanded = expandedKey === key;
						const isFresh = line._fresh;
						const { schema, domain, rest } = parseTenantPrefix(line.message);
						return (
							<Fragment key={key}>
								<tr
									onClick={() => setExpandedKey(isExpanded ? null : key)}
									className={`cursor-pointer border-b border-[#ECEEF5] transition-colors ${
										isExpanded ? 'bg-[#EEF1FE]' : 'hover:bg-[#F0F2F7]'
									} ${isFresh ? 'animate-[runtime-pulse_1.6s_ease-out]' : ''}`}
								>
									<td className="px-[14px] py-[6px] align-top text-[#8389A3]">
										{formatTime(line.ts)}
									</td>
									{showLevel && (
										<td className="px-[14px] py-[6px] align-top">
											<span
												className={`inline-flex h-[18px] items-center justify-center rounded-[3px] px-[7px] font-sans text-[10px] font-semibold uppercase tracking-[0.03em] ${
													LEVEL_BADGE[line.level] || LEVEL_BADGE.unknown
												}`}
											>
												{line.level}
											</span>
										</td>
									)}
									{showTenant && (
										<td className="px-[14px] py-[6px] align-top">
											{schema ? (
												<span
													className="inline-block max-w-full truncate rounded-[3px] border border-[#DCE3FD] bg-[#EEF1FE] px-[6px] py-[1px] text-[10.5px] font-medium text-[#3938B5]"
													title={domain ? `${schema} · ${domain}` : schema}
												>
													{schema}
												</span>
											) : (
												<span className="text-[10px] text-[#C2C8D8]">—</span>
											)}
										</td>
									)}
									{showStream && (
										<td className="px-[14px] py-[6px] align-top">
											<span className="inline-block max-w-full truncate rounded-[3px] border border-[#ECEEF5] bg-[#F0F2F7] px-[6px] py-[1px] text-[10.5px] text-[#5A607A]">
												{line.stream}
											</span>
										</td>
									)}
									<td
										className={`px-[14px] py-[6px] align-top text-[#2C3047] ${
											wrapMessage ? 'whitespace-pre-wrap break-all' : 'truncate'
										}`}
									>
										{showTenant && schema ? rest : line.message}
									</td>
								</tr>
								{isExpanded && (
									<tr className="bg-[#EEF1FE]">
										<td colSpan={colCount} className="px-[14px] pb-[14px]">
											<DetailCard
												line={line}
												onCopy={copyText}
												onCopyJson={(l) => copyText(JSON.stringify(l, null, 2))}
											/>
										</td>
									</tr>
								)}
							</Fragment>
						);
					})}
				</tbody>
			</table>

			<div className="border-t border-[#ECEEF5] bg-[#FAFBFD] px-[14px] py-[10px] text-center">
				{hasMoreEarlier ? (
					<button
						type="button"
						onClick={onLoadEarlier}
						disabled={loadingEarlier}
						className="inline-flex items-center gap-[6px] rounded-[6px] border border-[#D4D8E5] bg-white px-[14px] py-[5px] text-[11.5px] font-medium text-[#2C3047] hover:bg-[#F0F2F7] disabled:cursor-not-allowed disabled:opacity-50"
					>
						{loadingEarlier ? (
							<>
								<span className="h-[10px] w-[10px] animate-spin rounded-full border-[1.5px] border-[#5961E5] border-t-transparent" />
								Loading older lines…
							</>
						) : (
							<>
								↓ Load earlier
								<span className="text-[10px] text-[#8389A3]">
									(within the selected range)
								</span>
							</>
						)}
					</button>
				) : (
					<span className="text-[10.5px] text-[#8389A3]">
						No more lines in this time range.
					</span>
				)}
			</div>

			<style>{`
				@keyframes runtime-pulse {
					0% { background-color: rgba(90,164,91,0.18); }
					100% { background-color: transparent; }
				}
			`}</style>
		</div>
	);
}

function Th({ width, children }) {
	return (
		<th
			style={{ width }}
			className="border-b border-[#E3E6EF] bg-[#FAFBFD] px-[14px] py-[8px] text-left font-sans text-[10px] font-semibold uppercase tracking-[0.08em] text-[#8389A3]"
		>
			{children}
		</th>
	);
}
