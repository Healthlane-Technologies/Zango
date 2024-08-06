import { Link } from 'react-router-dom';
import { ReactComponent as EachAppIcon } from '../../../../../../assets/images/svg/each-app-icon.svg';
import { ReactComponent as EachAppRocketIcon } from '../../../../../../assets/images/svg/each-app-rocket-icon.svg';
import {
	formatLaunchDate,
	getTimeFromNow,
	isRecentlyLaunched,
} from '../../../../../../utils/formats';
import AppLinkButton from './AppLinkButton';

export default function EachApp({ data }) {
	const { uuid, name, domain_url, description, logo, created_at, modified_at } =
		data;

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
			<div data-cy="app_list" className="flex grow flex-col gap-[28px] px-[16px] pb-[16px] pt-[22px]">
				<div className="flex grow flex-col gap-[8px]">
					<span data-cy="app_id" className="font-lato text-[12px] font-bold uppercase leading-[20px] tracking-[0.6px] text-[#A3ABB1]">
						App ID: {uuid?.slice(0, 7)}
					</span>
					<span data-cy="app_name" className="font-source-sans-pro text-[18px] font-semibold leading-[24px] tracking-[-0.2px] text-[#212429]">
						{name}
					</span>
					<span data-cy="app_description "className="truncate font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#212429]">
						{description}
					</span>
				</div>
				<div data-cy="domain_url" className="flex flex-col gap-[8px]">
					<span className="font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#000000]">
						Modified {getTimeFromNow(modified_at)}
					</span> 
					{domain_url ? <AppLinkButton domain_url={domain_url} /> : null}
				</div>
			</div>
		</Link>
	);
}
