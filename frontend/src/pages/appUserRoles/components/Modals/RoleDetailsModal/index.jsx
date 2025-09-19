import { useState, useEffect, useMemo } from 'react';
import { useDispatch } from 'react-redux';
import { useParams } from 'react-router-dom';
import { Disclosure } from '@headlessui/react';
import RoleDetailsModalWrapper from './RoleDetailsModalWrapper';
import useApi from '../../../../../hooks/useApi';
import { transformToFormData } from '../../../../../utils/form';
import {
	openIsEditUserRolesDetailModalOpen,
	openIsDeactivateUserRolesModalOpen,
	openIsActivateUserRolesModalOpen,
	toggleRerenderPage,
} from '../../../slice';

function RoleDetailsModal({ isOpen, closeModal, role, mode = 'view' }) {
	const { appId } = useParams();
	const dispatch = useDispatch();
	const triggerApi = useApi();

	const [activeTab, setActiveTab] = useState('overview');
	const [activePolicyTab, setActivePolicyTab] = useState('all');
	const [roleDetails, setRoleDetails] = useState(null);
	const [loading, setLoading] = useState(false);
	const [attachedPolicies, setAttachedPolicies] = useState([]);
	const [searchTerm, setSearchTerm] = useState('');
	const [viewMode, setViewMode] = useState('list'); // 'grid' or 'list'
	const [expandedSections, setExpandedSections] = useState({});
	
	// Edit mode states
	const [isEditMode, setIsEditMode] = useState(mode === 'add');
	const [editedRole, setEditedRole] = useState(mode === 'add' ? { name: '', is_active: true } : null);
	const [selectedPoliciesForRemoval, setSelectedPoliciesForRemoval] = useState([]);
	const [selectedPoliciesForAddition, setSelectedPoliciesForAddition] = useState([]);
	const [isAddPolicyModalOpen, setIsAddPolicyModalOpen] = useState(false);
	const [availablePolicies, setAvailablePolicies] = useState([]);
	const [isSaving, setIsSaving] = useState(false);
	const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
	const [policySearchTerm, setPolicySearchTerm] = useState('');
	const [tempSelectedPolicies, setTempSelectedPolicies] = useState([]); // Temporary selection in modal

	// Check if this is a reserved role
	const isReservedRole = (roleDetails?.name || role?.name) === 'AnonymousUsers' || 
		(roleDetails?.name || role?.name) === 'SystemUsers';
		
	// Check if this is add mode
	const isAddMode = mode === 'add';

	// Filter policies based on search term
	const filteredPolicies = useMemo(() => {
		if (!searchTerm) return attachedPolicies;
		
		const lowerSearchTerm = searchTerm.toLowerCase();
		return attachedPolicies.filter(policy => {
			const policyName = (policy.name || policy.label || '').toLowerCase();
			return (
				policyName.includes(lowerSearchTerm) ||
				(policy.description && policy.description.toLowerCase().includes(lowerSearchTerm)) ||
				(policy.path && policy.path.toLowerCase().includes(lowerSearchTerm))
			);
		});
	}, [attachedPolicies, searchTerm]);

	// Initialize expanded sections when policies change
	useEffect(() => {
		const systemCount = attachedPolicies.filter(p => p.type === 'system').length;
		const packagePolicies = attachedPolicies.filter(p => p.path && p.path.startsWith('packages.'));
		const modulePolicies = attachedPolicies.filter(p => p.path && !p.path.startsWith('packages.') && p.type !== 'system');
		
		// Auto-expand sections if there are 3 or fewer total sections
		const totalSections = (systemCount > 0 ? 1 : 0) + 
			[...new Set(packagePolicies.map(p => p.path.split('.')[1]))].length +
			[...new Set(modulePolicies.map(p => p.path))].length;
		
		if (totalSections <= 3) {
			const newExpanded = {};
			if (systemCount > 0) newExpanded['system'] = true;
			packagePolicies.forEach(p => {
				const packageName = p.path.split('.')[1];
				newExpanded[`package-${packageName}`] = true;
			});
			modulePolicies.forEach(p => {
				newExpanded[`module-${p.path}`] = true;
			});
			setExpandedSections(newExpanded);
		}
	}, [attachedPolicies]);

	// Fetch role details when modal opens
	useEffect(() => {
		if (isOpen && !isAddMode && role) {
			fetchRoleDetails();
			// Reset edit mode when modal opens (only for view mode)
			setIsEditMode(false);
			setEditedRole(null);
			setSelectedPoliciesForRemoval([]);
			setHasUnsavedChanges(false);
		} else if (isOpen && isAddMode) {
			// For add mode, fetch available policies immediately
			fetchAvailablePolicies();
			setAttachedPolicies([]);
			setEditedRole({ name: '', is_active: true });
		}
	}, [isOpen, role, isAddMode]);

	const fetchRoleDetails = async () => {
		setLoading(true);
		try {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/roles/${role.id}/`,
				type: 'GET',
				loader: false,
			});
			if (success && response) {
				const roleData = response.role || response;
				setRoleDetails(roleData);
				setAttachedPolicies(roleData.attached_policies || []);
				setEditedRole(roleData); // Initialize edited role
			}
		} catch (error) {
			console.error('Error fetching role details:', error);
		} finally {
			setLoading(false);
		}
	};

	const handleEditRole = () => {
		if (isEditMode) {
			// Cancel edit mode
			if (hasUnsavedChanges) {
				const confirmCancel = window.confirm('You have unsaved changes. Are you sure you want to cancel?');
				if (!confirmCancel) return;
			}
			setIsEditMode(false);
			setEditedRole(roleDetails);
			setSelectedPoliciesForRemoval([]);
			setSelectedPoliciesForAddition([]);
			setHasUnsavedChanges(false);
			// Reset attachedPolicies to original
			setAttachedPolicies(roleDetails?.attached_policies || []);
		} else {
			// Enter edit mode
			setIsEditMode(true);
			setEditedRole(roleDetails); // Make sure to use current role details
			fetchAvailablePolicies();
		}
	};
	
	const handleCloseModal = () => {
		if (hasUnsavedChanges) {
			const confirmClose = window.confirm('You have unsaved changes. Are you sure you want to close?');
			if (!confirmClose) return;
		}
		closeModal();
	};

	// Fetch available policies for adding
	const fetchAvailablePolicies = async () => {
		try {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/roles/?page=1&page_size=100&include_dropdown_options=true`,
				type: 'GET',
				loader: false,
			});
			if (success && response) {
				const allPolicies = response.dropdown_options?.policies || [];
				// Filter out already attached policies (including newly added ones)
				const attachedPolicyIds = attachedPolicies.map(p => p.id);
				const availablePoliciesFiltered = allPolicies.filter(
					policy => !attachedPolicyIds.includes(policy.id)
				);
				setAvailablePolicies(availablePoliciesFiltered);
			}
		} catch (error) {
			console.error('Error fetching available policies:', error);
		}
	};

	// Handle saving changes
	const handleSaveChanges = async () => {
		setIsSaving(true);
		try {
			// Build the payload
			const payload = {};
			
			// Only include name for non-reserved roles
			if (!isReservedRole) {
				payload.name = editedRole.name;
			}
			
			// Include is_active for edit mode
			if (!isAddMode) {
				payload.is_active = editedRole.is_active;
			}
			
			// Always include policies
			payload.policies = attachedPolicies
				.filter(p => !selectedPoliciesForRemoval.includes(p.id))
				.map(p => p.id);

			console.log('Saving role with payload:', payload);
			
			// Transform to FormData
			const formData = transformToFormData(payload);

			// API call
			const { response, success } = await triggerApi({
				url: isAddMode ? `/api/v1/apps/${appId}/roles/` : `/api/v1/apps/${appId}/roles/${roleDetails.id}/`,
				type: isAddMode ? 'POST' : 'PUT',
				loader: true,
				payload: formData,
			});

			if (success) {
				if (isAddMode) {
					// For add mode, close modal and refresh
					closeModal();
					dispatch(toggleRerenderPage());
				} else {
					// For edit mode, refresh the data
					await fetchRoleDetails();
					setIsEditMode(false);
					setSelectedPoliciesForRemoval([]);
					setSelectedPoliciesForAddition([]);
					setHasUnsavedChanges(false);
					dispatch(toggleRerenderPage());
				}
			}
		} catch (error) {
			console.error('Error saving changes:', error);
		} finally {
			setIsSaving(false);
		}
	};

	// Helper function to toggle section expansion
	const toggleSection = (sectionKey) => {
		setExpandedSections(prev => ({
			...prev,
			[sectionKey]: !prev[sectionKey]
		}));
	};

	// Helper function to render policy card
	const renderPolicyCard = (policy, colorScheme) => {
		const { bg, border, text } = colorScheme;
		const isMarkedForRemoval = selectedPoliciesForRemoval.includes(policy.id);
		const isNewlyAdded = selectedPoliciesForAddition.includes(policy.id);
		
		if (viewMode === 'list') {
			return (
				<tr key={policy.id} className={`border-b border-[#E5E7EB] ${isMarkedForRemoval ? 'opacity-50' : ''} ${isNewlyAdded ? 'bg-[#D1FAE5]' : ''} ${isEditMode ? 'hover:bg-[#F9FAFB]' : ''}`}>
					{isEditMode && (
						<td className="py-[8px] px-[12px] w-[40px]">
							<input
								type="checkbox"
								checked={!isMarkedForRemoval}
								onChange={() => {
									if (isMarkedForRemoval) {
										setSelectedPoliciesForRemoval(prev => prev.filter(id => id !== policy.id));
									} else {
										setSelectedPoliciesForRemoval(prev => [...prev, policy.id]);
									}
									setHasUnsavedChanges(true);
								}}
								className="w-[16px] h-[16px] text-[#5048ED] rounded border-[#D1D5DB] focus:ring-[#5048ED]"
							/>
						</td>
					)}
					<td className="py-[8px] px-[12px]">
						<div className="flex items-center gap-[8px]">
							<p className="text-[14px] font-medium text-[#111827]">{policy.name || policy.label}</p>
							{isNewlyAdded && (
								<span className="px-[6px] py-[1px] bg-[#10B981] text-white text-[10px] font-medium rounded-[4px]">NEW</span>
							)}
							{isMarkedForRemoval && (
								<span className="px-[6px] py-[1px] bg-[#EF4444] text-white text-[10px] font-medium rounded-[4px]">REMOVING</span>
							)}
						</div>
					</td>
					<td className="py-[8px] px-[12px]">
						<p className="text-[12px] text-[#6B7280]">{policy.description || '-'}</p>
					</td>
					<td className="py-[8px] px-[12px]">
						<span className={`text-[11px] ${text}`}>
							{policy.type === 'system' ? 'System' : 
							 policy.path?.startsWith('packages.') ? `Package: ${policy.path.split('.')[1]}` : 
							 policy.path ? `Module: ${policy.path}` : '-'}
						</span>
					</td>
				</tr>
			);
		}
		
		return (
			<div
				key={policy.id}
				className={`p-[12px] rounded-[6px] border ${bg} ${border} ${isMarkedForRemoval ? 'opacity-50' : ''} ${isNewlyAdded ? 'ring-2 ring-[#10B981] ring-offset-2' : ''} ${isEditMode ? 'cursor-pointer' : ''} relative`}
				onClick={isEditMode ? () => {
					if (isMarkedForRemoval) {
						setSelectedPoliciesForRemoval(prev => prev.filter(id => id !== policy.id));
					} else {
						setSelectedPoliciesForRemoval(prev => [...prev, policy.id]);
					}
					setHasUnsavedChanges(true);
				} : undefined}
			>
				{isEditMode && (
					<div className="flex items-start gap-[8px]">
						<input
							type="checkbox"
							checked={!isMarkedForRemoval}
							onChange={(e) => {
								e.stopPropagation();
								if (isMarkedForRemoval) {
									setSelectedPoliciesForRemoval(prev => prev.filter(id => id !== policy.id));
								} else {
									setSelectedPoliciesForRemoval(prev => [...prev, policy.id]);
								}
								setHasUnsavedChanges(true);
							}}
							className="mt-[2px] w-[16px] h-[16px] text-[#5048ED] rounded border-[#D1D5DB] focus:ring-[#5048ED]"
						/>
						<div className="flex-1">
							<div className="flex items-center gap-[8px] mb-[2px]">
								<p className="text-[14px] font-medium text-[#111827]">{policy.name || policy.label}</p>
								{isNewlyAdded && (
									<span className="px-[6px] py-[1px] bg-[#10B981] text-white text-[10px] font-medium rounded-[4px]">NEW</span>
								)}
								{isMarkedForRemoval && (
									<span className="px-[6px] py-[1px] bg-[#EF4444] text-white text-[10px] font-medium rounded-[4px]">REMOVING</span>
								)}
							</div>
							{policy.description && (
								<p className="text-[12px] text-[#6B7280]">{policy.description}</p>
							)}
						</div>
					</div>
				)}
				{!isEditMode && (
					<>
						<div className="flex items-center gap-[8px] mb-[2px]">
							<p className="text-[14px] font-medium text-[#111827]">{policy.name || policy.label}</p>
							{isNewlyAdded && (
								<span className="px-[6px] py-[1px] bg-[#10B981] text-white text-[10px] font-medium rounded-[4px]">NEW</span>
							)}
							{isMarkedForRemoval && (
								<span className="px-[6px] py-[1px] bg-[#EF4444] text-white text-[10px] font-medium rounded-[4px]">REMOVING</span>
							)}
						</div>
						{policy.description && (
							<p className="text-[12px] text-[#6B7280]">{policy.description}</p>
						)}
					</>
				)}
			</div>
		);
	};

	// Helper function to render policies in a section
	const renderPoliciesSection = (policies, colorScheme) => {
		if (viewMode === 'list') {
			return (
				<table className="w-full">
					<thead>
						<tr className="border-b border-[#E5E7EB]">
							{isEditMode && <th className="text-left py-[8px] px-[12px] w-[40px]"></th>}
							<th className="text-left py-[8px] px-[12px] text-[12px] font-medium text-[#6B7280]">Policy Name</th>
							<th className="text-left py-[8px] px-[12px] text-[12px] font-medium text-[#6B7280]">Description</th>
							<th className="text-left py-[8px] px-[12px] text-[12px] font-medium text-[#6B7280]">Type</th>
						</tr>
					</thead>
					<tbody>
						{policies.map(policy => renderPolicyCard(policy, colorScheme))}
					</tbody>
				</table>
			);
		}
		
		return (
			<div className="grid grid-cols-2 gap-[12px]">
				{policies.map(policy => renderPolicyCard(policy, colorScheme))}
			</div>
		);
	};

	const tabs = [
		{ id: 'overview', label: 'Overview' },
		{ id: 'policies', label: 'Policies' },
	];

	return (
		<RoleDetailsModalWrapper
			label={isEditMode && editedRole ? (
				<div className="flex items-center gap-[12px]">
					{!isReservedRole && !isAddMode ? (
						<input
							type="text"
							value={editedRole?.name || ''}
							onChange={(e) => {
								setEditedRole({ ...editedRole, name: e.target.value });
								setHasUnsavedChanges(true);
							}}
							className="text-[18px] font-semibold text-[#111827] bg-transparent border-b border-[#E5E7EB] focus:border-[#5048ED] focus:outline-none px-[4px]"
						/>
					) : isAddMode ? (
						<span>Create New Role</span>
					) : (
						<span>{roleDetails?.name || role?.name}</span>
					)}
				</div>
			) : isAddMode ? (
				'Create New Role'
			) : (
				`${roleDetails?.name || role?.name}`
			)}
			show={isOpen}
			closeModal={handleCloseModal}
			headerAction={
				<div className="flex items-center gap-[8px]">
					{isEditMode ? (
						<>
							<button
								onClick={handleSaveChanges}
								disabled={isSaving || !hasUnsavedChanges}
								className="px-[16px] py-[6px] bg-[#5048ED] text-white rounded-[6px] text-[13px] font-medium hover:bg-[#4338CA] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
							>
								{isSaving ? 'Saving...' : (isAddMode ? 'Create Role' : 'Save Changes')}
							</button>
							<button
								onClick={handleEditRole}
								className="px-[16px] py-[6px] bg-[#F3F4F6] text-[#6B7280] rounded-[6px] text-[13px] font-medium hover:bg-[#E5E7EB] transition-colors"
							>
								Cancel
							</button>
						</>
					) : !isAddMode ? (
						<button
							onClick={handleEditRole}
							className="px-[16px] py-[6px] bg-[#5048ED] text-white rounded-[6px] text-[13px] font-medium hover:bg-[#4338CA] transition-colors"
						>
							{isReservedRole ? 'Edit Policies' : 'Edit Role'}
						</button>
					) : null}
				</div>
			}
		>
			<div className="flex h-[600px]">
				{/* Tabs */}
				<div className="flex flex-col w-full">
					<div className="flex border-b border-[#E5E7EB]">
						{tabs.map((tab) => (
							<button
								key={tab.id}
								onClick={() => setActiveTab(tab.id)}
								className={`px-[24px] py-[12px] text-[14px] font-medium border-b-2 transition-colors ${
									activeTab === tab.id
										? 'border-[#5048ED] text-[#5048ED]'
										: 'border-transparent text-[#6B7280] hover:text-[#111827]'
								}`}
							>
								{tab.label}
							</button>
						))}
					</div>

					{/* Content */}
					<div className="flex-1 overflow-auto">
						{loading ? (
							<div className="flex items-center justify-center h-full">
								<div className="animate-spin rounded-full h-[32px] w-[32px] border-b-2 border-[#5048ED]"></div>
							</div>
						) : (
							<>
								{/* Overview Tab */}
								{activeTab === 'overview' && (
									<div className="p-[24px] space-y-[24px]">
										<div className="grid grid-cols-2 gap-[24px]">
											<div>
												<h3 className="text-[16px] font-semibold text-[#111827] mb-[16px]">Role Information</h3>
												<div className="space-y-[12px]">
													{isAddMode && isEditMode ? (
														<div>
															<p className="text-[12px] text-[#6B7280] mb-[4px]">Role Name</p>
															<input
																type="text"
																value={editedRole?.name || ''}
																onChange={(e) => {
																	setEditedRole({ ...editedRole, name: e.target.value });
																	setHasUnsavedChanges(true);
																}}
																placeholder="Enter role name"
																className="w-full px-[12px] py-[8px] text-[14px] border border-[#E5E7EB] rounded-[6px] focus:outline-none focus:border-[#5048ED]"
															/>
														</div>
													) : null}
													{!isAddMode && (
														<>
															<div>
																<p className="text-[12px] text-[#6B7280] mb-[4px]">Type</p>
																<p className="text-[14px] text-[#111827]">
																	{isReservedRole ? 'Reserved System Role' : 'User Defined Role'}
																</p>
															</div>
															<div>
																<p className="text-[12px] text-[#6B7280] mb-[4px]">Status</p>
																{isEditMode && !isReservedRole && editedRole ? (
																	<button
																		onClick={() => {
																			setEditedRole(prev => ({ ...prev, is_active: !prev.is_active }));
																			setHasUnsavedChanges(true);
																		}}
																		className={`inline-flex items-center gap-[6px] px-[12px] py-[4px] rounded-[6px] text-[13px] font-medium transition-colors ${
																			editedRole.is_active
																				? 'bg-[#D1FAE5] text-[#10B981] hover:bg-[#A7F3D0]'
																				: 'bg-[#FEE2E2] text-[#EF4444] hover:bg-[#FECACA]'
																		}`}
																	>
																		<div className={`w-[36px] h-[20px] rounded-full relative transition-colors ${
																			editedRole.is_active ? 'bg-[#10B981]' : 'bg-[#EF4444]'
																		}`}>
																			<div className={`absolute top-[2px] w-[16px] h-[16px] bg-white rounded-full transition-transform ${
																				editedRole.is_active ? 'translate-x-[18px]' : 'translate-x-[2px]'
																			}`} />
																		</div>
																		{editedRole.is_active ? 'Active' : 'Inactive'}
																	</button>
																) : (
																	<span className={`inline-flex px-[8px] py-[2px] rounded-[4px] text-[12px] font-medium ${
																		roleDetails?.is_active
																			? 'bg-[#D1FAE5] text-[#10B981]'
																			: 'bg-[#FEE2E2] text-[#EF4444]'
																	}`}>
																		{roleDetails?.is_active ? 'Active' : 'Inactive'}
																	</span>
																)}
															</div>
															<div>
																<p className="text-[12px] text-[#6B7280] mb-[4px]">Created</p>
																<p className="text-[14px] text-[#111827]">
																	{roleDetails?.created_at ? new Date(roleDetails.created_at).toLocaleDateString() : 'N/A'}
																</p>
															</div>
														</>
													)}
												</div>
											</div>

											{!isAddMode && (
												<div>
													<h3 className="text-[16px] font-semibold text-[#111827] mb-[16px]">Summary</h3>
													<div className="space-y-[12px]">
														<div className="bg-[#F9FAFB] rounded-[8px] p-[16px]">
															<p className="text-[24px] font-bold text-[#111827]">
																{roleDetails?.policies_count?.policies || attachedPolicies.length || 0}
															</p>
															<p className="text-[14px] text-[#6B7280]">Total Policies</p>
														</div>
														{!isReservedRole && (
															<div className="bg-[#F9FAFB] rounded-[8px] p-[16px]">
																<p className="text-[24px] font-bold text-[#111827]">
																	{roleDetails?.users_count || 0}
																</p>
																<p className="text-[14px] text-[#6B7280]">Active Users</p>
															</div>
														)}
													</div>
												</div>
											)}
										</div>

									</div>
								)}

								{/* Policies Tab */}
								{activeTab === 'policies' && (
									<div className="p-[24px]">
										<div className="flex justify-between items-center mb-[16px]">
											<h3 className="text-[16px] font-semibold text-[#111827]">
												Attached Policies ({attachedPolicies.filter(p => !selectedPoliciesForRemoval.includes(p.id)).length})
											</h3>
											{/* View Mode Toggle and Add Policy Button */}
											<div className="flex items-center gap-[8px]">
												{isEditMode && (
													<button
														onClick={() => {
															setIsAddPolicyModalOpen(true);
															fetchAvailablePolicies();
														}}
														className="px-[12px] py-[6px] bg-[#5048ED] text-white rounded-[6px] text-[13px] font-medium hover:bg-[#4338CA] transition-colors flex items-center gap-[6px]"
													>
														<svg className="w-[14px] h-[14px]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
															<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
														</svg>
														Add Policies
													</button>
												)}
												<button
													onClick={() => setViewMode('grid')}
													className={`p-[6px] rounded-[4px] transition-colors ${
														viewMode === 'grid' 
															? 'bg-[#5048ED] text-white' 
															: 'bg-[#F3F4F6] text-[#6B7280] hover:bg-[#E5E7EB]'
													}`}
													title="Grid View"
												>
													<svg className="w-[16px] h-[16px]" fill="currentColor" viewBox="0 0 20 20">
														<path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
													</svg>
												</button>
												<button
													onClick={() => setViewMode('list')}
													className={`p-[6px] rounded-[4px] transition-colors ${
														viewMode === 'list' 
															? 'bg-[#5048ED] text-white' 
															: 'bg-[#F3F4F6] text-[#6B7280] hover:bg-[#E5E7EB]'
													}`}
													title="List View"
												>
													<svg className="w-[16px] h-[16px]" fill="currentColor" viewBox="0 0 20 20">
														<path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
													</svg>
												</button>
											</div>
										</div>
										
										{/* Pending Changes Summary */}
										{isEditMode && (selectedPoliciesForRemoval.length > 0 || selectedPoliciesForAddition.length > 0) && (
											<div className="mb-[16px] p-[12px] bg-[#F9FAFB] rounded-[8px] border border-[#E5E7EB]">
												<div className="space-y-[8px]">
													{selectedPoliciesForRemoval.length > 0 && (
														<div>
															<p className="text-[12px] font-medium text-[#EF4444] mb-[4px] flex items-center gap-[4px]">
																<svg className="w-[14px] h-[14px]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
																	<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
																</svg>
																Removing {selectedPoliciesForRemoval.length} {selectedPoliciesForRemoval.length === 1 ? 'policy' : 'policies'}:
															</p>
															<div className="flex flex-wrap gap-[6px]">
																{attachedPolicies
																	.filter(p => selectedPoliciesForRemoval.includes(p.id))
																	.map(policy => (
																		<span key={policy.id} className="px-[8px] py-[2px] bg-[#FEE2E2] text-[#EF4444] text-[11px] rounded-[4px]">
																			{policy.name}
																		</span>
																	))}
															</div>
														</div>
													)}
													{selectedPoliciesForAddition.length > 0 && (
														<div>
															<p className="text-[12px] font-medium text-[#10B981] mb-[4px] flex items-center gap-[4px]">
																<svg className="w-[14px] h-[14px]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
																	<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
																</svg>
																Adding {selectedPoliciesForAddition.length} {selectedPoliciesForAddition.length === 1 ? 'policy' : 'policies'}:
															</p>
															<div className="flex flex-wrap gap-[6px]">
																{attachedPolicies
																	.filter(p => selectedPoliciesForAddition.includes(p.id))
																	.map(policy => (
																		<span key={policy.id} className="px-[8px] py-[2px] bg-[#D1FAE5] text-[#10B981] text-[11px] rounded-[4px]">
																			{policy.name || policy.label}
																		</span>
																	))}
															</div>
														</div>
													)}
												</div>
											</div>
										)}
										
										{/* Search Bar */}
										<div className="mb-[16px]">
											<div className="relative">
												<input
													type="text"
													placeholder="Search policies by name, description, or path..."
													value={searchTerm}
													onChange={(e) => setSearchTerm(e.target.value)}
													className="w-full px-[36px] py-[8px] text-[14px] border border-[#E5E7EB] rounded-[6px] focus:outline-none focus:border-[#5048ED]"
												/>
												<svg className="absolute left-[12px] top-[50%] transform -translate-y-[50%] w-[16px] h-[16px] text-[#6B7280]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
												</svg>
												{searchTerm && (
													<button
														onClick={() => setSearchTerm('')}
														className="absolute right-[12px] top-[50%] transform -translate-y-[50%] text-[#6B7280] hover:text-[#111827]"
													>
														<svg className="w-[16px] h-[16px]" fill="currentColor" viewBox="0 0 20 20">
															<path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
														</svg>
													</button>
												)}
											</div>
										</div>
										{filteredPolicies.length > 0 ? (
											<div>
												{/* Policy Type Tabs */}
												<div className="flex border-b border-[#E5E7EB] mb-[20px]">
													<button
														onClick={() => setActivePolicyTab('all')}
														className={`px-[16px] py-[8px] text-[13px] font-medium border-b-2 transition-colors ${
															activePolicyTab === 'all'
																? 'border-[#5048ED] text-[#5048ED]'
																: 'border-transparent text-[#6B7280] hover:text-[#111827]'
														}`}
													>
														All ({filteredPolicies.length})
													</button>
													<button
														onClick={() => setActivePolicyTab('system')}
														className={`px-[16px] py-[8px] text-[13px] font-medium border-b-2 transition-colors ${
															activePolicyTab === 'system'
																? 'border-[#5048ED] text-[#5048ED]'
																: 'border-transparent text-[#6B7280] hover:text-[#111827]'
														}`}
													>
														System ({filteredPolicies.filter(p => p.type === 'system').length})
													</button>
													<button
														onClick={() => setActivePolicyTab('package')}
														className={`px-[16px] py-[8px] text-[13px] font-medium border-b-2 transition-colors ${
															activePolicyTab === 'package'
																? 'border-[#5048ED] text-[#5048ED]'
																: 'border-transparent text-[#6B7280] hover:text-[#111827]'
														}`}
													>
														Package ({filteredPolicies.filter(p => p.path && p.path.startsWith('packages.')).length})
													</button>
													<button
														onClick={() => setActivePolicyTab('module')}
														className={`px-[16px] py-[8px] text-[13px] font-medium border-b-2 transition-colors ${
															activePolicyTab === 'module'
																? 'border-[#5048ED] text-[#5048ED]'
																: 'border-transparent text-[#6B7280] hover:text-[#111827]'
														}`}
													>
														Module ({filteredPolicies.filter(p => p.path && !p.path.startsWith('packages.') && p.type !== 'system').length})
													</button>
												</div>

												{/* Policy Content */}
												<div className="min-h-[200px] max-h-[400px] overflow-y-auto">
													{/* All Policies */}
													{activePolicyTab === 'all' && (
														<div className="space-y-[16px]">
															{/* System Policies Section */}
															{filteredPolicies.filter(p => p.type === 'system').length > 0 && (
																<Disclosure defaultOpen={expandedSections['system']}>
																	{({ open }) => (
																		<div className="border border-[#E5E7EB] rounded-[8px] overflow-hidden">
																			<Disclosure.Button
																				onClick={() => toggleSection('system')}
																				className="w-full px-[16px] py-[12px] bg-[#FEF3F2] hover:bg-[#FED7D7] transition-colors flex items-center justify-between"
																			>
																				<div className="flex items-center gap-[8px]">
																					<h4 className="text-[14px] font-semibold text-[#111827]">System Policies</h4>
																					<span className="px-[8px] py-[2px] bg-[#DC2626] text-white text-[11px] rounded-[12px]">
																						{filteredPolicies.filter(p => p.type === 'system').length}
																					</span>
																				</div>
																				<svg
																					className={`w-[16px] h-[16px] text-[#6B7280] transition-transform ${open ? 'rotate-180' : ''}`}
																					fill="none"
																					stroke="currentColor"
																					viewBox="0 0 24 24"
																				>
																					<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
																				</svg>
																			</Disclosure.Button>
																			<Disclosure.Panel className="p-[16px] bg-white">
																				{renderPoliciesSection(
																					filteredPolicies.filter(p => p.type === 'system'),
																					{ bg: 'bg-[#FEF3F2]', border: 'border-[#FED7D7]', text: 'text-[#DC2626]' }
																				)}
																			</Disclosure.Panel>
																		</div>
																	)}
																</Disclosure>
															)}

															{/* Package Policies Section */}
															{(() => {
																const packagePolicies = filteredPolicies.filter(p => p.path && p.path.startsWith('packages.'));
																const groupedPackages = packagePolicies.reduce((acc, policy) => {
																	const packageName = policy.path.split('.')[1];
																	if (!acc[packageName]) acc[packageName] = [];
																	acc[packageName].push(policy);
																	return acc;
																}, {});

																return Object.entries(groupedPackages).map(([packageName, policies]) => (
																	<Disclosure key={packageName} defaultOpen={expandedSections[`package-${packageName}`]}>
																		{({ open }) => (
																			<div className="border border-[#E5E7EB] rounded-[8px] overflow-hidden">
																				<Disclosure.Button
																					onClick={() => toggleSection(`package-${packageName}`)}
																					className="w-full px-[16px] py-[12px] bg-[#EBF8FF] hover:bg-[#BFE6FF] transition-colors flex items-center justify-between"
																				>
																					<div className="flex items-center gap-[8px]">
																						<h4 className="text-[14px] font-semibold text-[#111827] capitalize">{packageName} Package</h4>
																						<span className="px-[8px] py-[2px] bg-[#2563EB] text-white text-[11px] rounded-[12px]">
																							{policies.length}
																						</span>
																					</div>
																					<svg
																						className={`w-[16px] h-[16px] text-[#6B7280] transition-transform ${open ? 'rotate-180' : ''}`}
																						fill="none"
																						stroke="currentColor"
																						viewBox="0 0 24 24"
																					>
																						<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
																					</svg>
																				</Disclosure.Button>
																				<Disclosure.Panel className="p-[16px] bg-white">
																					{renderPoliciesSection(
																						policies,
																						{ bg: 'bg-[#EBF8FF]', border: 'border-[#BFE6FF]', text: 'text-[#2563EB]' }
																					)}
																				</Disclosure.Panel>
																			</div>
																		)}
																	</Disclosure>
																));
															})()}

															{/* Module Policies Section */}
															{(() => {
																const modulePolicies = filteredPolicies.filter(
																	p => p.path && !p.path.startsWith('packages.') && p.type !== 'system'
																);
																const groupedModules = modulePolicies.reduce((acc, policy) => {
																	const moduleName = policy.path;
																	if (!acc[moduleName]) acc[moduleName] = [];
																	acc[moduleName].push(policy);
																	return acc;
																}, {});

																return Object.entries(groupedModules).map(([moduleName, policies]) => (
																	<Disclosure key={moduleName} defaultOpen={expandedSections[`module-${moduleName}`]}>
																		{({ open }) => (
																			<div className="border border-[#E5E7EB] rounded-[8px] overflow-hidden">
																				<Disclosure.Button
																					onClick={() => toggleSection(`module-${moduleName}`)}
																					className="w-full px-[16px] py-[12px] bg-[#F0FDF4] hover:bg-[#BBF7D0] transition-colors flex items-center justify-between"
																				>
																					<div className="flex items-center gap-[8px]">
																						<h4 className="text-[14px] font-semibold text-[#111827]">{moduleName} Module</h4>
																						<span className="px-[8px] py-[2px] bg-[#059669] text-white text-[11px] rounded-[12px]">
																							{policies.length}
																						</span>
																					</div>
																					<svg
																						className={`w-[16px] h-[16px] text-[#6B7280] transition-transform ${open ? 'rotate-180' : ''}`}
																						fill="none"
																						stroke="currentColor"
																						viewBox="0 0 24 24"
																					>
																						<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
																					</svg>
																				</Disclosure.Button>
																				<Disclosure.Panel className="p-[16px] bg-white">
																					{renderPoliciesSection(
																						policies,
																						{ bg: 'bg-[#F0FDF4]', border: 'border-[#BBF7D0]', text: 'text-[#059669]' }
																					)}
																				</Disclosure.Panel>
																			</div>
																		)}
																	</Disclosure>
																));
															})()}
														</div>
													)}

													{/* System Policies Tab */}
													{activePolicyTab === 'system' && (
														<div>
															{renderPoliciesSection(
																filteredPolicies.filter(p => p.type === 'system'),
																{ bg: 'bg-[#FEF3F2]', border: 'border-[#FED7D7]', text: 'text-[#DC2626]' }
															)}
														</div>
													)}

													{/* Package Policies Tab */}
													{activePolicyTab === 'package' && (
														<div className="space-y-[16px]">
															{(() => {
																const packagePolicies = filteredPolicies.filter(
																	policy => policy.path && policy.path.startsWith('packages.')
																);
																const groupedPackages = packagePolicies.reduce((acc, policy) => {
																	const packageName = policy.path.split('.')[1];
																	if (!acc[packageName]) {
																		acc[packageName] = [];
																	}
																	acc[packageName].push(policy);
																	return acc;
																}, {});

																return Object.entries(groupedPackages).map(([packageName, policies]) => (
																	<Disclosure key={packageName} defaultOpen={expandedSections[`package-${packageName}`]}>
																		{({ open }) => (
																			<div className="border border-[#E5E7EB] rounded-[8px] overflow-hidden">
																				<Disclosure.Button
																					onClick={() => toggleSection(`package-${packageName}`)}
																					className="w-full px-[16px] py-[12px] bg-[#EBF8FF] hover:bg-[#BFE6FF] transition-colors flex items-center justify-between"
																				>
																					<div className="flex items-center gap-[8px]">
																						<h4 className="text-[14px] font-semibold text-[#111827] capitalize">{packageName} Package</h4>
																						<span className="px-[8px] py-[2px] bg-[#2563EB] text-white text-[11px] rounded-[12px]">
																							{policies.length}
																						</span>
																					</div>
																					<svg
																						className={`w-[16px] h-[16px] text-[#6B7280] transition-transform ${open ? 'rotate-180' : ''}`}
																						fill="none"
																						stroke="currentColor"
																						viewBox="0 0 24 24"
																					>
																						<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
																					</svg>
																				</Disclosure.Button>
																				<Disclosure.Panel className="p-[16px] bg-white">
																					{renderPoliciesSection(
																						policies,
																						{ bg: 'bg-[#EBF8FF]', border: 'border-[#BFE6FF]', text: 'text-[#2563EB]' }
																					)}
																				</Disclosure.Panel>
																			</div>
																		)}
																	</Disclosure>
																));
															})()}
														</div>
													)}

													{/* Module Policies Tab */}
													{activePolicyTab === 'module' && (
														<div className="space-y-[16px]">
															{(() => {
																const modulePolicies = filteredPolicies.filter(
																	policy => policy.path && !policy.path.startsWith('packages.') && policy.type !== 'system'
																);
																const groupedModules = modulePolicies.reduce((acc, policy) => {
																	const moduleName = policy.path;
																	if (!acc[moduleName]) {
																		acc[moduleName] = [];
																	}
																	acc[moduleName].push(policy);
																	return acc;
																}, {});

																return Object.entries(groupedModules).map(([moduleName, policies]) => (
																	<Disclosure key={moduleName} defaultOpen={expandedSections[`module-${moduleName}`]}>
																		{({ open }) => (
																			<div className="border border-[#E5E7EB] rounded-[8px] overflow-hidden">
																				<Disclosure.Button
																					onClick={() => toggleSection(`module-${moduleName}`)}
																					className="w-full px-[16px] py-[12px] bg-[#F0FDF4] hover:bg-[#BBF7D0] transition-colors flex items-center justify-between"
																				>
																					<div className="flex items-center gap-[8px]">
																						<h4 className="text-[14px] font-semibold text-[#111827]">{moduleName} Module</h4>
																						<span className="px-[8px] py-[2px] bg-[#059669] text-white text-[11px] rounded-[12px]">
																							{policies.length}
																						</span>
																					</div>
																					<svg
																						className={`w-[16px] h-[16px] text-[#6B7280] transition-transform ${open ? 'rotate-180' : ''}`}
																						fill="none"
																						stroke="currentColor"
																						viewBox="0 0 24 24"
																					>
																						<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
																					</svg>
																				</Disclosure.Button>
																				<Disclosure.Panel className="p-[16px] bg-white">
																					{renderPoliciesSection(
																						policies,
																						{ bg: 'bg-[#F0FDF4]', border: 'border-[#BBF7D0]', text: 'text-[#059669]' }
																					)}
																				</Disclosure.Panel>
																			</div>
																		)}
																	</Disclosure>
																));
															})()}
														</div>
													)}
												</div>
											</div>
										) : (
											<div className="text-center py-[40px]">
												<p className="text-[14px] text-[#6B7280]">No policies attached to this role</p>
											</div>
										)}
										
									</div>
								)}
							</>
						)}
					</div>
				</div>
			</div>
			
			{/* Policy Selector Modal */}
			{isAddPolicyModalOpen && (
				<div className="fixed inset-0 z-[60] flex items-center justify-center">
					<div 
						className="fixed inset-0 bg-black bg-opacity-50"
						onClick={() => setIsAddPolicyModalOpen(false)}
					/>
					<div className="relative bg-white rounded-[12px] w-[600px] max-h-[80vh] overflow-hidden shadow-xl">
						{/* Header */}
						<div className="flex items-center justify-between px-[24px] py-[16px] border-b border-[#E5E7EB]">
							<h3 className="text-[18px] font-semibold text-[#111827]">Add Policies</h3>
							<button
								onClick={() => setIsAddPolicyModalOpen(false)}
								className="p-[4px] hover:bg-[#F3F4F6] rounded-[6px] transition-colors"
							>
								<svg className="w-[20px] h-[20px] text-[#6B7280]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
								</svg>
							</button>
						</div>
						
						{/* Search */}
						<div className="px-[24px] py-[16px] border-b border-[#E5E7EB]">
							<div className="relative">
								<input
									type="text"
									placeholder="Search policies..."
									value={policySearchTerm}
									onChange={(e) => setPolicySearchTerm(e.target.value)}
									className="w-full px-[36px] py-[8px] text-[14px] border border-[#E5E7EB] rounded-[6px] focus:outline-none focus:border-[#5048ED]"
								/>
								<svg className="absolute left-[12px] top-[50%] transform -translate-y-[50%] w-[16px] h-[16px] text-[#6B7280]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
								</svg>
							</div>
						</div>
						
						{/* Policy List */}
						<div className="px-[24px] py-[16px] max-h-[400px] overflow-y-auto">
							{availablePolicies.length > 0 ? (
								<div className="space-y-[8px]">
									{availablePolicies
										.filter(policy => 
											policy.label?.toLowerCase().includes(policySearchTerm.toLowerCase()) ||
											policy.path?.toLowerCase().includes(policySearchTerm.toLowerCase())
										)
										.map(policy => (
											<label
												key={policy.id}
												className="flex items-start gap-[12px] p-[12px] border border-[#E5E7EB] rounded-[8px] hover:bg-[#F9FAFB] cursor-pointer"
											>
												<input
													type="checkbox"
													checked={tempSelectedPolicies.includes(policy.id)}
													onChange={(e) => {
														if (e.target.checked) {
															setTempSelectedPolicies(prev => [...prev, policy.id]);
														} else {
															setTempSelectedPolicies(prev => prev.filter(id => id !== policy.id));
														}
													}}
													className="mt-[2px] w-[16px] h-[16px] text-[#5048ED] rounded border-[#D1D5DB] focus:ring-[#5048ED]"
												/>
												<div className="flex-1">
													<p className="text-[14px] font-medium text-[#111827]">{policy.label}</p>
													<p className="text-[12px] text-[#6B7280]">
														{policy.type === 'system' ? 'System Policy' : 
														 policy.path ? `Path: ${policy.path}` : 'User Policy'}
													</p>
												</div>
											</label>
										))}
								</div>
							) : (
								<p className="text-center text-[14px] text-[#6B7280] py-[40px]">
									No available policies to add
								</p>
							)}
						</div>
						
						{/* Footer */}
						<div className="flex items-center justify-between px-[24px] py-[16px] border-t border-[#E5E7EB]">
							<p className="text-[13px] text-[#6B7280]">
								{tempSelectedPolicies.length} {tempSelectedPolicies.length === 1 ? 'policy' : 'policies'} selected
							</p>
							<div className="flex gap-[8px]">
								<button
									onClick={() => {
										setIsAddPolicyModalOpen(false);
										setTempSelectedPolicies([]);
										setPolicySearchTerm('');
									}}
									className="px-[16px] py-[6px] bg-[#F3F4F6] text-[#6B7280] rounded-[6px] text-[13px] font-medium hover:bg-[#E5E7EB] transition-colors"
								>
									Cancel
								</button>
								<button
									onClick={() => {
										// Add selected policies to attachedPolicies
										const newPolicies = availablePolicies.filter(p => tempSelectedPolicies.includes(p.id));
										setAttachedPolicies(prev => [...prev, ...newPolicies]);
										// Track which policies are newly added
										setSelectedPoliciesForAddition(prev => [...prev, ...tempSelectedPolicies]);
										setHasUnsavedChanges(true);
										setIsAddPolicyModalOpen(false);
										setTempSelectedPolicies([]);
										setPolicySearchTerm('');
									}}
									disabled={tempSelectedPolicies.length === 0}
									className="px-[16px] py-[6px] bg-[#5048ED] text-white rounded-[6px] text-[13px] font-medium hover:bg-[#4338CA] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
								>
									Add Selected
								</button>
							</div>
						</div>
					</div>
				</div>
			)}
		</RoleDetailsModalWrapper>
	);
}

export default RoleDetailsModal;