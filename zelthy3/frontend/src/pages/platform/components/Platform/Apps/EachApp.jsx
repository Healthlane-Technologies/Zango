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
	let port = document.location.port;
	let protocol = document.location.protocol;

	const [isBookmarked, setIsBookmarked] = useState(false);

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
			to={`${uuid}/app-settings/app-configuration/`}
			className="group relative flex w-full flex-col rounded-[8px] border border-[#DDE2E5] hover:border-[#8485F6] hover:shadow-eachApp"
		>
			<div className="relative flex flex-col border-b border-[#F0F3F4] px-[16px] py-[22px]">
				{logo ? (
					<img
						src={logo}
						alt="#"
						className="max-h-[32px] min-h-[32px] w-fit object-contain"
					/>
				) : (
					<EachAppIcon className="mt-[6px] min-h-[32px] min-w-[32px]" />
				)}

				<div className="absolute bottom-[-10px] flex items-center gap-[8px]">
					<div className="flex items-center gap-[4px] rounded-[16px] bg-[#F0F3F4] px-[8px] py-[4px]">
						<EachAppRocketIcon className="min-h-[12px] min-w-[12px]" />
						<span className="font-lato text-[9px] font-bold leading-[8px] tracking-[0.2px] text-[#495057]">
							{formatLaunchDate(created_at)}
						</span>
					</div>
					{isRecentlyLaunched(created_at) ? (
						<div className="flex items-center gap-[4px] rounded-[16px] bg-[#E4F9F2] px-[8px] py-[6px]">
							<span className="font-lato text-[9px] font-bold leading-[8px] tracking-[0.2px] text-[#186A50]">
								Recently Launched
							</span>
						</div>
					) : null}
				</div>
			</div>
			<div className="flex grow flex-col gap-[28px] px-[16px] pt-[22px] pb-[16px]">
				<div className="flex grow flex-col gap-[8px]">
					<span className="font-lato text-[12px] font-bold uppercase leading-[20px] tracking-[0.6px] text-[#A3ABB1]">
						App ID: {uuid?.slice(0, 7)}
					</span>
					<span className="font-source-sans-pro text-[18px] font-semibold leading-[24px] tracking-[-0.2px] text-[#212429]">
						{name}
					</span>
					<span className="truncate font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#212429]">
						{description}
					</span>
				</div>
				<div className="flex flex-col gap-[8px]">
					<span className="font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#000000]">
						Modified {getTimeFromNow(modified_at)}
					</span>
					{domain_url ? (
						<button
							type="button"
							onClick={(event) =>
								handleUrlButtonClick(
									event,
									protocol + '//' + domain_url + (port ? `:${port}` : '')
								)
							}
							data-url={protocol + '//' + domain_url + (port ? `:${port}` : '')}
							className="w-fit"
						>
							<span className="font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-primary">
								{protocol + '//' + domain_url + (port ? `:${port}` : '')}
							</span>
						</button>
					) : null}
				</div>
			</div>
			{/* <button
				type="button"
				className={`absolute top-[16px] right-[16px] rounded-[2px] bg-[#F0F3F4] p-[4px] ${
					isBookmarked ? 'flex' : 'hidden group-hover:flex'
				}`}
				onClick={handleToggleBookmark}
			>
				<EachAppStarBookmarkIcon
					className={` ${isBookmarked ? 'text-[#FC9E01]' : 'text-[#A3ABB1]'}`}
				/>
			</button> */}
		</Link>
	);
}
