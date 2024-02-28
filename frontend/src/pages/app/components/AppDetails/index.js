import { ReactComponent as LaunchNewAppIcon } from '../../../../assets/images/svg/launch-new-app-icon.svg';

export default function AppDetails() {
	return (
		<div className="flex grow flex-col px-[48px] py-[24px]">
			<span className="font-source-sans-pro text-[22px] font-semibold leading-[28px] text-[#000000]">
				Apps
			</span>
			<div className="flex grow flex-col items-center justify-center gap-[56px]">
				<div className="flex flex-col items-center justify-center gap-[8px]">
					<h3 className="first-app-text font-source-sans-pro text-[64px] font-[700] leading-[72px]">
						start by launching your first app
					</h3>
					<p className="font-source-sans-pro text-[18px] font-semibold leading-[24px] text-[#212429]">
						setting up an app have never been so easy and seamless
					</p>
				</div>
				<div>
					<button className="flex grow gap-[8px] rounded-[4px] bg-primary px-[16px] py-[7px]">
						<span className="font-lato text-[14px] font-bold leading-[20px] text-[#FFFFFF]">
							Launch New App
						</span>
						<LaunchNewAppIcon />
					</button>
				</div>
			</div>
		</div>
	);
}
