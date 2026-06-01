const LEVEL_BADGE = {
	debug: 'bg-[#F4F5F8] text-[#3D4159]',
	info: 'bg-[#EEF1FE] text-[#3938B5]',
	warning: 'bg-[#FEF6E7] text-[#8A5A07]',
	error: 'bg-[#FCEDEF] text-[#931F2A]',
	critical: 'bg-[#F8D5D9] text-[#931F2A]',
	unknown: 'bg-[#F4F5F8] text-[#5A607A]',
};

function formatTs(ts) {
	if (!ts) return '—';
	try {
		const d = new Date(ts);
		return d.toLocaleString();
	} catch {
		return ts;
	}
}

export default function DetailCard({ line, onCopy, onCopyJson }) {
	const meta = line.structured || {};
	return (
		<div className="rounded-[10px] border border-[#DCE3FD] bg-white p-[14px] shadow-sm">
			<div className="mb-[12px] grid grid-cols-2 gap-[1px] overflow-hidden rounded-[8px] border border-[#ECEEF5] bg-[#ECEEF5] md:grid-cols-4">
				<MetaCell label="Timestamp" value={formatTs(line.ts)} mono />
				<MetaCell
					label="Level"
					value={
						<span
							className={`inline-flex h-[18px] items-center rounded-[3px] px-[7px] text-[10px] font-semibold uppercase tracking-[0.03em] ${
								LEVEL_BADGE[line.level] || LEVEL_BADGE.unknown
							}`}
						>
							{line.level}
						</span>
					}
				/>
				<MetaCell label="Stream" value={line.stream} mono />
				<MetaCell label="App" value={meta.app_name || '—'} mono />
				{meta.request_id && <MetaCell label="Request ID" value={meta.request_id} mono />}
				{meta.task_id && <MetaCell label="Task ID" value={meta.task_id} mono />}
				{meta.path && <MetaCell label="Path" value={meta.path} mono />}
				{meta.pathname && <MetaCell label="Source" value={meta.pathname} mono />}
			</div>

			<div className="mb-[6px] text-[10px] font-semibold uppercase tracking-[0.08em] text-[#8389A3]">
				Message
			</div>
			<pre className="mb-[12px] whitespace-pre-wrap break-words rounded-[8px] bg-[#0F1117] px-[14px] py-[12px] font-mono text-[11.5px] leading-[1.65] text-[#E1E4ED]">
				{line.message}
			</pre>

			<div className="flex items-center gap-[8px] border-t border-[#ECEEF5] pt-[10px]">
				<button
					type="button"
					onClick={() => onCopy(line.message)}
					className="inline-flex items-center gap-[5px] rounded-[8px] border border-[#D4D8E5] bg-white px-[11px] py-[5px] text-[11.5px] font-medium text-[#2C3047] hover:bg-[#F0F2F7]"
				>
					Copy line
				</button>
				<button
					type="button"
					onClick={() => onCopyJson(line)}
					className="inline-flex items-center gap-[5px] rounded-[8px] border border-[#D4D8E5] bg-white px-[11px] py-[5px] text-[11.5px] font-medium text-[#2C3047] hover:bg-[#F0F2F7]"
				>
					Copy as JSON
				</button>
			</div>
		</div>
	);
}

function MetaCell({ label, value, mono }) {
	return (
		<div className="bg-white px-[12px] py-[8px]">
			<div className="mb-[3px] text-[9.5px] font-semibold uppercase tracking-[0.08em] text-[#8389A3]">
				{label}
			</div>
			<div
				className={`text-[11px] font-medium text-[#0B0D14] ${
					mono ? 'font-mono' : ''
				}`}
			>
				{value}
			</div>
		</div>
	);
}
