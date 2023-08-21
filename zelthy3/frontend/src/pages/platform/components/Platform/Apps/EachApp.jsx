import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ReactComponent as EachAppIcon } from '../../../../../assets/images/svg/each-app-icon.svg';
import { ReactComponent as EachAppRocketIcon } from '../../../../../assets/images/svg/each-app-rocket-icon.svg';
import { ReactComponent as EachAppStarBookmarkIcon } from '../../../../../assets/images/svg/each-app-star-bookmark.svg';
import {
	formatLaunchDate,
	getTimeFromNow,
	isRecentlyLaunched,
} from '../../../../../utils/formats';

export default function EachApp({ data }) {
	const [isBookmarked, setIsBookmarked] = useState(false);

	const {
		app_id,
		name,
		status,
		domain_url,
		description,
		logo,
		launched_at,
		updated_at,
	} = data;

	const handleToggleBookmark = (event) => {
		event.preventDefault();
		setIsBookmarked((prev) => !prev);
	};

	const handleUrlButtonClick = (event, url) => {
		event.preventDefault();
		window.open(url, '_blank');
	};

	return (
		<Link
			to="apps/123"
			className="group relative flex w-full flex-col rounded-[8px] border border-[#DDE2E5] hover:border-[#8485F6] hover:shadow-eachApp"
		>
			<div className="relative flex flex-col border-b border-[#F0F3F4] px-[16px] py-[22px]">
				{logo ? (
					<img src={logo} alt="#" />
				) : (
					<EachAppIcon className="mt-[6px] min-h-[32px] min-w-[32px]" />
				)}

				<div className="absolute bottom-[-10px] flex items-center gap-[8px]">
					<div className="flex items-center gap-[4px] rounded-[16px] bg-[#F0F3F4] px-[8px] py-[4px]">
						<EachAppRocketIcon className="min-h-[12px] min-w-[12px]" />
						<span className="font-lato text-[9px] font-bold leading-[8px] tracking-[0.2px] text-[#495057]">
							{formatLaunchDate(launched_at)}
						</span>
					</div>
					{isRecentlyLaunched(launched_at) ? (
						<div className="flex items-center gap-[4px] rounded-[16px] bg-[#E4F9F2] px-[8px] py-[6px]">
							<span className="font-lato text-[9px] font-bold leading-[8px] tracking-[0.2px] text-[#186A50]">
								Recently Launched
							</span>
						</div>
					) : null}
				</div>
			</div>
			<div className="flex flex-col gap-[28px] px-[16px] pt-[22px] pb-[16px]">
				<div className="flex flex-col gap-[8px]">
					<span className="font-lato text-[12px] font-bold uppercase leading-[20px] tracking-[0.6px] text-[#A3ABB1]">
						App ID: {app_id}
					</span>
					<span className="font-source-sans-pro text-[18px] font-semibold leading-[24px] tracking-[-0.2px] text-[#212429]">
						{name}
					</span>
					<span className="font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#212429]">
						{description}
					</span>
				</div>
				<div className="flex flex-col gap-[8px]">
					<span className="font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#000000]">
						Modified {getTimeFromNow(updated_at)}
					</span>
					<button
						type="button"
						onClick={(event) => handleUrlButtonClick(event, domain_url)}
						data-url={domain_url}
						className="w-fit"
					>
						<span className="font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-primary">
							{domain_url}
						</span>
					</button>
				</div>
			</div>
			<button
				type="button"
				className={`absolute top-[16px] right-[16px] rounded-[2px] bg-[#F0F3F4] p-[4px] ${
					isBookmarked ? 'flex' : 'hidden group-hover:flex'
				}`}
				onClick={handleToggleBookmark}
			>
				<EachAppStarBookmarkIcon
					className={` ${isBookmarked ? 'text-[#FC9E01]' : 'text-[#A3ABB1]'}`}
				/>
			</button>
		</Link>
	);
}
