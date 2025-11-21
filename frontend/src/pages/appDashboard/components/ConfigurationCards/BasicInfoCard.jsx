import { Link } from 'react-router-dom';
import { ReactComponent as SettingsIcon } from '../../../../assets/images/svg/app-settings-icon.svg';
import { ReactComponent as ArrowRightIcon } from '../../../../assets/images/svg/table-pagination-next-icon.svg';

export default function BasicInfoCard({ appData }) {
	const isConfigured = appData?.domain && appData?.timezone;

	return (
		<div className="flex flex-col rounded-[12px] border border-[#DDE2E5] bg-white p-[24px]">
			{/* Card Header */}
			<div className="mb-[20px] flex items-start justify-between">
				<div className="flex items-center gap-[12px]">
					<div className="rounded-[8px] bg-[#F0EFFF] p-[10px]">
						<SettingsIcon className="h-[20px] w-[20px] text-[#5048ED]" />
					</div>
					<div>
						<h3 className="font-source-sans-pro text-[18px] font-semibold text-[#212429]">
							Basic Information
						</h3>
						<p className="font-lato text-[12px] text-[#6C747D]">
							App details and settings
						</p>
					</div>
				</div>
				<span
					className={`rounded-[20px] px-[8px] py-[2px] text-[11px] font-medium ${
						isConfigured
							? 'bg-[#E4F9F2] text-[#2CBE90]'
							: 'bg-[#FEF3C7] text-[#F59E0B]'
					}`}
				>
					{isConfigured ? 'Configured' : 'Incomplete'}
				</span>
			</div>

			{/* Card Content */}
			<div className="mb-[20px] flex flex-col gap-[12px]">
				<div className="flex justify-between">
					<span className="font-lato text-[14px] text-[#6C747D]">Domain</span>
					<span className="font-lato text-[14px] font-medium text-[#212429]">
						{appData?.domain || 'Not set'}
					</span>
				</div>
				<div className="flex justify-between">
					<span className="font-lato text-[14px] text-[#6C747D]">Timezone</span>
					<span className="font-lato text-[14px] font-medium text-[#212429]">
						{appData?.timezone || 'Not set'}
					</span>
				</div>
				<div className="flex justify-between">
					<span className="font-lato text-[14px] text-[#6C747D]">Template</span>
					<span className="font-lato text-[14px] font-medium text-[#212429]">
						{appData?.template || 'No template'}
					</span>
				</div>
			</div>

			{/* Card Footer */}
			<Link
				to={`/platform/apps/${appData?.id}/app-settings/app-configuration/`}
				className="mt-auto flex items-center justify-between rounded-[6px] border border-[#DDE2E5] px-[16px] py-[12px] transition-colors hover:bg-[#F0F3F4]"
			>
				<span className="font-lato text-[14px] font-medium text-[#212429]">
					View Details
				</span>
				<ArrowRightIcon className="h-[16px] w-[16px] text-[#6C747D]" />
			</Link>
		</div>
	);
}