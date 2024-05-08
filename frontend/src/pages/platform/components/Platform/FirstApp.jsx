import LaunchNewAppButton from './LaunchNewAppButton';

export default function FirstApp() {
	return (
		<div className="px-[48px] py-[24px] flex grow flex-col">
			<span className="text-[22px] leading-[28px] text-[#000000] font-source-sans-pro font-semibold">
				Apps
			</span>
			<div className="gap-[56px] flex grow flex-col items-center justify-center">
				<div className="gap-[8px] flex flex-col items-center justify-center">
					<h3 className="first-app-text text-[64px] font-[700] leading-[72px] font-source-sans-pro">
						start by launching your first app
					</h3>
					<p className="text-[18px] leading-[24px] text-[#212429] font-source-sans-pro font-semibold">
						setting up an app have never been so easy and seamless
					</p>
				</div>
				<div>
					<LaunchNewAppButton />
				</div>
			</div>
		</div>
	);
}
