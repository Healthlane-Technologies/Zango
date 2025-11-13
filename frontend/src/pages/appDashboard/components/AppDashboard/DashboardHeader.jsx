import { Link } from 'react-router-dom';
import { ReactComponent as ExternalLinkIcon } from '../../../../assets/images/svg/popout-icon.svg';

export default function DashboardHeader({ appData }) {
	if (!appData) {
		return (
			<div className="animate-pulse">
				<div className="h-8 w-48 bg-gray-200 rounded"></div>
			</div>
		);
	}

	return (
		<div className="flex items-start justify-between">
			<div className="flex items-center gap-[24px]">
				{/* App Logo */}
				{appData.logo ? (
					<img
						src={appData.logo}
						alt={appData.name}
						className="h-[60px] w-[60px] rounded-[8px] object-contain"
					/>
				) : (
					<div className="flex h-[60px] w-[60px] items-center justify-center rounded-[8px] bg-[#5048ED] text-white">
						<span className="text-[24px] font-bold">
							{appData.name?.charAt(0)?.toUpperCase()}
						</span>
					</div>
				)}

				{/* App Info */}
				<div className="flex flex-col gap-[4px]">
					<h1 className="font-source-sans-pro text-[28px] font-semibold leading-[36px] text-[#212429]">
						{appData.name}
					</h1>
					<p className="font-lato text-[14px] leading-[20px] text-[#6C747D]">
						{appData.description || 'No description available'}
					</p>
				</div>
			</div>

			{/* Quick Actions */}
			<div className="flex items-center gap-[12px]">
				{appData.domain && (
					<a
						href={`https://${appData.domain}`}
						target="_blank"
						rel="noopener noreferrer"
						className="flex items-center gap-[8px] rounded-[4px] border border-[#DDE2E5] bg-white px-[16px] py-[8px] transition-colors hover:bg-[#F0F3F4]"
					>
						<span className="font-lato text-[14px] font-medium text-[#212429]">
							Launch App
						</span>
						<ExternalLinkIcon className="h-[16px] w-[16px]" />
					</a>
				)}
				
				<Link
					to={`/platform/apps/${appData.id}/app-settings/app-configuration`}
					className="rounded-[4px] border border-[#DDE2E5] bg-white px-[16px] py-[8px] font-lato text-[14px] font-medium text-[#212429] transition-colors hover:bg-[#F0F3F4]"
				>
					Settings
				</Link>
			</div>
		</div>
	);
}