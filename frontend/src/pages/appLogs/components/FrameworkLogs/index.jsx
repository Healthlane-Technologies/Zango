import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import useApi from '../../../../hooks/useApi';

export default function FrameworkLogs() {
	const { appId } = useParams();
	const triggerApi = useApi();
	const [logs, setLogs] = useState([]);
	const [loading, setLoading] = useState(true);
	const [searchTerm, setSearchTerm] = useState('');
	const [expandedLogs, setExpandedLogs] = useState({});
	const [page, setPage] = useState(1);
	const [totalPages, setTotalPages] = useState(1);
	const [pageSize] = useState(20);
	const [filters, setFilters] = useState({
		action: '',
		model: '',
		user: ''
	});

	// Fetch logs
	const fetchLogs = async () => {
		setLoading(true);
		try {
			const queryParams = new URLSearchParams({
				page: page.toString(),
				page_size: pageSize.toString(),
				include_dropdown_options: 'true',
				search: searchTerm,
				model_type: 'platform'
			});

			// Add filters
			if (filters.action) {
				queryParams.append('search_action', filters.action);
			}
			if (filters.model) {
				queryParams.append('search_table', filters.model);
			}
			if (filters.user) {
				queryParams.append('search_actor', filters.user);
			}

			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/auditlog/?${queryParams.toString()}`,
				type: 'GET',
				loader: false,
			});

			if (success && response?.audit_logs) {
				setLogs(response.audit_logs.records || []);
				setTotalPages(response.audit_logs.total_pages || 1);
			}
		} catch (error) {
			console.error('Error fetching framework logs:', error);
		} finally {
			setLoading(false);
		}
	};

	useEffect(() => {
		fetchLogs();
	}, [appId, page, searchTerm, filters]);

	// Toggle log expansion
	const toggleLogExpansion = (logId) => {
		setExpandedLogs(prev => ({
			...prev,
			[logId]: !prev[logId]
		}));
	};

	// Format timestamp
	const formatTimestamp = (timestamp) => {
		const date = new Date(timestamp);
		const now = new Date();
		const diffMs = now - date;
		const diffMins = Math.floor(diffMs / 60000);
		const diffHours = Math.floor(diffMs / 3600000);
		const diffDays = Math.floor(diffMs / 86400000);

		if (diffMins < 1) return 'Just now';
		if (diffMins < 60) return `${diffMins} minutes ago`;
		if (diffHours < 24) return `${diffHours} hours ago`;
		if (diffDays < 7) return `${diffDays} days ago`;
		
		return date.toLocaleString();
	};

	// Get action badge color
	const getActionBadgeColor = (action) => {
		switch (action?.toLowerCase()) {
			case 'create':
			case 'insert':
				return 'bg-green-100 text-green-800';
			case 'update':
			case 'edit':
				return 'bg-blue-100 text-blue-800';
			case 'delete':
			case 'remove':
				return 'bg-red-100 text-red-800';
			default:
				return 'bg-gray-100 text-gray-800';
		}
	};

	// Get log severity
	const getLogSeverity = (log) => {
		if (log.action?.toLowerCase().includes('delete')) return 'high';
		if (log.action?.toLowerCase().includes('update')) return 'medium';
		return 'low';
	};

	// Get severity badge
	const getSeverityBadge = (severity) => {
		switch (severity) {
			case 'high':
				return { color: 'bg-red-100 text-red-800', icon: '🔴', label: 'High' };
			case 'medium':
				return { color: 'bg-yellow-100 text-yellow-800', icon: '🟡', label: 'Medium' };
			case 'low':
				return { color: 'bg-green-100 text-green-800', icon: '🟢', label: 'Low' };
			default:
				return { color: 'bg-gray-100 text-gray-800', icon: '⚪', label: 'Info' };
		}
	};

	// Format field changes
	const formatFieldChanges = (changes) => {
		if (!changes) return [];
		
		try {
			const parsed = typeof changes === 'string' ? JSON.parse(changes) : changes;
			return Object.entries(parsed).map(([field, values]) => ({
				field,
				oldValue: values[0],
				newValue: values[1]
			}));
		} catch (error) {
			return [];
		}
	};

	return (
		<div className="space-y-6">
			{/* Stats Overview */}
			<div className="grid grid-cols-1 md:grid-cols-4 gap-6">
				<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
					<div className="flex items-center justify-between">
						<div>
							<p className="text-sm font-medium text-gray-600">Total Framework Changes</p>
							<p className="text-2xl font-semibold text-gray-900 mt-1">{logs.length}</p>
						</div>
						<div className="p-3 bg-gray-100 rounded-lg">
							<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
								<path d="M12 2L2 7V12C2 16.5 4.23 20.68 8 21.93C11.77 20.68 14 16.5 14 12V7L12 2Z" fill="#6B7280" fillOpacity="0.2"/>
								<path d="M12 2L2 7V12C2 16.5 4.23 20.68 8 21.93C11.77 20.68 14 16.5 14 12V7L12 2Z" stroke="#6B7280" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
								<path d="M18 9V15M21 12H15" stroke="#6B7280" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
							</svg>
						</div>
					</div>
				</div>

				<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
					<div className="flex items-center justify-between">
						<div>
							<p className="text-sm font-medium text-gray-600">High Severity</p>
							<p className="text-2xl font-semibold text-red-600 mt-1">
								{logs.filter(log => getLogSeverity(log) === 'high').length}
							</p>
						</div>
						<div className="p-3 bg-red-100 rounded-lg">
							<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
								<path d="M12 9V13M12 17H12.01M10.29 3.86L1.82 18A2 2 0 003.64 21H20.36A2 2 0 0022.18 18L13.71 3.86A2 2 0 0010.29 3.86Z" stroke="#EF4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
							</svg>
						</div>
					</div>
				</div>

				<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
					<div className="flex items-center justify-between">
						<div>
							<p className="text-sm font-medium text-gray-600">System Updates</p>
							<p className="text-2xl font-semibold text-blue-600 mt-1">
								{logs.filter(log => log.action?.toLowerCase() === 'update').length}
							</p>
						</div>
						<div className="p-3 bg-blue-100 rounded-lg">
							<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
								<path d="M21 15V19C21 20.1046 20.1046 21 19 21H5C3.89543 21 3 20.1046 3 19V15M17 8L12 3M12 3L7 8M12 3V15" stroke="#3B82F6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
							</svg>
						</div>
					</div>
				</div>

				<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
					<div className="flex items-center justify-between">
						<div>
							<p className="text-sm font-medium text-gray-600">Recent Activity</p>
							<p className="text-2xl font-semibold text-purple-600 mt-1">
								{logs.filter(log => {
									const date = new Date(log.action_time);
									const now = new Date();
									const diffHours = Math.floor((now - date) / 3600000);
									return diffHours < 24;
								}).length}
							</p>
						</div>
						<div className="p-3 bg-purple-100 rounded-lg">
							<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
								<path d="M12 6V12L16 14M22 12C22 17.5228 17.5228 22 12 22C6.47715 22 2 17.5228 2 12C2 6.47715 6.47715 2 12 2C17.5228 2 22 6.47715 22 12Z" stroke="#9333EA" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
							</svg>
						</div>
					</div>
				</div>
			</div>

			{/* Filters and Search */}
			<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
				<div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
					<div>
						<h2 className="text-lg font-semibold text-gray-900">Framework Activity Log</h2>
						<p className="text-sm text-gray-600 mt-1">System-level changes and platform updates</p>
					</div>
					<div className="flex flex-wrap gap-3">
						{/* Search */}
						<div className="relative">
							<input
								type="text"
								placeholder="Search logs..."
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

						{/* Action Filter */}
						<select
							value={filters.action}
							onChange={(e) => setFilters({ ...filters, action: e.target.value })}
							className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
						>
							<option value="">All Actions</option>
							<option value="create">Create</option>
							<option value="update">Update</option>
							<option value="delete">Delete</option>
						</select>

						{/* Severity Filter */}
						<div className="flex gap-2">
							{['high', 'medium', 'low'].map(severity => {
								const badge = getSeverityBadge(severity);
								return (
									<button
										key={severity}
										onClick={() => {
											// Toggle severity filter
											setFilters(prev => ({
												...prev,
												severity: prev.severity === severity ? '' : severity
											}));
										}}
										className={`inline-flex items-center gap-1 px-3 py-1.5 text-sm rounded-lg transition-colors ${
											filters.severity === severity
												? badge.color
												: 'bg-gray-100 text-gray-700 hover:bg-gray-200'
										}`}
									>
										<span>{badge.icon}</span>
										<span>{badge.label}</span>
									</button>
								);
							})}
						</div>
					</div>
				</div>
			</div>

			{/* Logs List */}
			<div className="space-y-4">
				{loading ? (
					<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12">
						<div className="flex items-center justify-center">
							<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
						</div>
					</div>
				) : logs.length === 0 ? (
					<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
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
								d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
							/>
						</svg>
						<p className="mt-2 text-sm text-gray-500">No framework logs found</p>
					</div>
				) : (
					<>
						{logs.map((log) => {
							const isExpanded = expandedLogs[log.id];
							const severity = getLogSeverity(log);
							const severityBadge = getSeverityBadge(severity);
							const changes = formatFieldChanges(log.field_changes);
							
							return (
								<div
									key={log.id}
									className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden transition-all hover:shadow-md"
								>
									<div
										className="p-6 cursor-pointer"
										onClick={() => toggleLogExpansion(log.id)}
									>
										<div className="flex items-start justify-between">
											<div className="flex-1">
												{/* Header */}
												<div className="flex items-center gap-3 mb-2">
													<span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${severityBadge.color}`}>
														{severityBadge.icon} {severityBadge.label}
													</span>
													<span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${getActionBadgeColor(log.action)}`}>
														{log.action}
													</span>
													<span className="text-sm text-muted-foreground">
														{formatTimestamp(log.action_time)}
													</span>
												</div>

												{/* Content */}
												<div className="flex items-center gap-2 text-gray-900">
													<span className="font-medium">{log.actor || 'System'}</span>
													<span className="text-gray-600">{log.action?.toLowerCase()}d</span>
													<span className="font-mono text-sm bg-gray-100 px-2 py-0.5 rounded">
														{log.table}
													</span>
													{log.object_repr && (
														<>
															<span className="text-gray-600">•</span>
															<span className="text-gray-700">{log.object_repr}</span>
														</>
													)}
												</div>

												{/* Module info */}
												{log.module && (
													<div className="mt-2 flex items-center gap-2 text-sm text-gray-600">
														<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" className="opacity-50">
															<path d="M8 1L2 4V8L8 11L14 8V4L8 1Z"/>
														</svg>
														<span>Module: {log.module}</span>
													</div>
												)}

												{/* Preview of changes */}
												{changes.length > 0 && !isExpanded && (
													<div className="mt-2 text-sm text-gray-600">
														Modified {changes.length} field{changes.length > 1 ? 's' : ''}
													</div>
												)}
											</div>

											{/* Expand Icon */}
											<svg
												className={`w-5 h-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
												fill="none"
												viewBox="0 0 24 24"
												stroke="currentColor"
											>
												<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
											</svg>
										</div>
									</div>

									{/* Expanded Details */}
									{isExpanded && (
										<div className="border-t border-gray-200 bg-gray-50 p-6">
											<div className="space-y-4">
												{/* Metadata */}
												<div className="grid grid-cols-2 gap-4 text-sm">
													<div>
														<span className="text-gray-600">Object ID:</span>
														<span className="ml-2 font-mono text-gray-900">{log.object_id}</span>
													</div>
													<div>
														<span className="text-gray-600">Timestamp:</span>
														<span className="ml-2 text-gray-900">
															{new Date(log.action_time).toLocaleString()}
														</span>
													</div>
													{log.module && (
														<div>
															<span className="text-gray-600">Module:</span>
															<span className="ml-2 text-gray-900">{log.module}</span>
														</div>
													)}
													{log.actor_role && (
														<div>
															<span className="text-gray-600">Actor Role:</span>
															<span className="ml-2 text-gray-900">{log.actor_role}</span>
														</div>
													)}
												</div>

												{/* Field Changes */}
												{changes.length > 0 && (
													<div>
														<h4 className="text-sm font-medium text-gray-900 mb-3">Configuration Changes</h4>
														<div className="space-y-2">
															{changes.map((change, idx) => (
																<div key={idx} className="bg-white rounded-lg border border-gray-200 p-3">
																	<div className="font-mono text-sm text-gray-700 mb-2">
																		{change.field}
																	</div>
																	<div className="grid grid-cols-2 gap-4 text-sm">
																		<div>
																			<span className="text-gray-600 block mb-1">Previous Value:</span>
																			<div className="bg-red-50 rounded p-2 font-mono text-xs text-red-700 break-all">
																				{change.oldValue || 'null'}
																			</div>
																		</div>
																		<div>
																			<span className="text-gray-600 block mb-1">New Value:</span>
																			<div className="bg-green-50 rounded p-2 font-mono text-xs text-green-700 break-all">
																				{change.newValue || 'null'}
																			</div>
																		</div>
																	</div>
																</div>
															))}
														</div>
													</div>
												)}

												{/* Additional Details */}
												{log.description && (
													<div>
														<h4 className="text-sm font-medium text-gray-900 mb-2">Description</h4>
														<p className="text-sm text-gray-700 bg-white rounded-lg border border-gray-200 p-3">
															{log.description}
														</p>
													</div>
												)}
											</div>
										</div>
									)}
								</div>
							);
						})}
					</>
				)}
			</div>

			{/* Pagination */}
			{totalPages > 1 && (
				<div className="bg-white rounded-lg shadow-sm border border-gray-200 px-6 py-3 flex items-center justify-between">
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
						Showing {logs.length} of {totalPages * pageSize} logs
					</span>
				</div>
			)}
		</div>
	);
}