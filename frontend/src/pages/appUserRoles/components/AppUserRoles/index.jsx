import { useEffect, useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import { ReactComponent as AddUserIcon } from '../../../../assets/images/svg/add-user-icon.svg';
import useApi from '../../../../hooks/useApi';
import BreadCrumbs from '../../../app/components/BreadCrumbs';
import {
	openIsAddNewUserRolesModalOpen,
	selectAppUserRolesData,
	selectAppUserRolesTableData,
	selectIsAppUserRolesDataEmpty,
	selectRerenderPage,
	setAppUserRolesData,
} from '../../slice';
import AppTable from '../AppTable';
import ActivateUserRolesModal from '../Modals/ActivateUserRolesModal';
import AddNewUserRolesModal from '../Modals/AddNewUserRolesModal';
import DeactivateUserRolesModal from '../Modals/DeactivateUserRolesModal';
import EditUserRolesDetailsModal from '../Modals/EditUserDetailsRolesModal';

export default function AppUserRoles() {
	let { appId } = useParams();
	const appUserRolesData = useSelector(selectAppUserRolesData);
	const appUserRolesTableData = useSelector(selectAppUserRolesTableData);
	const rerenderPage = useSelector(selectRerenderPage);
	const isAppUserRolesDataEmpty = useSelector(selectIsAppUserRolesDataEmpty);

	const dispatch = useDispatch();

	const handleAddNewUser = () => {
		dispatch(openIsAddNewUserRolesModalOpen());
	};

	function updateAppUserRolesData(value) {
		dispatch(setAppUserRolesData(value));
	}

	const triggerApi = useApi();

	useEffect(() => {
		let columnFilter = appUserRolesTableData?.columns
			? appUserRolesTableData?.columns
					?.filter(({ id, value }) => value)
					?.map(({ id, value }) => {
						if (
							typeof value === 'object' &&
							!Array.isArray(value) &&
							isNaN(parseInt(value))
						) {
							return `&search_${id}=${JSON.stringify(value)}`;
						} else {
							return `&search_${id}=${value}`;
						}
					})
					.join('')
			: '';

		const makeApiCall = async () => {
			// Fetch all roles with a larger page size since we need to separate them client-side
			// This is necessary because the API doesn't support filtering by role type (reserved vs user-defined)
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/roles/?page=1&page_size=100&include_dropdown_options=true&search=${
					appUserRolesTableData?.searchValue
				}${columnFilter?.length ? columnFilter : ''}`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				updateAppUserRolesData(response);
			}
		};

		makeApiCall();
	}, [rerenderPage, appUserRolesTableData]);

	// Separate roles into reserved and user-defined
	const { reservedRoles, userDefinedRoles } = useMemo(() => {
		if (!appUserRolesData?.roles?.records) {
			return { reservedRoles: [], userDefinedRoles: [] };
		}

		const reserved = [];
		const userDefined = [];

		appUserRolesData.roles.records.forEach(role => {
			if (role.name === 'AnonymousUsers' || role.name === 'SystemUsers') {
				reserved.push(role);
			} else {
				userDefined.push(role);
			}
		});

		return { reservedRoles: reserved, userDefinedRoles: userDefined };
	}, [appUserRolesData]);

	if (!appUserRolesData) {
		return null;
	}

	return (
		<>
			<div className="flex grow flex-col gap-[20px]">
				<div className="flex items-center justify-between py-[12px] pl-[40px] pr-[48px]">
					<BreadCrumbs />
					{isAppUserRolesDataEmpty ? null : (
						<button
							data-cy="add_user_role_button"	
							type="button"
							onClick={handleAddNewUser}
							className="flex gap-[8px] rounded-[4px] bg-primary px-[16px] py-[7px]"
						>
							<span className="font-lato text-[14px] font-bold leading-[20px] text-[#FFFFFF]">
								New User Role
							</span>
							<AddUserIcon />
						</button>
					)}
				</div>
				<div className="flex grow flex-col overflow-x-auto">
					{isAppUserRolesDataEmpty ? (
						<div className="flex grow flex-col items-center justify-center gap-[56px]">
							<div className="flex flex-col items-center justify-center gap-[8px]">
								<h3 className="first-app-text font-source-sans-pro text-[64px] font-[700] leading-[72px]">
									set-up user role(s)
								</h3>
							</div>
							<button
								type="button"
								onClick={handleAddNewUser}
								className="flex gap-[8px] rounded-[4px] bg-primary px-[16px] py-[7px]"
							>
								<span className="font-lato text-[14px] font-bold leading-[20px] text-[#FFFFFF]">
									Create New User Role
								</span>
								<AddUserIcon />
							</button>
						</div>
					) : appUserRolesData ? (
						<div className="flex flex-col gap-[32px] px-[40px]">
							{/* Stats Overview */}
							<div className="grid grid-cols-1 md:grid-cols-4 gap-[16px] mb-[24px]">
								<div className="bg-white border border-[#E5E7EB] rounded-[8px] p-[16px]">
									<div className="flex items-center gap-[8px] mb-[8px]">
										<svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[#6366F1]">
											<path d="M8 8a3 3 0 100-6 3 3 0 000 6zM8 10c-4 0-7 2-7 4v1h14v-1c0-2-3-4-7-4z" fill="currentColor"/>
										</svg>
										<span className="font-lato text-[12px] font-semibold text-[#6B7280] uppercase tracking-[0.5px]">Total Roles</span>
									</div>
									<span className="font-source-sans-pro text-[24px] font-[700] text-[#111827]">
										{appUserRolesData?.roles?.total_records || 0}
									</span>
								</div>

								<div className="bg-white border border-[#E5E7EB] rounded-[8px] p-[16px]">
									<div className="flex items-center gap-[8px] mb-[8px]">
										<svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[#10B981]">
											<path d="M8 2L3 7l5 5 5-5-5-5z" fill="currentColor"/>
										</svg>
										<span className="font-lato text-[12px] font-semibold text-[#6B7280] uppercase tracking-[0.5px]">Active Roles</span>
									</div>
									<span className="font-source-sans-pro text-[24px] font-[700] text-[#111827]">
										{appUserRolesData?.roles?.records?.filter(role => role.is_active).length || 0}
									</span>
								</div>

								<div className="bg-white border border-[#E5E7EB] rounded-[8px] p-[16px]">
									<div className="flex items-center gap-[8px] mb-[8px]">
										<svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[#F59E0B]">
											<path d="M8 2a6 6 0 100 12A6 6 0 008 2zm0 11a5 5 0 110-10 5 5 0 010 10z" fill="currentColor"/>
										</svg>
										<span className="font-lato text-[12px] font-semibold text-[#6B7280] uppercase tracking-[0.5px]">User Defined</span>
									</div>
									<span className="font-source-sans-pro text-[24px] font-[700] text-[#111827]">
										{userDefinedRoles.length}
									</span>
								</div>

								<div className="bg-white border border-[#E5E7EB] rounded-[8px] p-[16px]">
									<div className="flex items-center gap-[8px] mb-[8px]">
										<svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[#EF4444]">
											<path d="M8 2a6 6 0 100 12A6 6 0 008 2zm3 8.5L9.5 12 8 10.5 6.5 12 5 10.5 6.5 9 5 7.5 6.5 6 8 7.5 9.5 6 11 7.5 9.5 9 11 10.5z" fill="currentColor"/>
										</svg>
										<span className="font-lato text-[12px] font-semibold text-[#6B7280] uppercase tracking-[0.5px]">Reserved</span>
									</div>
									<span className="font-source-sans-pro text-[24px] font-[700] text-[#111827]">
										{reservedRoles.length}
									</span>
								</div>
							</div>

							{/* Reserved Roles Section */}
							{reservedRoles.length > 0 && (
								<div>
									<div className="flex items-center justify-between mb-[16px]">
										<h3 className="font-source-sans-pro text-[20px] font-[600] leading-[28px] text-[#212429]">
											Reserved Roles
										</h3>
										<span className="font-lato text-[12px] text-[#6B7280] bg-[#F3F4F6] px-[8px] py-[4px] rounded-[12px]">
											{reservedRoles.length} role{reservedRoles.length !== 1 ? 's' : ''}
										</span>
									</div>
									<div className="bg-[#FEF3C7] border border-[#F59E0B] rounded-[8px] p-[12px] mb-[16px]">
										<div className="flex items-start gap-[8px]">
											<svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[#F59E0B] mt-[2px]">
												<path d="M8 1a7 7 0 100 14A7 7 0 008 1zM8 4a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 018 4zm0 8a1 1 0 100-2 1 1 0 000 2z" fill="currentColor"/>
											</svg>
											<div>
												<p className="font-lato text-[12px] font-semibold text-[#92400E]">System Roles</p>
												<p className="font-lato text-[11px] text-[#92400E] mt-[2px]">These are system roles required for application functionality. You can only modify their policies.</p>
											</div>
										</div>
									</div>
									<AppTable 
										tableData={{
											...appUserRolesData,
											roles: {
												...appUserRolesData.roles,
												records: reservedRoles,
												total_records: reservedRoles.length,
												total_pages: 1
											}
										}}
									/>
								</div>
							)}

							{/* User Defined Roles Section */}
							<div>
								<div className="flex items-center justify-between mb-[16px]">
									<h3 className="font-source-sans-pro text-[20px] font-[600] leading-[28px] text-[#212429]">
										User Defined Roles
									</h3>
									<span className="font-lato text-[12px] text-[#6B7280] bg-[#F3F4F6] px-[8px] py-[4px] rounded-[12px]">
										{userDefinedRoles.length} role{userDefinedRoles.length !== 1 ? 's' : ''}
									</span>
								</div>
								{userDefinedRoles.length === 0 ? (
									<div className="bg-[#F9FAFB] border border-[#E5E7EB] rounded-[8px] p-[32px] text-center">
										<svg width="48" height="48" viewBox="0 0 24 24" fill="none" className="mx-auto mb-[16px] text-[#9CA3AF]">
											<path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
										</svg>
										<h4 className="font-source-sans-pro text-[16px] font-[600] text-[#111827] mb-[8px]">No User Defined Roles</h4>
										<p className="font-lato text-[14px] text-[#6B7280] mb-[16px]">Create custom roles to manage user permissions and access control.</p>
										<button
											type="button"
											onClick={handleAddNewUser}
											className="inline-flex items-center gap-[8px] rounded-[4px] bg-primary px-[16px] py-[8px] font-lato text-[14px] font-medium text-white hover:bg-primary/90 transition-colors"
										>
											<AddUserIcon className="w-[16px] h-[16px]" />
											Create User Role
										</button>
									</div>
								) : (
									<AppTable 
										tableData={{
											...appUserRolesData,
											roles: {
												...appUserRolesData.roles,
												records: userDefinedRoles,
												total_records: userDefinedRoles.length,
												total_pages: Math.ceil(userDefinedRoles.length / appUserRolesTableData?.pageSize)
											}
										}}
									/>
								)}
							</div>
						</div>
					) : null}
				</div>
			</div>
			<AddNewUserRolesModal />
			<EditUserRolesDetailsModal />
			<DeactivateUserRolesModal />
			<ActivateUserRolesModal />
		</>
	);
}
