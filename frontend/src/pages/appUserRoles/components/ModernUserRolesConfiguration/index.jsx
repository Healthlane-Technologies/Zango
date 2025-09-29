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
	const [filterStatus, setFilterStatus] = useState('all'); // all, active, inactive
	const [sortBy, setSortBy] = useState('name'); // name, created, modified, users, policies
	const [viewMode, setViewMode] = useState('card'); // card, list

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
	
	// Calculate stats
	const totalRoles = rolesData.length;
	const activeRoles = rolesData.filter(role => role.is_active).length;
	const inactiveRoles = totalRoles - activeRoles;
	const totalPolicies = rolesData.reduce((sum, role) => sum + (role.policies_count?.total || role.policies_count?.policies || 0), 0);
	const totalUsers = rolesData.reduce((sum, role) => sum + (role.users_count || 0), 0);
	
	// Helper function to format date
	const formatDate = (dateString) => {
		if (!dateString) return 'N/A';
		try {
			const date = new Date(dateString);
			return date.toLocaleDateString('en-US', {
				year: 'numeric',
				month: 'short',
				day: 'numeric'
			});
		} catch {
			return 'N/A';
		}
	};
	
	// Helper function to sort roles
	const sortRoles = (roles, sortBy) => {
		return [...roles].sort((a, b) => {
			switch (sortBy) {
				case 'created':
					return new Date(b.created_at || 0) - new Date(a.created_at || 0);
				case 'modified':
					return new Date(b.modified_at || 0) - new Date(a.modified_at || 0);
				case 'users':
					return (b.users_count || 0) - (a.users_count || 0);
				case 'policies':
					return (b.policies_count?.total || b.policies_count?.policies || 0) - (a.policies_count?.total || a.policies_count?.policies || 0);
				case 'name':
				default:
					return a.name.localeCompare(b.name);
			}
		});
	};
	
	// Separate reserved roles from regular roles
	const reservedRoleNames = ['AnonymousUsers', 'SystemUsers'];
	const reservedRoles = rolesData.filter(role => 
		reservedRoleNames.includes(role.name)
	);
	const regularRoles = rolesData.filter(role => 
		!reservedRoleNames.includes(role.name)
	);
	
	// Filter and sort roles based on search and filters
	const applyFilters = (roles) => {
		let filtered = roles.filter(role => {
			const searchLower = searchTerm.toLowerCase();
			const matchesSearch = (
				role.name?.toLowerCase().includes(searchLower) ||
				role.email?.toLowerCase().includes(searchLower) ||
				role.mobile?.toLowerCase().includes(searchLower) ||
				role.user_role_names?.some(roleName => 
					roleName?.toLowerCase().includes(searchLower)
				)
			);
			
			const matchesStatus = filterStatus === 'all' || 
				(filterStatus === 'active' && role.is_active) ||
				(filterStatus === 'inactive' && !role.is_active);
				
			return matchesSearch && matchesStatus;
		});
		
		return sortRoles(filtered, sortBy);
	};
	
	const filteredReservedRoles = applyFilters(reservedRoles);
	const filteredRegularRoles = applyFilters(regularRoles);
	
	const hasFilteredResults = filteredReservedRoles.length > 0 || filteredRegularRoles.length > 0;

	// Reserved role card component
	const ReservedRoleCard = ({ role }) => {
		const isRecent = new Date(role.modified_at) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
		const totalPolicies = role.policies_count?.total || role.policies_count?.policies || 0;
		const userPolicies = role.policies_count?.policies || 0;
		const policyGroups = role.policies_count?.policy_groups || 0;
		
		return (
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

				{/* Status Indicator */}
				{isRecent && (
					<div className="absolute -top-[12px] right-[20px]">
						<div className="w-[8px] h-[8px] bg-[#10B981] rounded-full"></div>
					</div>
				)}

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
						<p className="text-[12px] text-[#6B7280] mb-[2px]">Role ID</p>
						<p className="text-[13px] text-[#111827] font-mono">#{role.id}</p>
					</div>

					<div>
						<p className="text-[12px] text-[#6B7280] mb-[2px]">Attached Policies</p>
						<div className="flex items-center gap-[8px]">
							<p className="text-[14px] text-[#111827] font-semibold">{totalPolicies}</p>
							<span className="text-[12px] text-[#6B7280]">
								({userPolicies} user • {policyGroups} groups)
							</span>
						</div>
					</div>

					<div>
						<p className="text-[12px] text-[#6B7280] mb-[2px]">Users Assigned</p>
						<p className="text-[13px] text-[#111827]">
							{role.users_count || 0} {role.users_count === 1 ? 'user' : 'users'}
						</p>
					</div>

					<div>
						<p className="text-[12px] text-[#6B7280] mb-[2px]">Last Modified</p>
						<div className="flex items-center gap-[6px]">
							<p className="text-[13px] text-[#111827]">
								{formatDate(role.modified_at)}
							</p>
							{isRecent && (
								<span className="text-[11px] text-[#10B981] font-medium">Recent</span>
							)}
						</div>
					</div>
				</div>
			</div>
		);
	};
	
	// Role card component
	const RoleCard = ({ role }) => {
		const isRecent = new Date(role.modified_at) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
		const totalPolicies = role.policies_count?.total || role.policies_count?.policies || 0;
		const userPolicies = role.policies_count?.policies || 0;
		const policyGroups = role.policies_count?.policy_groups || 0;
		const isDefault = role.is_default;
		
		return (
			<div 
				className={`relative bg-white rounded-[12px] border p-[20px] transition-all hover:shadow-md cursor-pointer ${
					role.is_active ? 'border-[#E5E7EB]' : 'border-[#FCA5A5] bg-[#FEF2F2]'
				}`}
				onClick={() => handleRoleClick(role)}
			>
				{/* Status Badges */}
				<div className="absolute -top-[12px] right-[20px] flex gap-[8px]">
					{!role.is_active && (
						<div className="px-[12px] py-[4px] rounded-full text-[11px] font-semibold bg-[#EF4444] text-white">
							Inactive
						</div>
					)}
					{isDefault && (
						<div className="px-[12px] py-[4px] rounded-full text-[11px] font-semibold bg-[#7C3AED] text-white">
							Default
						</div>
					)}
				</div>

				{/* Recent Activity Indicator */}
				{isRecent && (
					<div className="absolute -top-[12px] left-[20px]">
						<div className="w-[8px] h-[8px] bg-[#10B981] rounded-full"></div>
					</div>
				)}

				{/* Header */}
				<div className="mb-[16px] mt-[8px]">
					<h4 className="text-[16px] font-semibold text-[#111827] mb-[4px]">{role.name}</h4>
					<p className="text-[13px] text-[#6B7280]">{role.email || 'No email specified'}</p>
				</div>

				{/* Role Info */}
				<div className="space-y-[12px] mb-[16px]">
					<div>
						<p className="text-[12px] text-[#6B7280] mb-[2px]">Role ID</p>
						<p className="text-[13px] text-[#111827] font-mono">#{role.id}</p>
					</div>

					<div>
						<p className="text-[12px] text-[#6B7280] mb-[2px]">Attached Policies</p>
						<div className="flex items-center gap-[8px]">
							<p className="text-[14px] text-[#111827] font-semibold">{totalPolicies}</p>
							<span className="text-[12px] text-[#6B7280]">
								({userPolicies} user • {policyGroups} groups)
							</span>
						</div>
					</div>

					<div>
						<p className="text-[12px] text-[#6B7280] mb-[2px]">Users Assigned</p>
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

					<div className="grid grid-cols-2 gap-[12px]">
						<div>
							<p className="text-[12px] text-[#6B7280] mb-[2px]">Created</p>
							<p className="text-[13px] text-[#111827]">
								{formatDate(role.created_at)}
							</p>
						</div>
						<div>
							<p className="text-[12px] text-[#6B7280] mb-[2px]">Modified</p>
							<div className="flex items-center gap-[4px]">
								<p className="text-[13px] text-[#111827]">
									{formatDate(role.modified_at)}
								</p>
								{isRecent && (
									<span className="w-[4px] h-[4px] bg-[#10B981] rounded-full"></span>
								)}
							</div>
						</div>
					</div>
				</div>
			</div>
		);
	};

	// List view components
	const ReservedRoleListItem = ({ role }) => {
		const isRecent = new Date(role.modified_at) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
		const totalPolicies = role.policies_count?.total || role.policies_count?.policies || 0;
		const userPolicies = role.policies_count?.policies || 0;
		const policyGroups = role.policies_count?.policy_groups || 0;
		
		return (
			<div 
				className="bg-[#F9FAFB] border border-[#E5E7EB] rounded-[8px] p-[16px] cursor-pointer transition-all hover:shadow-sm hover:bg-[#F3F4F6]"
				onClick={() => handleRoleClick(role)}
			>
				<div className="flex items-center justify-between">
					<div className="flex items-center gap-[16px] flex-1">
						{/* Role Info */}
						<div className="flex-1">
							<div className="flex items-center gap-[8px] mb-[4px]">
								<h4 className="text-[16px] font-semibold text-[#111827]">{role.name}</h4>
								<span className="px-[6px] py-[2px] bg-[#6B7280] text-white rounded-full text-[10px] font-medium">
									Reserved
								</span>
								{isRecent && (
									<span className="w-[6px] h-[6px] bg-[#10B981] rounded-full"></span>
								)}
							</div>
							<p className="text-[13px] text-[#6B7280]">
								{role.name === 'AnonymousUsers' ? 'Unauthenticated users' : 'System processes'}
							</p>
						</div>

						{/* Stats */}
						<div className="flex items-center gap-[32px] text-[13px]">
							<div className="text-center">
								<p className="text-[#6B7280] text-[11px] uppercase tracking-[0.5px] mb-[2px]">Policies</p>
								<p className="font-semibold text-[#111827]">{totalPolicies}</p>
								<p className="text-[10px] text-[#6B7280]">{userPolicies}u • {policyGroups}g</p>
							</div>
							<div className="text-center">
								<p className="text-[#6B7280] text-[11px] uppercase tracking-[0.5px] mb-[2px]">Users</p>
								<p className="font-semibold text-[#111827]">{role.users_count || 0}</p>
							</div>
							<div className="text-center">
								<p className="text-[#6B7280] text-[11px] uppercase tracking-[0.5px] mb-[2px]">Modified</p>
								<p className="font-semibold text-[#111827]">{formatDate(role.modified_at)}</p>
								{isRecent && (
									<p className="text-[10px] text-[#10B981] font-medium">Recent</p>
								)}
							</div>
						</div>
					</div>

					{/* Action */}
					<div className="ml-[16px]">
						<svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[#6B7280]">
							<path d="M6 12L10 8L6 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
						</svg>
					</div>
				</div>
			</div>
		);
	};

	const RoleListItem = ({ role }) => {
		const isRecent = new Date(role.modified_at) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
		const totalPolicies = role.policies_count?.total || role.policies_count?.policies || 0;
		const userPolicies = role.policies_count?.policies || 0;
		const policyGroups = role.policies_count?.policy_groups || 0;
		const isDefault = role.is_default;
		
		return (
			<div 
				className={`border rounded-[8px] p-[16px] cursor-pointer transition-all hover:shadow-sm ${
					role.is_active 
						? 'bg-white border-[#E5E7EB] hover:bg-[#F9FAFB]' 
						: 'bg-[#FEF2F2] border-[#FCA5A5] hover:bg-[#FEE2E2]'
				}`}
				onClick={() => handleRoleClick(role)}
			>
				<div className="flex items-center justify-between">
					<div className="flex items-center gap-[16px] flex-1">
						{/* Role Info */}
						<div className="flex-1">
							<div className="flex items-center gap-[8px] mb-[4px]">
								<h4 className="text-[16px] font-semibold text-[#111827]">{role.name}</h4>
								{!role.is_active && (
									<span className="px-[6px] py-[2px] bg-[#EF4444] text-white rounded-full text-[10px] font-medium">
										Inactive
									</span>
								)}
								{isDefault && (
									<span className="px-[6px] py-[2px] bg-[#7C3AED] text-white rounded-full text-[10px] font-medium">
										Default
									</span>
								)}
								{isRecent && (
									<span className="w-[6px] h-[6px] bg-[#10B981] rounded-full"></span>
								)}
							</div>
							<p className="text-[13px] text-[#6B7280]">{role.email || 'No email specified'}</p>
						</div>

						{/* Stats */}
						<div className="flex items-center gap-[32px] text-[13px]">
							<div className="text-center">
								<p className="text-[#6B7280] text-[11px] uppercase tracking-[0.5px] mb-[2px]">Policies</p>
								<p className="font-semibold text-[#111827]">{totalPolicies}</p>
								<p className="text-[10px] text-[#6B7280]">{userPolicies}u • {policyGroups}g</p>
							</div>
							<div className="text-center">
								<p className="text-[#6B7280] text-[11px] uppercase tracking-[0.5px] mb-[2px]">Users</p>
								<p className="font-semibold text-[#111827]">{role.users_count || 0}</p>
							</div>
							<div className="text-center">
								<p className="text-[#6B7280] text-[11px] uppercase tracking-[0.5px] mb-[2px]">Created</p>
								<p className="font-semibold text-[#111827]">{formatDate(role.created_at)}</p>
							</div>
							<div className="text-center">
								<p className="text-[#6B7280] text-[11px] uppercase tracking-[0.5px] mb-[2px]">Modified</p>
								<p className="font-semibold text-[#111827]">{formatDate(role.modified_at)}</p>
								{isRecent && (
									<p className="text-[10px] text-[#10B981] font-medium">Recent</p>
								)}
							</div>
						</div>
					</div>

					{/* Action */}
					<div className="ml-[16px]">
						<svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[#6B7280]">
							<path d="M6 12L10 8L6 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
						</svg>
					</div>
				</div>
			</div>
		);
	};

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

			{/* Stats Dashboard */}
			<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-[16px] mb-[32px]">
				<div className="bg-white border border-[#E5E7EB] rounded-[12px] p-[20px]">
					<div className="flex items-center gap-[12px] mb-[12px]">
						<div className="w-[40px] h-[40px] bg-[#EDE9FE] rounded-[8px] flex items-center justify-center">
							<svg width="20" height="20" viewBox="0 0 20 20" fill="none" className="text-[#7C3AED]">
								<path d="M10 10a3 3 0 100-6 3 3 0 000 6zM10 12c-4.42 0-8 2.69-8 6v1h16v-1c0-3.31-3.58-6-8-6z" fill="currentColor"/>
							</svg>
						</div>
						<div>
							<p className="text-[12px] font-semibold text-[#6B7280] uppercase tracking-[0.5px]">Total Roles</p>
							<p className="text-[24px] font-bold text-[#111827]">{totalRoles}</p>
						</div>
					</div>
				</div>

				<div className="bg-white border border-[#E5E7EB] rounded-[12px] p-[20px]">
					<div className="flex items-center gap-[12px] mb-[12px]">
						<div className="w-[40px] h-[40px] bg-[#D1FAE5] rounded-[8px] flex items-center justify-center">
							<svg width="20" height="20" viewBox="0 0 20 20" fill="none" className="text-[#10B981]">
								<path d="M10 2L5 7l5 5 5-5-5-5z" fill="currentColor"/>
							</svg>
						</div>
						<div>
							<p className="text-[12px] font-semibold text-[#6B7280] uppercase tracking-[0.5px]">Active</p>
							<p className="text-[24px] font-bold text-[#111827]">{activeRoles}</p>
						</div>
					</div>
				</div>

				<div className="bg-white border border-[#E5E7EB] rounded-[12px] p-[20px]">
					<div className="flex items-center gap-[12px] mb-[12px]">
						<div className="w-[40px] h-[40px] bg-[#FEE2E2] rounded-[8px] flex items-center justify-center">
							<svg width="20" height="20" viewBox="0 0 20 20" fill="none" className="text-[#EF4444]">
								<path d="M10 2a8 8 0 100 16 8 8 0 000-16zm3 11l-3-3-3 3 1.5-1.5L10 10l1.5 1.5L13 13z" fill="currentColor"/>
							</svg>
						</div>
						<div>
							<p className="text-[12px] font-semibold text-[#6B7280] uppercase tracking-[0.5px]">Inactive</p>
							<p className="text-[24px] font-bold text-[#111827]">{inactiveRoles}</p>
						</div>
					</div>
				</div>

				<div className="bg-white border border-[#E5E7EB] rounded-[12px] p-[20px]">
					<div className="flex items-center gap-[12px] mb-[12px]">
						<div className="w-[40px] h-[40px] bg-[#DBEAFE] rounded-[8px] flex items-center justify-center">
							<svg width="20" height="20" viewBox="0 0 20 20" fill="none" className="text-[#3B82F6]">
								<path d="M4 3a2 2 0 00-2 2v1a2 2 0 002 2h1a2 2 0 002-2V5a2 2 0 00-2-2H4zM9 3a2 2 0 00-2 2v1a2 2 0 002 2h1a2 2 0 002-2V5a2 2 0 00-2-2H9zM4 9a2 2 0 00-2 2v1a2 2 0 002 2h1a2 2 0 002-2v-1a2 2 0 00-2-2H4zM9 9a2 2 0 00-2 2v1a2 2 0 002 2h1a2 2 0 002-2v-1a2 2 0 00-2-2H9z" fill="currentColor"/>
							</svg>
						</div>
						<div>
							<p className="text-[12px] font-semibold text-[#6B7280] uppercase tracking-[0.5px]">Policies</p>
							<p className="text-[24px] font-bold text-[#111827]">{totalPolicies}</p>
						</div>
					</div>
				</div>

				<div className="bg-white border border-[#E5E7EB] rounded-[12px] p-[20px]">
					<div className="flex items-center gap-[12px] mb-[12px]">
						<div className="w-[40px] h-[40px] bg-[#FEF3C7] rounded-[8px] flex items-center justify-center">
							<svg width="20" height="20" viewBox="0 0 20 20" fill="none" className="text-[#F59E0B]">
								<path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z" fill="currentColor"/>
							</svg>
						</div>
						<div>
							<p className="text-[12px] font-semibold text-[#6B7280] uppercase tracking-[0.5px]">Users</p>
							<p className="text-[24px] font-bold text-[#111827]">{totalUsers}</p>
						</div>
					</div>
				</div>
			</div>

			{/* Search and Filters */}
			<div className="mb-[24px]">
				<div className="flex flex-col sm:flex-row gap-[16px] items-start sm:items-center justify-between">
					{/* Search Bar */}
					<div className="relative flex-1 max-w-[400px]">
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

					{/* Filters, Sort, and View Toggle */}
					<div className="flex gap-[12px] items-center">
						{/* View Toggle */}
						<div className="flex border border-[#E5E7EB] rounded-[8px] overflow-hidden">
							<button
								onClick={() => setViewMode('card')}
								className={`px-[12px] py-[8px] text-[14px] transition-colors flex items-center gap-[6px] ${
									viewMode === 'card'
										? 'bg-[#5048ED] text-white'
										: 'bg-white text-[#6B7280] hover:text-[#111827]'
								}`}
							>
								<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
									<rect x="2" y="2" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5"/>
									<rect x="9" y="2" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5"/>
									<rect x="2" y="9" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5"/>
									<rect x="9" y="9" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5"/>
								</svg>
								Cards
							</button>
							<button
								onClick={() => setViewMode('list')}
								className={`px-[12px] py-[8px] text-[14px] transition-colors flex items-center gap-[6px] ${
									viewMode === 'list'
										? 'bg-[#5048ED] text-white'
										: 'bg-white text-[#6B7280] hover:text-[#111827]'
								}`}
							>
								<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
									<path d="M2 4h12M2 8h12M2 12h12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
								</svg>
								List
							</button>
						</div>

						{/* Status Filter */}
						<select
							value={filterStatus}
							onChange={(e) => setFilterStatus(e.target.value)}
							className="px-[12px] py-[8px] border border-[#E5E7EB] rounded-[8px] text-[14px] focus:outline-none focus:ring-2 focus:ring-[#5048ED] focus:border-transparent bg-white"
						>
							<option value="all">All Status</option>
							<option value="active">Active Only</option>
							<option value="inactive">Inactive Only</option>
						</select>

						{/* Sort */}
						<select
							value={sortBy}
							onChange={(e) => setSortBy(e.target.value)}
							className="px-[12px] py-[8px] border border-[#E5E7EB] rounded-[8px] text-[14px] focus:outline-none focus:ring-2 focus:ring-[#5048ED] focus:border-transparent bg-white"
						>
							<option value="name">Sort by Name</option>
							<option value="created">Sort by Created</option>
							<option value="modified">Sort by Modified</option>
							<option value="users">Sort by Users</option>
							<option value="policies">Sort by Policies</option>
						</select>

						{/* Clear Filters */}
						{(searchTerm || filterStatus !== 'all' || sortBy !== 'name') && (
							<button
								onClick={() => {
									setSearchTerm('');
									setFilterStatus('all');
									setSortBy('name');
								}}
								className="px-[12px] py-[8px] text-[#6B7280] hover:text-[#111827] transition-colors text-[14px] font-medium"
							>
								Clear
							</button>
						)}
					</div>
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
					{(filteredReservedRoles.length > 0 || (!searchTerm && filterStatus === 'all')) && (
						<div>
							<div className="mb-[20px] flex items-center justify-between">
								<div>
									<div className="flex items-center gap-[12px] mb-[6px]">
										<h3 className="text-[20px] font-semibold text-[#111827]">Reserved Roles</h3>
										<span className="px-[8px] py-[4px] bg-[#F3F4F6] text-[#6B7280] rounded-[8px] text-[12px] font-medium">
											{filteredReservedRoles.length} of {reservedRoles.length}
										</span>
									</div>
									<p className="text-[14px] text-[#6B7280]">System roles that cannot be modified or deleted</p>
								</div>
								<div className="w-[32px] h-[32px] bg-[#F3F4F6] rounded-[8px] flex items-center justify-center">
									<svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[#6B7280]">
										<path d="M8 2v6m0 2v4m-6-6h4m2 0h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
									</svg>
								</div>
							</div>
							{filteredReservedRoles.length > 0 ? (
								viewMode === 'card' ? (
									<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-[20px]">
										{filteredReservedRoles.map((role) => (
											<ReservedRoleCard key={role.id} role={role} />
										))}
									</div>
								) : (
									<div className="space-y-[12px]">
										{filteredReservedRoles.map((role) => (
											<ReservedRoleListItem key={role.id} role={role} />
										))}
									</div>
								)
							) : (
								<div className="bg-[#F9FAFB] rounded-[8px] border border-[#E5E7EB] p-[24px] text-center">
									<p className="text-[14px] text-[#6B7280]">No reserved roles found</p>
								</div>
							)}
						</div>
					)}

					{/* User Defined Roles Section */}
					{(filteredRegularRoles.length > 0 || (!searchTerm && filterStatus === 'all')) && (
						<div>
							<div className="mb-[20px] flex items-center justify-between">
								<div>
									<div className="flex items-center gap-[12px] mb-[6px]">
										<h3 className="text-[20px] font-semibold text-[#111827]">User Defined Roles</h3>
										<span className="px-[8px] py-[4px] bg-[#F3F4F6] text-[#6B7280] rounded-[8px] text-[12px] font-medium">
											{filteredRegularRoles.length} of {regularRoles.length}
										</span>
									</div>
									<p className="text-[14px] text-[#6B7280]">Custom roles for application users</p>
								</div>
								<div className="w-[32px] h-[32px] bg-[#EDE9FE] rounded-[8px] flex items-center justify-center">
									<svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[#7C3AED]">
										<path d="M8 8a3 3 0 100-6 3 3 0 000 6zM8 10c-4 0-7 2-7 4v1h14v-1c0-2-3-4-7-4z" fill="currentColor"/>
									</svg>
								</div>
							</div>
							{filteredRegularRoles.length > 0 ? (
								viewMode === 'card' ? (
									<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-[20px]">
										{filteredRegularRoles.map((role) => (
											<RoleCard key={role.id} role={role} />
										))}
									</div>
								) : (
									<div className="space-y-[12px]">
										{filteredRegularRoles.map((role) => (
											<RoleListItem key={role.id} role={role} />
										))}
									</div>
								)
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