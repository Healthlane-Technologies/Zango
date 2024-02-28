import launchingAppLoaderGif from '../../../../../assets/images/gif/launching-app-loader.gif';
import Lottie from 'lottie-react';
import animationData from '../../../../../assets/images/zelthy-loader.json';
export default function LaunchingApp({ data }) {
	const {
		uuid,
		name,
		status,
		domain_url,
		description,
		logo,
		created_at,
		modified_at,
	} = data;

	return (
		<div
			to="app/123"
			className="relative flex w-full flex-col rounded-[8px] border border-[#DDE2E5]"
		>
			<div className="flex grow flex-col justify-between gap-[28px] px-[16px] pt-[22px] pb-[40px]">
				<div className="flex flex-col gap-[8px]">
					<span className="font-source-sans-pro text-[18px] font-semibold leading-[24px] tracking-[-0.2px] text-[#212429]">
						{name}
					</span>
					<span className="font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#212429]">
						{description}
					</span>
				</div>
				<div className="itens-center flex justify-center">
					{/* <img
						src={launchingAppLoaderGif}
						alt="#"
						className="h-[78px] max-h-[78px] min-h-[78px] w-[79px] min-w-[79px] max-w-[79px]"
					/> */}
					<Lottie
						animationData={animationData}
						className="lottie-container h-[78px] w-[78px] [&>svg]:!transform-none"
					/>
				</div>
				<div>
					<p className="text-center font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#212429]">
						Laying the groundwork for the app. Please check back again in a few
						minutes.
					</p>
				</div>
			</div>
		</div>
	);
}
