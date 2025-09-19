import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import useApi from '../../../../hooks/useApi';
import {
	selectAppUserRolesData,
	selectRerenderPage,
	setAppUserRolesData,
	selectIsAppUserRolesDataEmpty,
} from '../../slice';
// import AddNewUserRolesModal from '../Modals/AddNewUserRolesModal';
import RoleDetailsModal from '../Modals/RoleDetailsModal';

const ModernUserRolesConfiguration = () => {
	const { appId } = useParams();
	const dispatch = useDispatch();
	const triggerApi = useApi();
	const rerenderPage = useSelector(selectRerenderPage);
	const appUserRolesData = useSelector(selectAppUserRolesData);
	const isAppUserRolesDataEmpty = useSelector(selectIsAppUserRolesDataEmpty);

	const [searchTerm, setSearchTerm] = useState('');
	const [selectedRole, setSelectedRole] = useState(null);
	const [isRoleDetailsModalOpen, setIsRoleDetailsModalOpen] = useState(false);
	const [isAddNewRoleModalOpen, setIsAddNewRoleModalOpen] = useState(false);

	function updateAppUserRolesData(value) {
		dispatch(setAppUserRolesData(value));
	}

	useEffect(() => {
		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/roles/?page=1&page_size=100&include_dropdown_options=true`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				updateAppUserRolesData(response);
			}
		};

		makeApiCall();
	}, [rerenderPage, appId]);

	const handleAddNewRole = () => {
		setIsAddNewRoleModalOpen(true);
	};

	const handleRoleClick = (role) => {
		setSelectedRole(role);
		setIsRoleDetailsModalOpen(true);
	};

	const closeRoleDetailsModal = () => {
		setIsRoleDetailsModalOpen(false);
		setSelectedRole(null);
	};
	
	const closeAddRoleModal = () => {
		setIsAddNewRoleModalOpen(false);
	};

	// Get users/roles data - check multiple possible data structures
	const rolesData = appUserRolesData?.users || appUserRolesData?.roles?.records || [];
	
	// Separate reserved roles from regular roles
	const reservedRoleNames = ['AnonymousUsers', 'SystemUsers'];
	const reservedRoles = rolesData.filter(role => 
		reservedRoleNames.includes(role.name)
	);
	const regularRoles = rolesData.filter(role => 
		!reservedRoleNames.includes(role.name)
	);
	
	// Filter roles based on search
	const filteredReservedRoles = reservedRoles.filter(role => {
		const searchLower = searchTerm.toLowerCase();
		return (
			role.name?.toLowerCase().includes(searchLower) ||
			role.email?.toLowerCase().includes(searchLower) ||
			role.mobile?.toLowerCase().includes(searchLower) ||
			role.user_role_names?.some(roleName => 
				roleName?.toLowerCase().includes(searchLower)
			)
		);
	});
	
	const filteredRegularRoles = regularRoles.filter(role => {
		const searchLower = searchTerm.toLowerCase();
		return (
			role.name?.toLowerCase().includes(searchLower) ||
			role.email?.toLowerCase().includes(searchLower) ||
			role.mobile?.toLowerCase().includes(searchLower) ||
			role.user_role_names?.some(roleName => 
				roleName?.toLowerCase().includes(searchLower)
			)
		);
	});
	
	const hasFilteredResults = filteredReservedRoles.length > 0 || filteredRegularRoles.length > 0;

	// Reserved role card component
	const ReservedRoleCard = ({ role }) => (
		<div 
			className="relative bg-[#F3F4F6] rounded-[12px] border border-[#E5E7EB] p-[20px] cursor-pointer transition-all hover:shadow-md hover:border-[#D1D5DB]"
			onClick={() => handleRoleClick(role)}
		>
			{/* Reserved Badge */}
			<div className="absolute -top-[12px] left-[20px]">
				<div className="px-[12px] py-[4px] rounded-full text-[11px] font-semibold bg-[#6B7280] text-white flex items-center gap-[4px]">
					<svg width="12" height="12" viewBox="0 0 12 12" fill="none">
						<path d="M6 1V5M6 7V11M1 6H5M7 6H11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
					</svg>
					Reserved
				</div>
			</div>

			{/* Header */}
			<div className="mb-[16px] mt-[8px]">
				<h4 className="text-[16px] font-semibold text-[#111827] mb-[4px]">{role.name}</h4>
				<p className="text-[13px] text-[#6B7280]">
					{role.name === 'AnonymousUsers' ? 'Unauthenticated users' : 'System processes'}
				</p>
			</div>

			{/* Role Info */}
			<div className="space-y-[12px] mb-[16px]">
				<div>
					<p className="text-[12px] text-[#6B7280] mb-[4px]">Type</p>
					<p className="text-[13px] text-[#111827]">System-generated role</p>
				</div>

				<div>
					<p className="text-[12px] text-[#6B7280] mb-[2px]">Attached Policies</p>
					<p className="text-[13px] text-[#111827]">
						{role.policies_count?.policies || 0} {role.policies_count?.policies === 1 ? 'policy' : 'policies'}
					</p>
				</div>

				<div>
					<p className="text-[12px] text-[#6B7280] mb-[2px]">Created</p>
					<p className="text-[13px] text-[#111827]">
						{role.created_at ? new Date(role.created_at).toLocaleDateString() : 'System default'}
					</p>
				</div>
			</div>

		</div>
	);
	
	// Role card component
	const RoleCard = ({ role }) => (
		<div 
			className={`relative bg-white rounded-[12px] border p-[20px] transition-all hover:shadow-md cursor-pointer ${
				role.is_active ? 'border-[#E5E7EB]' : 'border-[#FCA5A5] bg-[#FEF2F2]'
			}`}
			onClick={() => handleRoleClick(role)}
		>
			{/* Status Badge - Only show for inactive */}
			{!role.is_active && (
				<div className="absolute -top-[12px] right-[20px]">
					<div className="px-[12px] py-[4px] rounded-full text-[11px] font-semibold bg-[#EF4444] text-white">
						Inactive
					</div>
				</div>
			)}

			{/* Header */}
			<div className="mb-[16px]">
				<h4 className="text-[16px] font-semibold text-[#111827] mb-[4px]">{role.name}</h4>
				<p className="text-[13px] text-[#6B7280]">{role.email}</p>
			</div>

			{/* Role Info */}
			<div className="space-y-[12px] mb-[16px]">
				<div>
					<p className="text-[12px] text-[#6B7280] mb-[2px]">Attached Policies</p>
					<p className="text-[13px] text-[#111827]">
						{role.policies_count?.policies || 0} {role.policies_count?.policies === 1 ? 'policy' : 'policies'}
					</p>
				</div>

				<div>
					<p className="text-[12px] text-[#6B7280] mb-[2px]">Active Users</p>
					<p className="text-[13px] text-[#111827]">
						{role.users_count || 0} {role.users_count === 1 ? 'user' : 'users'}
					</p>
				</div>

				{role.mobile && (
					<div>
						<p className="text-[12px] text-[#6B7280] mb-[2px]">Mobile</p>
						<p className="text-[13px] text-[#111827]">{role.mobile}</p>
					</div>
				)}

				<div>
					<p className="text-[12px] text-[#6B7280] mb-[2px]">Created</p>
					<p className="text-[13px] text-[#111827]">
						{new Date(role.created_at).toLocaleDateString()}
					</p>
				</div>
			</div>

		</div>
	);


	return (
		<div className="max-w-[1400px] mx-auto">
			{/* Header */}
			<div className="flex items-center justify-between mb-[32px]">
				<div>
					<h2 className="text-[24px] font-semibold text-[#111827] mb-[4px]">User Roles</h2>
					<p className="text-[14px] text-[#6B7280]">Manage user access and permissions for your application</p>
				</div>
				<button
					onClick={handleAddNewRole}
					className="flex items-center gap-[8px] px-[16px] py-[8px] bg-[#5048ED] text-white rounded-[8px] hover:bg-[#4338CA] transition-colors"
				>
					<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
						<path d="M8 3V13M3 8H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
					</svg>
					<span className="font-medium text-[14px]">Add User Role</span>
				</button>
			</div>

			{/* Search Bar */}
			<div className="mb-[24px]">
				<div className="relative max-w-[400px]">
					<svg className="absolute left-[12px] top-1/2 transform -translate-y-1/2 text-[#6B7280]" width="20" height="20" viewBox="0 0 20 20" fill="none">
						<path d="M17.5 17.5L13.875 13.875M15.8333 9.16667C15.8333 12.8486 12.8486 15.8333 9.16667 15.8333C5.48477 15.8333 2.5 12.8486 2.5 9.16667C2.5 5.48477 5.48477 2.5 9.16667 2.5C12.8486 2.5 15.8333 5.48477 15.8333 9.16667Z" stroke="currentColor" strokeWidth="1.66667" strokeLinecap="round" strokeLinejoin="round"/>
					</svg>
					<input
						type="text"
						placeholder="Search user roles..."
						value={searchTerm}
						onChange={(e) => setSearchTerm(e.target.value)}
						className="w-full pl-[44px] pr-[12px] py-[8px] border border-[#E5E7EB] rounded-[8px] text-[14px] placeholder-[#6B7280] focus:outline-none focus:ring-2 focus:ring-[#5048ED] focus:border-transparent"
					/>
				</div>
			</div>

			{/* User Roles Grid/Empty State */}
			{!hasFilteredResults ? (
				<div className="bg-white rounded-[16px] border border-[#E5E7EB] p-[48px] text-center">
					<div className="w-[80px] h-[80px] bg-[#F3F4F6] rounded-full flex items-center justify-center mx-auto mb-[24px]">
						<svg width="40" height="40" viewBox="0 0 40 40" fill="none">
							<path d="M20 21.6667C24.6024 21.6667 28.3333 17.9357 28.3333 13.3333C28.3333 8.73096 24.6024 5 20 5C15.3976 5 11.6667 8.73096 11.6667 13.3333C11.6667 17.9357 15.3976 21.6667 20 21.6667Z" stroke="#9CA3AF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
							<path d="M35 35C35 29.4772 28.2843 25 20 25C11.7157 25 5 29.4772 5 35" stroke="#9CA3AF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
						</svg>
					</div>
					<h3 className="text-[20px] font-semibold text-[#111827] mb-[8px]">
						{searchTerm && rolesData.length > 0 ? 'No User Roles Found' : 'No User Roles Created'}
					</h3>
					<p className="text-[14px] text-[#6B7280] mb-[24px]">
						{searchTerm && rolesData.length > 0
							? 'Try adjusting your search criteria' 
							: 'Create your first user role to manage application access'
						}
					</p>
					{(!searchTerm || rolesData.length === 0) && (
						<button
							onClick={handleAddNewRole}
							className="inline-flex items-center gap-[8px] px-[20px] py-[10px] bg-[#5048ED] text-white rounded-[8px] hover:bg-[#4338CA] transition-colors"
						>
							<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
								<path d="M10 5V15M5 10H15" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
							</svg>
							<span className="font-medium">Create First User Role</span>
						</button>
					)}
				</div>
			) : (
				<div className="space-y-[40px]">
					{/* Reserved Roles Section */}
					{(filteredReservedRoles.length > 0 || !searchTerm) && (
						<div>
							<div className="mb-[20px]">
								<h3 className="text-[20px] font-semibold text-[#111827] mb-[6px]">Reserved</h3>
								<p className="text-[14px] text-[#6B7280]">System roles that cannot be modified or deleted</p>
							</div>
							{filteredReservedRoles.length > 0 ? (
								<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-[20px]">
									{filteredReservedRoles.map((role) => (
										<ReservedRoleCard key={role.id} role={role} />
									))}
								</div>
							) : (
								<div className="bg-[#F9FAFB] rounded-[8px] border border-[#E5E7EB] p-[24px] text-center">
									<p className="text-[14px] text-[#6B7280]">No reserved roles found</p>
								</div>
							)}
						</div>
					)}

					{/* User Defined Roles Section */}
					{(filteredRegularRoles.length > 0 || !searchTerm) && (
						<div>
							<div className="mb-[20px]">
								<h3 className="text-[20px] font-semibold text-[#111827] mb-[6px]">User Defined</h3>
								<p className="text-[14px] text-[#6B7280]">Custom roles for application users</p>
							</div>
							{filteredRegularRoles.length > 0 ? (
								<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-[20px]">
									{filteredRegularRoles.map((role) => (
										<RoleCard key={role.id} role={role} />
									))}
								</div>
							) : (
								<div className="bg-[#F9FAFB] rounded-[8px] border border-[#E5E7EB] p-[24px] text-center">
									<p className="text-[14px] text-[#6B7280]">No user-defined roles found</p>
								</div>
							)}
						</div>
					)}
				</div>
			)}

			{/* Modals */}
			<RoleDetailsModal 
				isOpen={isRoleDetailsModalOpen}
				closeModal={closeRoleDetailsModal}
				role={selectedRole}
			/>
			<RoleDetailsModal 
				isOpen={isAddNewRoleModalOpen}
				closeModal={closeAddRoleModal}
				role={null}
				mode="add"
			/>
		</div>
	);
};

export default ModernUserRolesConfiguration;