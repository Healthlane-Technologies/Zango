import { ReactComponent as UsersIcon } from '../../../../assets/images/svg/app-user-management-icon.svg';
import { ReactComponent as ClockIcon } from '../../../../assets/images/svg/refresh-icon.svg';
import { ReactComponent as CheckCircleIcon } from '../../../../assets/images/svg/checkbox-tick.svg';

export default function QuickStats({ stats }) {
	// Default stats for now - will be populated from API
	const defaultStats = [
		{
			label: 'Total Users',
			value: stats?.totalUsers || '-',
			icon: UsersIcon,
			color: 'text-[#5048ED]',
			bgColor: 'bg-[#F0EFFF]',
		},
		{
			label: 'Active Sessions',
			value: stats?.activeSessions || '-',
			icon: CheckCircleIcon,
			color: 'text-[#2CBE90]',
			bgColor: 'bg-[#E4F9F2]',
		},
		{
			label: 'Last Modified',
			value: stats?.lastModified || '-',
			icon: ClockIcon,
			color: 'text-[#F59E0B]',
			bgColor: 'bg-[#FEF3C7]',
		},
	];

	return (
		<div className="grid grid-cols-1 gap-[16px] sm:grid-cols-2 lg:grid-cols-3">
			{defaultStats.map((stat, index) => {
				const Icon = stat.icon;
				return (
					<div
						key={index}
						className="flex items-center gap-[16px] rounded-[8px] border border-[#DDE2E5] bg-white p-[20px]"
					>
						<div className={`rounded-[8px] p-[12px] ${stat.bgColor}`}>
							<Icon className={`h-[24px] w-[24px] ${stat.color}`} />
						</div>
						<div className="flex flex-col">
							<span className="font-lato text-[12px] font-medium uppercase tracking-[0.6px] text-[#6C747D]">
								{stat.label}
							</span>
							<span className="font-source-sans-pro text-[24px] font-semibold text-[#212429]">
								{stat.value}
							</span>
						</div>
					</div>
				);
			})}
		</div>
	);
}