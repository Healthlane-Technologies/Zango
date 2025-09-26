import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import useApi from '../../../../hooks/useApi';

export default function Policies({ data }) {
	const { appId } = useParams();
	const triggerApi = useApi();
	const [policies, setPolicies] = useState([]);
	const [loading, setLoading] = useState(true);
	const [searchTerm, setSearchTerm] = useState('');
	const [expandedPolicies, setExpandedPolicies] = useState({});
	const [page, setPage] = useState(1);
	const [totalPages, setTotalPages] = useState(1);
	const [pageSize] = useState(10);
	const [editModalOpen, setEditModalOpen] = useState(false);
	const [viewConfigModalOpen, setViewConfigModalOpen] = useState(false);
	const [editingPolicy, setEditingPolicy] = useState(null);
	const [viewingPolicy, setViewingPolicy] = useState(null);
	const [selectedRoles, setSelectedRoles] = useState([]);
	const [availableRoles, setAvailableRoles] = useState([]);


	// Fetch policies from API
	const fetchPolicies = async () => {
		setLoading(true);
		try {
			const queryParams = new URLSearchParams({
				page: page.toString(),
				page_size: pageSize.toString(),
				include_dropdown_options: 'true',
				search: searchTerm,
			});

			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/policies/?${queryParams.toString()}`,
				type: 'GET',
				loader: false,
			});

			if (success && response?.policies) {
				setPolicies(response.policies.records || []);
				setTotalPages(response.policies.total_pages || 1);
				if (response.dropdown_options?.roles) {
					setAvailableRoles(response.dropdown_options.roles);
				}
			}
		} catch (error) {
			console.error('Error fetching policies:', error);
		} finally {
			setLoading(false);
		}
	};

	useEffect(() => {
		fetchPolicies();
	}, [appId, page, searchTerm]);

	// Toggle policy expansion
	const togglePolicyExpansion = (policyId) => {
		setExpandedPolicies(prev => ({
			...prev,
			[policyId]: !prev[policyId]
		}));
	};

	// Sync policies
	const syncPolicies = async () => {
		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/policies/?action=sync_policies`,
			type: 'POST',
			loader: true,
			payload: new FormData(),
		});

		if (success) {
			fetchPolicies();
		}
	};

	// Open edit modal
	const openEditModal = (policy) => {
		setEditingPolicy(policy);
		setSelectedRoles(policy.roles || []);
		setEditModalOpen(true);
	};

	// Close edit modal
	const closeEditModal = () => {
		setEditModalOpen(false);
		setEditingPolicy(null);
		setSelectedRoles([]);
	};

	// Update policy
	const updatePolicy = async () => {
		if (!editingPolicy) return;

		const formData = new FormData();
		formData.append('id', editingPolicy.id);
		selectedRoles.forEach(role => {
			formData.append('roles', role.id);
		});

		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/policies/${editingPolicy.id}/`,
			type: 'PUT',
			loader: true,
			payload: formData,
		});

		if (success) {
			closeEditModal();
			fetchPolicies();
		}
	};

	// Open view config modal
	const openViewConfigModal = (policy) => {
		setViewingPolicy(policy);
		setViewConfigModalOpen(true);
	};

	// Close view config modal
	const closeViewConfigModal = () => {
		setViewConfigModalOpen(false);
		setViewingPolicy(null);
	};

	// Toggle role selection
	const toggleRoleSelection = (role) => {
		setSelectedRoles(prev => {
			const exists = prev.find(r => r.id === role.id);
			if (exists) {
				return prev.filter(r => r.id !== role.id);
			} else {
				return [...prev, role];
			}
		});
	};

	return (
		<div className="space-y-6">
			{/* Header */}
			<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
				<div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
					<div>
						<h2 className="text-xl font-semibold text-gray-900">Security Policies</h2>
						<p className="text-sm text-gray-600 mt-1">
							Manage application security policies and role assignments
						</p>
					</div>
					<div className="flex flex-wrap gap-3">
						{/* Search */}
						<div className="relative">
							<input
								type="text"
								placeholder="Search policies..."
								value={searchTerm}
								onChange={(e) => setSearchTerm(e.target.value)}
								className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent w-full sm:w-64"
							/>
							<svg
								className="absolute left-3 top-2.5 h-5 w-5 text-gray-400"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									strokeLinecap="round"
									strokeLinejoin="round"
									strokeWidth={2}
									d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
								/>
							</svg>
						</div>

						{/* Sync Button */}
						<button
							onClick={syncPolicies}
							className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
						>
							<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
								<path
									d="M13.65 2.35a8 8 0 11-11.3 0"
									stroke="currentColor"
									strokeWidth="1.5"
									strokeLinecap="round"
								/>
								<path
									d="M8 2v4m0 0L6 4m2 2l2-2"
									stroke="currentColor"
									strokeWidth="1.5"
									strokeLinecap="round"
									strokeLinejoin="round"
								/>
							</svg>
							Sync Policies
						</button>
					</div>
				</div>
			</div>

			{/* Policies Table */}
			<div className="bg-white rounded-lg shadow-sm border border-gray-200">
				{loading ? (
					<div className="flex items-center justify-center py-12">
						<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
					</div>
				) : policies.length === 0 ? (
					<div className="text-center py-12">
						<svg
							className="mx-auto h-12 w-12 text-gray-300"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								strokeLinecap="round"
								strokeLinejoin="round"
								strokeWidth={1.5}
								d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
							/>
						</svg>
						<p className="mt-2 text-sm text-gray-500">No policies found</p>
						<button
							onClick={syncPolicies}
							className="mt-4 text-sm text-blue-600 hover:text-blue-700 font-medium"
						>
							Sync policies from codebase
						</button>
					</div>
				) : (
					<>
						<div className="overflow-x-auto">
							<table className="min-w-full divide-y divide-gray-200">
								<thead>
									<tr>
										<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
											Policy
										</th>
										<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
											Configuration
										</th>
										<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
											Roles
										</th>
									</tr>
								</thead>
								<tbody className="bg-white divide-y divide-gray-200">
									{policies.map((policy) => {
										const isExpanded = expandedPolicies[policy.id];
										
										return (
											<React.Fragment key={policy.id}>
												<tr className={`hover:bg-gray-50 ${isExpanded ? 'bg-gray-50' : ''}`}>
													<td className="px-6 py-4 whitespace-nowrap">
														<div className="flex items-center gap-2">
															<button
																onClick={() => togglePolicyExpansion(policy.id)}
																className="p-1 hover:bg-gray-200 rounded transition-colors"
															>
																<svg
																	className={`w-4 h-4 text-gray-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
																	fill="none"
																	viewBox="0 0 24 24"
																	stroke="currentColor"
																>
																	<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
																</svg>
															</button>
															<div>
																<div className="text-sm font-medium text-gray-900">
																	{policy.name}
																</div>
																<div className="text-sm text-gray-500">
																	ID: {policy.id}
																</div>
															</div>
														</div>
													</td>
													<td className="px-6 py-4 whitespace-nowrap">
														<button
															onClick={() => openViewConfigModal(policy)}
															className="text-blue-600 hover:text-blue-700 text-sm font-medium"
														>
															View Config
														</button>
													</td>
													<td className="px-6 py-4">
														<div className="flex items-center justify-between">
															<div className="flex flex-wrap gap-1">
																{policy.roles?.slice(0, 3).map((role, idx) => (
																	<span
																		key={idx}
																		className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
																	>
																		{role.name}
																	</span>
																))}
																{policy.roles?.length > 3 && (
																	<span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
																		+{policy.roles.length - 3} more
																	</span>
																)}
															</div>
															<button
																onClick={() => openEditModal(policy)}
																className="ml-3 inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 hover:border-blue-300 transition-colors"
															>
																<svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor">
																	<path d="M11.013 1.427a1.75 1.75 0 012.474 0l1.086 1.086a1.75 1.75 0 010 2.474l-8.61 8.61c-.21.21-.47.364-.756.445l-3.251.93a.75.75 0 01-.927-.928l.929-3.25a1.75 1.75 0 01.445-.758l8.61-8.61z" />
																	<path d="M11.013 1.427a1.75 1.75 0 012.474 0l1.086 1.086a1.75 1.75 0 010 2.474l-8.61 8.61c-.21.21-.47.364-.756.445l-3.251.93a.75.75 0 01-.927-.928l.929-3.25a1.75 1.75 0 01.445-.758l8.61-8.61z" />
																</svg>
																Edit
															</button>
														</div>
													</td>
												</tr>

												{isExpanded && (
													<tr>
														<td colSpan="3" className="p-0">
															<div className="bg-blue-50 border-t border-b border-blue-100">
																<div className="px-6 py-4">
																	<div className="space-y-4">
																		{/* Policy Details */}
																		<div>
																			<h5 className="text-sm font-medium text-gray-900 mb-2">Policy Details</h5>
																			<div className="bg-white rounded-lg border border-gray-200 p-4">
																				<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
																					<div>
																						<span className="text-xs text-gray-500 font-medium">Description:</span>
																						<p className="text-sm text-gray-700 mt-1">
																							{policy.description || 'No description available'}
																						</p>
																					</div>
																					<div>
																						<span className="text-xs text-gray-500 font-medium">Created:</span>
																						<p className="text-sm text-gray-700 mt-1">
																							{policy.created_at ? new Date(policy.created_at).toLocaleString() : 'N/A'}
																						</p>
																					</div>
																				</div>
																			</div>
																		</div>

																		{/* Assigned Roles */}
																		{policy.roles?.length > 0 && (
																			<div>
																				<h5 className="text-sm font-medium text-gray-900 mb-2">Assigned Roles</h5>
																				<div className="bg-white rounded-lg border border-gray-200 p-4">
																					<div className="flex flex-wrap gap-2">
																						{policy.roles.map((role, idx) => (
																							<div
																								key={idx}
																								className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-50 border border-gray-200"
																							>
																								<svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor" className="text-gray-400">
																									<path d="M8 8a3 3 0 100-6 3 3 0 000 6zM12.735 14c.618 0 1.093-.561.872-1.139a6.002 6.002 0 00-11.215 0c-.22.578.254 1.139.872 1.139h9.47z" />
																								</svg>
																								<span className="text-sm text-gray-700">{role.name}</span>
																							</div>
																						))}
																					</div>
																				</div>
																			</div>
																		)}
																	</div>
																</div>
															</div>
														</td>
													</tr>
												)}
											</React.Fragment>
										);
									})}
								</tbody>
							</table>
						</div>

						{/* Pagination */}
						{totalPages > 1 && (
							<div className="bg-gray-50 px-6 py-3 flex items-center justify-between border-t border-gray-200">
								<div className="flex items-center gap-2">
									<button
										onClick={() => setPage(p => Math.max(1, p - 1))}
										disabled={page === 1}
										className="p-2 rounded-lg border border-gray-300 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
									>
										<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
											<path d="M10 12L6 8L10 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
										</svg>
									</button>
									<span className="text-sm text-gray-700">
										Page {page} of {totalPages}
									</span>
									<button
										onClick={() => setPage(p => Math.min(totalPages, p + 1))}
										disabled={page === totalPages}
										className="p-2 rounded-lg border border-gray-300 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
									>
										<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
											<path d="M6 12L10 8L6 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
										</svg>
									</button>
								</div>
								<span className="text-sm text-gray-600">
									Showing {policies.length} policies
								</span>
							</div>
						)}
					</>
				)}
			</div>

			{/* Edit Roles Modal */}
			{editModalOpen && (
				<div className="fixed inset-0 z-50 overflow-y-auto">
					<div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
						{/* Background overlay */}
						<div 
							className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
							onClick={closeEditModal}
						></div>

						{/* Modal panel */}
						<div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
							{/* Modal header */}
							<div className="bg-white px-6 pt-6 pb-4">
								<div className="flex items-center justify-between">
									<h3 className="text-lg font-semibold text-gray-900">
										Edit Policy Roles
									</h3>
									<button
										onClick={closeEditModal}
										className="text-gray-400 hover:text-gray-500"
									>
										<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
										</svg>
									</button>
								</div>
								<p className="mt-2 text-sm text-gray-600">
									Policy: {editingPolicy?.name}
								</p>
							</div>

							{/* Modal body */}
							<div className="px-6 pb-4">
								<div className="space-y-2">
									<label className="block text-sm font-medium text-gray-700 mb-2">
										Assign Roles
									</label>
									<div className="max-h-64 overflow-y-auto border border-gray-200 rounded-lg">
										{availableRoles.map((role) => {
											const isSelected = selectedRoles.find(r => r.id === role.id);
											return (
												<div
													key={role.id}
													onClick={() => toggleRoleSelection(role)}
													className={`flex items-center justify-between p-3 cursor-pointer hover:bg-gray-50 ${
														isSelected ? 'bg-blue-50' : ''
													}`}
												>
													<div className="flex items-center gap-3">
														<div className={`w-5 h-5 border-2 rounded ${
															isSelected 
																? 'bg-blue-600 border-blue-600' 
																: 'border-gray-300'
														}`}>
															{isSelected && (
																<svg className="w-full h-full text-white" viewBox="0 0 20 20" fill="currentColor">
																	<path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
																</svg>
															)}
														</div>
														<div>
															<p className="text-sm font-medium text-gray-900">{role.label}</p>
															{role.is_reserved && (
																<span className="text-xs text-gray-500">System Role</span>
															)}
														</div>
													</div>
												</div>
											);
										})}
									</div>
								</div>
							</div>

							{/* Modal footer */}
							<div className="bg-gray-50 px-6 py-3 flex justify-end gap-3">
								<button
									onClick={closeEditModal}
									className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
								>
									Cancel
								</button>
								<button
									onClick={updatePolicy}
									className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700"
								>
									Save Changes
								</button>
							</div>
						</div>
					</div>
				</div>
			)}

			{/* View Configuration Modal */}
			{viewConfigModalOpen && (
				<div className="fixed inset-0 z-50 overflow-y-auto">
					<div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
						{/* Background overlay */}
						<div 
							className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
							onClick={closeViewConfigModal}
						></div>

						{/* Modal panel */}
						<div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-3xl sm:w-full">
							{/* Modal header */}
							<div className="bg-white px-6 pt-6 pb-4">
								<div className="flex items-center justify-between">
									<h3 className="text-lg font-semibold text-gray-900">
										Policy Configuration
									</h3>
									<button
										onClick={closeViewConfigModal}
										className="text-gray-400 hover:text-gray-500"
									>
										<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
										</svg>
									</button>
								</div>
								<p className="mt-2 text-sm text-gray-600">
									{viewingPolicy?.name}
								</p>
							</div>

							{/* Modal body */}
							<div className="px-6 pb-6">
								<div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
									<pre className="text-gray-100 text-sm">
										<code>
											{JSON.stringify(viewingPolicy?.statement || {}, null, 2)}
										</code>
									</pre>
								</div>
							</div>
						</div>
					</div>
				</div>
			)}
		</div>
	);
}