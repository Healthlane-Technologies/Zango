import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ReactComponent as UsersIcon } from '../../../../assets/images/svg/app-user-management-icon.svg';
import { ReactComponent as ArrowRightIcon } from '../../../../assets/images/svg/table-pagination-next-icon.svg';
import useApi from '../../../../hooks/useApi';

export default function UsersRolesCard({ appId }) {
	const [userStats, setUserStats] = useState(null);
	const [rolesData, setRolesData] = useState(null);
	const [isLoading, setIsLoading] = useState(true);
	const triggerApi = useApi();

	useEffect(() => {
		const fetchData = async () => {
			// Fetch users data
			const usersResponse = await triggerApi({
				url: `/api/v1/apps/${appId}/users/?page=1&page_size=1`,
				type: 'GET',
				loader: false,
			});

			// Fetch roles data
			const rolesResponse = await triggerApi({
				url: `/api/v1/apps/${appId}/roles/?page=1&page_size=10`,
				type: 'GET',
				loader: false,
			});
			
			if (usersResponse.success && usersResponse.response) {
				setUserStats(usersResponse.response);
			}
			
			if (rolesResponse.success && rolesResponse.response) {
				setRolesData(rolesResponse.response);
			}
			
			setIsLoading(false);
		};

		fetchData();
	}, [appId]);

	const totalUsers = userStats?.total_records || 0;
	const totalRoles = rolesData?.total_records || 0;
	const roles = Array.isArray(rolesData?.roles) ? rolesData.roles : [];
	const activeRoles = roles.filter(role => role.is_active).length;

	if (isLoading) {
		return (
			<div className="flex flex-col rounded-[12px] border border-[#DDE2E5] bg-white p-[24px]">
				<div className="animate-pulse">
					<div className="mb-[20px] h-[60px] bg-gray-200 rounded"></div>
					<div className="space-y-3">
						<div className="h-4 bg-gray-200 rounded"></div>
						<div className="h-4 bg-gray-200 rounded"></div>
					</div>
				</div>
			</div>
		);
	}

	return (
		<div className="flex flex-col rounded-[12px] border border-[#DDE2E5] bg-white p-[24px]">
			{/* Card Header */}
			<div className="mb-[20px] flex items-start justify-between">
				<div className="flex items-center gap-[12px]">
					<div className="rounded-[8px] bg-[#EDE9FE] p-[10px]">
						<UsersIcon className="h-[20px] w-[20px] text-[#7C3AED]" />
					</div>
					<div>
						<h3 className="font-source-sans-pro text-[18px] font-semibold text-[#212429]">
							Users & Roles
						</h3>
						<p className="font-lato text-[12px] text-[#6C747D]">
							Access management
						</p>
					</div>
				</div>
				{totalUsers > 0 && (
					<span className="rounded-[20px] bg-[#E4F9F2] px-[8px] py-[2px] text-[11px] font-medium text-[#2CBE90]">
						Active
					</span>
				)}
			</div>

			{/* Card Content */}
			<div className="mb-[20px] flex flex-col gap-[16px]">
				<div className="grid grid-cols-2 gap-[16px]">
					<div className="rounded-[8px] bg-[#F9FAFB] p-[12px]">
						<p className="font-lato text-[12px] text-[#6C747D]">Total Users</p>
						<p className="mt-[4px] font-source-sans-pro text-[24px] font-semibold text-[#212429]">
							{totalUsers}
						</p>
					</div>
					<div className="rounded-[8px] bg-[#F9FAFB] p-[12px]">
						<p className="font-lato text-[12px] text-[#6C747D]">Total Roles</p>
						<p className="mt-[4px] font-source-sans-pro text-[24px] font-semibold text-[#212429]">
							{totalRoles}
						</p>
					</div>
				</div>

				{roles.length > 0 && (
					<div>
						<span className="font-lato text-[14px] text-[#6C747D]">
							Recent Roles
						</span>
						<div className="mt-[8px] space-y-[4px]">
							{roles.slice(0, 3).map((role) => (
								<div
									key={role.id}
									className="flex items-center justify-between rounded-[4px] bg-[#F9FAFB] px-[12px] py-[8px]"
								>
									<span className="font-lato text-[14px] text-[#212429]">
										{role.name}
									</span>
									<span
										className={`text-[11px] ${
											role.is_active ? 'text-[#2CBE90]' : 'text-[#9CA3AF]'
										}`}
									>
										{role.is_active ? 'Active' : 'Inactive'}
									</span>
								</div>
							))}
						</div>
					</div>
				)}
			</div>

			{/* Card Footer */}
			<div className="mt-auto grid grid-cols-2 gap-[8px]">
				<Link
					to={`/platform/apps/${appId}/user-management`}
					className="flex items-center justify-center rounded-[6px] border border-[#DDE2E5] px-[12px] py-[10px] font-lato text-[14px] font-medium text-[#212429] transition-colors hover:bg-[#F0F3F4]"
				>
					Users
					<ArrowRightIcon className="ml-[4px] h-[14px] w-[14px] text-[#6C747D]" />
				</Link>
				<Link
					to={`/platform/apps/${appId}/user-roles`}
					className="flex items-center justify-center rounded-[6px] border border-[#DDE2E5] px-[12px] py-[10px] font-lato text-[14px] font-medium text-[#212429] transition-colors hover:bg-[#F0F3F4]"
				>
					Roles
					<ArrowRightIcon className="ml-[4px] h-[14px] w-[14px] text-[#6C747D]" />
				</Link>
			</div>
		</div>
	);
}