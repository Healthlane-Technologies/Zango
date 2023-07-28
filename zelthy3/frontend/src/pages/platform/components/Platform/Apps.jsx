import { ReactComponent as LaunchNewAppIcon } from '../../../../assets/images/svg/launch-new-app-icon.svg';

export default function Apps() {
	return (
		<div className="flex grow flex-col gap-[32px] px-[48px] py-[24px]">
			<div className="flex items-center justify-between">
				<span className="font-source-sans-pro text-[22px] font-semibold leading-[28px] text-[#000000]">
					Apps
				</span>

				<div>
					<button className="flex grow gap-[8px] rounded-[4px] bg-[#5048ED] px-[16px] py-[7px]">
						<span className="font-lato text-[14px] font-bold leading-[20px] text-[#FFFFFF]">
							Launch New App
						</span>
						<LaunchNewAppIcon />
					</button>
				</div>
			</div>
			<div className="flex grow flex-col gap-[16px]">
				<div className="flex items-center justify-end gap-[8px]">
					<span className="font-lato text-[14px] leading-[20px] tracking-[0.2px] text-[#A3ABB1]">
						Sort:
					</span>
					<div>
						<span className="font-lato text-[14px] leading-[20px] text-[#000000]">
							Alphabetical
						</span>
					</div>
				</div>
				<div className="flex grow flex-wrap items-start gap-[26px]">
					<div>asd</div>
				</div>
			</div>
		</div>
	);
}
