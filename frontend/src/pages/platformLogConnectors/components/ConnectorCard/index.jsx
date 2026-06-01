const ACCENT_BG = {
	indigo: 'bg-[#EEF1FE] text-[#3938B5]',
	teal: 'bg-[#119C85] text-white',
	amber: 'bg-[#FCEAC4] text-[#8A5A07]',
};

export default function ConnectorCard({ component, meta, row, onEdit }) {
	const configured = !!row;
	const cfg = row?.config || {};

	return (
		<div
			className={`flex flex-col gap-[10px] rounded-[12px] border bg-white p-[18px] shadow-sm transition-all duration-200 hover:-translate-y-[2px] hover:shadow-md ${
				configured
					? 'border-[#E3E6EF]'
					: 'border-dashed border-[#D4D8E5] bg-[#FAFBFD]'
			}`}
		>
			<div className="flex items-center gap-[10px]">
				<div
					className={`flex h-[32px] w-[32px] items-center justify-center rounded-[8px] ${
						configured ? ACCENT_BG[meta.accent] : 'bg-[#F0F2F7] text-[#8389A3]'
					}`}
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="16"
						height="16"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						strokeWidth="2"
					>
						<rect x="3" y="4" width="18" height="16" rx="2" />
						<path d="M3 10h18" />
					</svg>
				</div>
				<div className="flex-1">
					<div className="text-[13.5px] font-semibold text-[#0B0D14]">
						{meta.label}
					</div>
					<div className="text-[11px] text-[#5A607A]">{meta.sub}</div>
				</div>
				{configured ? (
					<span className="inline-flex items-center gap-[4px] rounded-full bg-[#EFF7EE] px-[8px] py-[2px] text-[10.5px] font-medium text-[#36713A]">
						<span className="h-[6px] w-[6px] rounded-full bg-[#5AA45B]" />
						Configured
					</span>
				) : (
					<span className="rounded-full bg-[#F0F2F7] px-[8px] py-[2px] text-[10.5px] font-medium text-[#8389A3]">
						Not configured
					</span>
				)}
			</div>

			<div
				className={`grid grid-cols-[max-content_1fr] gap-x-[10px] gap-y-[3px] rounded-[8px] bg-[#F0F2F7] p-[10px] font-mono text-[10.5px] ${
					configured ? '' : 'opacity-50'
				}`}
			>
				<span className="text-[#8389A3]">type</span>
				<span className="font-medium text-[#0B0D14]">
					{row?.connector || '—'}
				</span>
				<span className="text-[#8389A3]">region</span>
				<span className="font-medium text-[#0B0D14]">{cfg.region || '—'}</span>
				<span className="text-[#8389A3]">group</span>
				<span className="truncate font-medium text-[#0B0D14]">
					{cfg.log_group_name || '—'}
				</span>
				<span className="text-[#8389A3]">format</span>
				<span className="font-medium text-[#0B0D14]">{cfg.format || '—'}</span>
			</div>

			<div className="flex gap-[6px] border-t border-[#ECEEF5] pt-[8px]">
				<button
					type="button"
					onClick={onEdit}
					className={`flex-1 rounded-[8px] px-[12px] py-[5px] text-[12px] font-medium ${
						configured
							? 'bg-white text-[#2C3047] hover:bg-[#F0F2F7] border border-[#D4D8E5]'
							: 'bg-[#0B0D14] text-white hover:bg-[#14172A]'
					}`}
				>
					{configured ? 'Edit' : '+ Configure'}
				</button>
			</div>
		</div>
	);
}
