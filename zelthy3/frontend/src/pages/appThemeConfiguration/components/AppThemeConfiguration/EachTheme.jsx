export default function EachTheme({ data }) {
	let { theme_name, status, font_family, colors } = data;

	return (
		<div className="flex flex-col rounded-[8px] border border-[#DDE2E5] bg-[#FFFFFF]">
			<div className="flex flex-col gap-[8px] px-[16px] pt-[24px] pb-[16px]">
				<h4 className="font-source-sans-pro text-[18px] font-semibold leading-[24px] tracking-[-0.2px] text-[#212429]">
					{theme_name}
				</h4>
				<span
					className={`w-fit rounded-[13px]  px-[8px] py-[5px] font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.4px] text-[#FFFFFF] ${
						status === 'active' ? 'bg-[#2CBE90]' : 'bg-[#DDE2E5] text-[#6C747D]'
					}`}
				>
					{status}
				</span>
			</div>
			<hr></hr>
			<div className="flex flex-col gap-[16px] px-[16px] py-[16px]">
				<div className="flex flex-col">
					<span className="font-lato text-[14px] leading-[20px] tracking-[0.2px] text-[#212429]">
						{font_family}
					</span>
					<span className="font-source-sans-pro text-[26px] leading-[32px] tracking-[-0.2px] text-[#A3ABB1]">
						Aa Bb Cc Dd Ee
					</span>
				</div>
				<div className="flex flex-col gap-[4px]">
					<span className="font-lato text-[14px] leading-[20px] tracking-[0.2px] text-[#212429]">
						Color
					</span>
					<div className="flex gap-[8px]">
						<span
							className={`h-[24px] min-h-[24px] w-[24px] min-w-[24px] rounded-[4px] border border-[#DDE2E5] bg-[${colors.primary}]`}
							style={{ backgroundColor: colors.primary }}
						></span>
						<span
							className={`h-[24px] min-h-[24px] w-[24px] min-w-[24px] rounded-[4px] border border-[#DDE2E5] bg-[${colors.secondary}]`}
							style={{ backgroundColor: colors.secondary }}
						></span>
					</div>
				</div>
				<div className="flex flex-col gap-[8px]">
					<span className="font-lato text-[14px] leading-[20px] tracking-[0.2px] text-[#212429]">
						CTA Example
					</span>
					<button
						type="button"
						className={`rounded-[4px] bg-[${colors.primary}] p-[11px]`}
						style={{ backgroundColor: colors.primary }}
					>
						<span
							className={`font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[${colors.secondary}]`}
							style={{ color: colors.secondary }}
						>
							Button/CTA
						</span>
					</button>
				</div>
			</div>
		</div>
	);
}
