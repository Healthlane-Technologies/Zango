import { useEffect } from 'react';
import WebFont from 'webfontloader';
import EachThemeMenu from './EachThemeMenu';

export default function EachTheme({ data }) {
	let { id, name, is_active, config } = data;

	useEffect(() => {
		WebFont.load({
			google: {
				families: [`${config?.typography?.font_family}`],
			},
		});
	}, [data]);

	return (
		<div className="relative flex flex-col rounded-[8px] border border-[#DDE2E5] bg-[#FFFFFF]">
			<div className="flex flex-col gap-[8px] px-[16px] pb-[16px] pt-[24px]">
				<h4 className="font-source-sans-pro text-[18px] font-semibold leading-[24px] tracking-[-0.2px] text-[#212429]">
					{name}
				</h4>
				<span
					className={`w-fit rounded-[13px]  px-[8px] py-[5px] font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.4px] text-[#FFFFFF] ${
						is_active ? 'bg-[#2CBE90]' : 'bg-[#DDE2E5] text-[#6C747D]'
					}`}
				>
					{is_active ? 'Active' : 'InActive'}
				</span>
			</div>
			<hr></hr>
			<div className="flex flex-col gap-[16px] px-[16px] py-[16px]">
				<div className="flex flex-col">
					<span className="font-lato text-[14px] leading-[20px] tracking-[0.2px] text-[#212429]">
						{config?.typography?.font_family}
					</span>
					<span
						className="font-source-sans-pro text-[26px] leading-[32px] tracking-[-0.2px] text-[#A3ABB1]"
						style={{ fontFamily: config?.typography?.font_family }}
					>
						Aa Bb Cc Dd Ee
					</span>
				</div>
				<div className="flex flex-col gap-[4px]">
					<span className="font-lato text-[14px] leading-[20px] tracking-[0.2px] text-[#212429]">
						Colors
					</span>
					<div className="grid grid-cols-3 gap-[8px]">
						<div className="flex flex-col items-center gap-[2px]">
							<span
								className={`h-[24px] min-h-[24px] w-[24px] min-w-[24px] rounded-[4px] border border-[#DDE2E5]`}
								style={{ backgroundColor: config?.colors?.primary }}
								title="Primary"
							></span>
							<span className="font-lato text-[10px] text-[#6C747D]">Primary</span>
						</div>
						<div className="flex flex-col items-center gap-[2px]">
							<span
								className={`h-[24px] min-h-[24px] w-[24px] min-w-[24px] rounded-[4px] border border-[#DDE2E5]`}
								style={{ backgroundColor: config?.colors?.gray }}
								title="Gray"
							></span>
							<span className="font-lato text-[10px] text-[#6C747D]">Gray</span>
						</div>
						<div className="flex flex-col items-center gap-[2px]">
							<span
								className={`h-[24px] min-h-[24px] w-[24px] min-w-[24px] rounded-[4px] border border-[#DDE2E5]`}
								style={{ backgroundColor: config?.colors?.success }}
								title="Success"
							></span>
							<span className="font-lato text-[10px] text-[#6C747D]">Success</span>
						</div>
						<div className="flex flex-col items-center gap-[2px]">
							<span
								className={`h-[24px] min-h-[24px] w-[24px] min-w-[24px] rounded-[4px] border border-[#DDE2E5]`}
								style={{ backgroundColor: config?.colors?.warning }}
								title="Warning"
							></span>
							<span className="font-lato text-[10px] text-[#6C747D]">Warning</span>
						</div>
						<div className="flex flex-col items-center gap-[2px]">
							<span
								className={`h-[24px] min-h-[24px] w-[24px] min-w-[24px] rounded-[4px] border border-[#DDE2E5]`}
								style={{ backgroundColor: config?.colors?.error }}
								title="Error"
							></span>
							<span className="font-lato text-[10px] text-[#6C747D]">Error</span>
						</div>
						<div className="flex flex-col items-center gap-[2px]">
							<span
								className={`h-[24px] min-h-[24px] w-[24px] min-w-[24px] rounded-[4px] border border-[#DDE2E5]`}
								style={{ backgroundColor: config?.colors?.info }}
								title="Info"
							></span>
							<span className="font-lato text-[10px] text-[#6C747D]">Info</span>
						</div>
					</div>
				</div>
				<div className="flex flex-col gap-[4px]">
					<span className="font-lato text-[14px] leading-[20px] tracking-[0.2px] text-[#212429]">
						Typography Details
					</span>
					<div className="flex flex-col gap-[2px]">
						<span className="font-lato text-[12px] text-[#6C747D]">
							Font Size: {config?.typography?.font_size_base || '14px'}
						</span>
						<span className="font-lato text-[12px] text-[#6C747D]">
							Line Height: {config?.typography?.line_height || 1.5}
						</span>
					</div>
				</div>
			</div>
			<div className="absolute right-[12px] top-[12px]">
				<EachThemeMenu data={data} />
			</div>
		</div>
	);
}
