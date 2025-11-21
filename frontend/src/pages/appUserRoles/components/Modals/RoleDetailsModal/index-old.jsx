import { useState, useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { useParams } from 'react-router-dom';
import RoleDetailsModalWrapper from './RoleDetailsModalWrapper';
import useApi from '../../../../../hooks/useApi';
import {
	openIsEditUserRolesDetailModalOpen,
	openIsDeactivateUserRolesModalOpen,
	openIsActivateUserRolesModalOpen,
	toggleRerenderPage,
} from '../../../slice';

function RoleDetailsModal({ isOpen, closeModal, role }) {
	const { appId } = useParams();
	const dispatch = useDispatch();
	const triggerApi = useApi();

	const [activeTab, setActiveTab] = useState('policies');
	const [roleDetails, setRoleDetails] = useState(null);
	const [loading, setLoading] = useState(false);
	const [attachedPolicies, setAttachedPolicies] = useState([]);
	const [availablePolicies, setAvailablePolicies] = useState([]);
	const [selectedPolicies, setSelectedPolicies] = useState([]);
	const [searchTerm, setSearchTerm] = useState('');

	// Check if this is a reserved role
	const isReservedRole = role?.name === 'AnonymousUsers' || role?.name === 'SystemUsers';

	// Fetch role details when modal opens
	useEffect(() => {
		if (isOpen && role) {
			fetchRoleDetails();
		}
	}, [isOpen, role]);

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
			}
		} catch (error) {
			console.error('Error fetching role details:', error);
		} finally {
			setLoading(false);
		}
	};

	const fetchAvailablePolicies = async () => {
		try {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/policies/?page_size=100`,
				type: 'GET',
				loader: false,
			});
			if (success && response) {
				setAvailablePolicies(response.policies?.records || []);
			}
		} catch (error) {
			console.error('Error fetching policies:', error);
		}
	};

	// Fetch available policies when policies tab is active
	useEffect(() => {
		if (activeTab === 'policies' && availablePolicies.length === 0) {
			fetchAvailablePolicies();
		}
	}, [activeTab]);

	const handleEditRole = () => {
		dispatch(openIsEditUserRolesDetailModalOpen(role));
		closeModal();
	};

	const handleToggleStatus = () => {
		if (role.is_active) {
			dispatch(openIsDeactivateUserRolesModalOpen(role));
		} else {
			dispatch(openIsActivateUserRolesModalOpen(role));
		}
		closeModal();
	};

	const handleAttachPolicies = async () => {
		try {
			const { success } = await triggerApi({
				url: `/api/v1/apps/${appId}/roles/${role.id}/`,
				type: 'PATCH',
				loader: true,
				data: {
					policies: [...attachedPolicies.map(p => p.id), ...selectedPolicies],
				},
			});
			if (success) {
				dispatch(toggleRerenderPage());
				fetchRoleDetails();
				setSelectedPolicies([]);
			}
		} catch (error) {
			console.error('Error attaching policies:', error);
		}
	};

	const handleDetachPolicy = async (policyId) => {
		try {
			const { success } = await triggerApi({
				url: `/api/v1/apps/${appId}/roles/${role.id}/`,
				type: 'PATCH',
				loader: true,
				data: {
					policies: attachedPolicies.filter(p => p.id !== policyId).map(p => p.id),
				},
			});
			if (success) {
				dispatch(toggleRerenderPage());
				fetchRoleDetails();
			}
		} catch (error) {
			console.error('Error detaching policy:', error);
		}
	};

	const filteredAvailablePolicies = availablePolicies.filter(policy => {
		const isNotAttached = !attachedPolicies.some(ap => ap.id === policy.id);
		const matchesSearch = policy.name.toLowerCase().includes(searchTerm.toLowerCase());
		return isNotAttached && matchesSearch;
	});

	const tabs = [
		{ id: 'overview', label: 'Overview' },
		{ id: 'policies', label: 'Policies' },
		...(isReservedRole ? [] : [{ id: 'settings', label: 'Settings' }]),
	];

	const ModalContent = () => (
		<div className="flex h-[600px]">
			{/* Sidebar */}
			<div className="w-[200px] border-r border-[#E5E7EB] bg-[#F9FAFB] p-[20px]">
				<div className="space-y-[4px]">
					{tabs.map((tab) => (
						<button
							key={tab.id}
							onClick={() => setActiveTab(tab.id)}
							className={`w-full flex items-center gap-[8px] px-[12px] py-[8px] rounded-[6px] text-left transition-colors ${
								activeTab === tab.id
									? 'bg-[#5048ED] text-white'
									: 'hover:bg-white text-[#6B7280]'
							}`}
						>
							{tab.id === 'overview' && (
								<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
									<path d="M2 5C2 3.89543 2.89543 3 4 3H12C13.1046 3 14 3.89543 14 5V11C14 12.1046 13.1046 13 12 13H4C2.89543 13 2 12.1046 2 11V5Z" stroke="currentColor" strokeWidth="1.5"/>
									<path d="M5 7H11M5 9H8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
								</svg>
							)}
							{tab.id === 'policies' && (
								<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
									<path d="M8 2L3 5V8C3 11.5 5 13.5 8 14C11 13.5 13 11.5 13 8V5L8 2Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
									<path d="M6 8L7.5 9.5L10.5 6.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
								</svg>
							)}
							{tab.id === 'settings' && (
								<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
									<path d="M8 10C9.10457 10 10 9.10457 10 8C10 6.89543 9.10457 6 8 6C6.89543 6 6 6.89543 6 8C6 9.10457 6.89543 10 8 10Z" stroke="currentColor" strokeWidth="1.5"/>
									<path d="M13 8C13 8.34 12.98 8.67 12.94 9L14.19 10.07C14.31 10.17 14.34 10.35 14.27 10.49L13.07 12.51C13 12.65 12.82 12.71 12.68 12.65L11.19 12.03C10.88 12.26 10.54 12.45 10.17 12.59L9.92 14.17C9.9 14.32 9.77 14.43 9.62 14.43H7.22C7.07 14.43 6.94 14.32 6.92 14.17L6.67 12.59C6.3 12.45 5.96 12.27 5.65 12.03L4.16 12.65C4.02 12.71 3.84 12.65 3.77 12.51L2.57 10.49C2.5 10.35 2.53 10.17 2.65 10.07L3.9 9C3.86 8.67 3.84 8.34 3.84 8C3.84 7.66 3.86 7.33 3.9 7L2.65 5.93C2.53 5.83 2.5 5.65 2.57 5.51L3.77 3.49C3.84 3.35 4.02 3.29 4.16 3.35L5.65 3.97C5.96 3.74 6.3 3.55 6.67 3.41L6.92 1.83C6.94 1.68 7.07 1.57 7.22 1.57H9.62C9.77 1.57 9.9 1.68 9.92 1.83L10.17 3.41C10.54 3.55 10.88 3.73 11.19 3.97L12.68 3.35C12.82 3.29 13 3.35 13.07 3.49L14.27 5.51C14.34 5.65 14.31 5.83 14.19 5.93L12.94 7C12.98 7.33 13 7.66 13 8Z" stroke="currentColor" strokeWidth="1.5"/>
								</svg>
							)}
							<span className="text-[14px] font-medium">{tab.label}</span>
						</button>
					))}
				</div>
			</div>

			{/* Content */}
			<div className="flex-1 overflow-hidden bg-white">
						{loading ? (
							<div className="flex items-center justify-center h-full">
								<div className="animate-spin rounded-full h-[40px] w-[40px] border-b-2 border-[#5048ED]"></div>
							</div>
						) : (
							<>
								{/* Overview Tab */}
								{activeTab === 'overview' && (
									<div className="p-[24px] h-full overflow-y-auto">
										<div className="space-y-[24px]">
											{/* Role Info */}
											<div>
												<h3 className="text-[18px] font-semibold text-[#111827] mb-[16px]">Role Information</h3>
												<div className="bg-[#F9FAFB] rounded-[8px] p-[16px] space-y-[12px]">
													<div>
														<p className="text-[12px] text-[#6B7280] mb-[4px]">Role Name</p>
														<p className="text-[14px] text-[#111827] font-medium">{role?.name}</p>
													</div>
													<div>
														<p className="text-[12px] text-[#6B7280] mb-[4px]">Status</p>
														<span className={`inline-flex px-[8px] py-[2px] rounded-[4px] text-[12px] font-medium ${
															role?.is_active
																? 'bg-[#D1FAE5] text-[#10B981]'
																: 'bg-[#FEE2E2] text-[#EF4444]'
														}`}>
															{role?.is_active ? 'Active' : 'Inactive'}
														</span>
													</div>
													<div>
														<p className="text-[12px] text-[#6B7280] mb-[4px]">Type</p>
														<p className="text-[14px] text-[#111827]">
															{isReservedRole ? 'System Reserved' : 'User Defined'}
														</p>
													</div>
													<div>
														<p className="text-[12px] text-[#6B7280] mb-[4px]">Created</p>
														<p className="text-[14px] text-[#111827]">
															{role?.created_at ? new Date(role.created_at).toLocaleDateString() : 'N/A'}
														</p>
													</div>
												</div>
											</div>

											{/* Statistics */}
											<div>
												<h3 className="text-[18px] font-semibold text-[#111827] mb-[16px]">Statistics</h3>
												<div className="grid grid-cols-3 gap-[16px]">
													<div className="bg-[#EFF6FF] rounded-[8px] p-[16px]">
														<p className="text-[24px] font-bold text-[#3730A3]">
															{role?.policies_count?.policies || 0}
														</p>
														<p className="text-[14px] text-[#6B7280]">Direct Policies</p>
													</div>
													<div className="bg-[#F0FDF4] rounded-[8px] p-[16px]">
														<p className="text-[24px] font-bold text-[#10B981]">
															{role?.policies_count?.policy_groups || 0}
														</p>
														<p className="text-[14px] text-[#6B7280]">Policy Groups</p>
													</div>
													<div className="bg-[#FEF3C7] rounded-[8px] p-[16px]">
														<p className="text-[24px] font-bold text-[#F59E0B]">
															{role?.policies_count?.total || 0}
														</p>
														<p className="text-[14px] text-[#6B7280]">Total Policies</p>
													</div>
												</div>
											</div>

											{/* Actions */}
											<div>
												<h3 className="text-[18px] font-semibold text-[#111827] mb-[16px]">Quick Actions</h3>
												<div className="flex gap-[12px]">
													{!isReservedRole && (
														<>
															<button
																onClick={handleEditRole}
																className="px-[16px] py-[8px] bg-[#5048ED] text-white rounded-[6px] text-[14px] font-medium hover:bg-[#4338CA] transition-colors"
															>
																Edit Role
															</button>
															<button
																onClick={handleToggleStatus}
																className={`px-[16px] py-[8px] rounded-[6px] text-[14px] font-medium transition-colors ${
																	role?.is_active
																		? 'bg-[#FEE2E2] text-[#EF4444] hover:bg-[#FECACA]'
																		: 'bg-[#D1FAE5] text-[#10B981] hover:bg-[#A7F3D0]'
																}`}
															>
																{role?.is_active ? 'Deactivate' : 'Activate'}
															</button>
														</>
													)}
												</div>
											</div>
										</div>
									</div>
								)}

								{/* Policies Tab */}
								{activeTab === 'policies' && (
									<div className="flex flex-col h-full">
										<div className="p-[24px] border-b border-[#E5E7EB]">
											<h3 className="text-[18px] font-semibold text-[#111827] mb-[16px]">Policy Management</h3>
											
											{/* Search and Add */}
											<div className="flex gap-[12px]">
												<input
													type="text"
													placeholder="Search policies..."
													value={searchTerm}
													onChange={(e) => setSearchTerm(e.target.value)}
													className="flex-1 px-[12px] py-[8px] border border-[#E5E7EB] rounded-[6px] text-[14px]"
												/>
												{selectedPolicies.length > 0 && (
													<button
														onClick={handleAttachPolicies}
														className="px-[16px] py-[8px] bg-[#5048ED] text-white rounded-[6px] text-[14px] font-medium hover:bg-[#4338CA] transition-colors"
													>
														Attach {selectedPolicies.length} {selectedPolicies.length === 1 ? 'Policy' : 'Policies'}
													</button>
												)}
											</div>
										</div>

										<div className="flex-1 overflow-hidden flex">
											{/* Attached Policies */}
											<div className="flex-1 p-[24px] overflow-y-auto">
												<h4 className="text-[16px] font-semibold text-[#111827] mb-[12px]">
													Attached Policies ({attachedPolicies.length})
												</h4>
												<div className="space-y-[8px]">
													{attachedPolicies.length > 0 ? (
														attachedPolicies.map((policy) => (
															<div
																key={policy.id}
																className="flex items-center justify-between p-[12px] bg-[#F9FAFB] rounded-[6px] hover:bg-[#F3F4F6] transition-colors"
															>
																<div>
																	<p className="text-[14px] font-medium text-[#111827]">{policy.name}</p>
																	{policy.description && (
																		<p className="text-[12px] text-[#6B7280] mt-[2px]">{policy.description}</p>
																	)}
																</div>
																<button
																	onClick={() => handleDetachPolicy(policy.id)}
																	className="px-[12px] py-[4px] text-[#EF4444] hover:bg-[#FEE2E2] rounded-[4px] text-[13px] font-medium transition-colors"
																>
																	Detach
																</button>
															</div>
														))
													) : (
														<p className="text-[14px] text-[#6B7280]">No policies attached</p>
													)}
												</div>
											</div>

											{/* Available Policies */}
											<div className="flex-1 p-[24px] border-l border-[#E5E7EB] overflow-y-auto">
												<h4 className="text-[16px] font-semibold text-[#111827] mb-[12px]">
													Available Policies ({filteredAvailablePolicies.length})
												</h4>
												<div className="space-y-[8px]">
													{filteredAvailablePolicies.length > 0 ? (
														filteredAvailablePolicies.map((policy) => (
															<div
																key={policy.id}
																className="flex items-center justify-between p-[12px] bg-white border border-[#E5E7EB] rounded-[6px] hover:border-[#5048ED] transition-colors"
															>
																<div className="flex items-center gap-[12px]">
																	<input
																		type="checkbox"
																		checked={selectedPolicies.includes(policy.id)}
																		onChange={(e) => {
																			if (e.target.checked) {
																				setSelectedPolicies([...selectedPolicies, policy.id]);
																			} else {
																				setSelectedPolicies(selectedPolicies.filter(id => id !== policy.id));
																			}
																		}}
																		className="w-[16px] h-[16px] text-[#5048ED] rounded"
																	/>
																	<div>
																		<p className="text-[14px] font-medium text-[#111827]">{policy.name}</p>
																		{policy.description && (
																			<p className="text-[12px] text-[#6B7280] mt-[2px]">{policy.description}</p>
																		)}
																	</div>
																</div>
															</div>
														))
													) : (
														<p className="text-[14px] text-[#6B7280]">No available policies found</p>
													)}
												</div>
											</div>
										</div>
									</div>
								)}

								{/* Settings Tab */}
								{activeTab === 'settings' && !isReservedRole && (
									<div className="p-[24px] h-full overflow-y-auto">
										<div className="space-y-[24px]">
											<div>
												<h3 className="text-[18px] font-semibold text-[#111827] mb-[16px]">Role Settings</h3>
												<div className="space-y-[16px]">
													<div className="bg-[#F9FAFB] rounded-[8px] p-[16px]">
														<h4 className="text-[16px] font-medium text-[#111827] mb-[8px]">Authentication Configuration</h4>
														<div className="space-y-[8px]">
															<div>
																<p className="text-[12px] text-[#6B7280] mb-[2px]">Redirect URL</p>
																<p className="text-[14px] text-[#111827]">{roleDetails?.auth_config?.redirect_url || '/frame/router/'}</p>
															</div>
														</div>
													</div>

													<div className="flex gap-[12px]">
														<button
															onClick={handleEditRole}
															className="px-[16px] py-[8px] bg-[#5048ED] text-white rounded-[6px] text-[14px] font-medium hover:bg-[#4338CA] transition-colors"
														>
															Edit Settings
														</button>
													</div>
												</div>
											</div>
										</div>
									</div>
								)}
							</>
						)}
					</div>
				</div>
		);

	return (
		<RoleDetailsModalWrapper
			label={`${role?.name} - Role Details`}
			show={isOpen}
			closeModal={closeModal}
		>
			<ModalContent />
		</RoleDetailsModalWrapper>
	);
}

export default RoleDetailsModal;