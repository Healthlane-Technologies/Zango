import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import useApi from '../../../../hooks/useApi';

export default function ApplicationLogs() {
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
				model_type: 'dynamic_models'
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
			console.error('Error fetching application logs:', error);
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
				return 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/20';
			case 'update':
			case 'edit':
				return 'bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-500/20';
			case 'delete':
			case 'remove':
				return 'bg-red-500/10 text-red-700 dark:text-red-400 border-red-500/20';
			default:
				return 'bg-muted text-muted-foreground border-border';
		}
	};

	// Get action icon
	const getActionIcon = (action) => {
		switch (action?.toLowerCase()) {
			case 'create':
			case 'insert':
				return (
					<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
						<path d="M8 4a.5.5 0 01.5.5v3h3a.5.5 0 010 1h-3v3a.5.5 0 01-1 0v-3h-3a.5.5 0 010-1h3v-3A.5.5 0 018 4z"/>
						<path d="M8 15A7 7 0 108 1a7 7 0 000 14z"/>
					</svg>
				);
			case 'update':
			case 'edit':
				return (
					<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
						<path d="M15.502 1.94a.5.5 0 010 .706L14.459 3.69l-2-2L13.502.646a.5.5 0 01.707 0l1.293 1.293zm-1.75 2.456l-2-2L4.939 9.21a.5.5 0 00-.121.196l-.805 2.414a.25.25 0 00.316.316l2.414-.805a.5.5 0 00.196-.12l6.813-6.814z"/>
					</svg>
				);
			case 'delete':
			case 'remove':
				return (
					<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
						<path d="M5.5 5.5A.5.5 0 016 6v6a.5.5 0 01-1 0V6a.5.5 0 01.5-.5zm2.5 0a.5.5 0 01.5.5v6a.5.5 0 01-1 0V6a.5.5 0 01.5-.5zm3 .5a.5.5 0 00-1 0v6a.5.5 0 001 0V6z"/>
						<path d="M14.5 3a1 1 0 01-1 1H13v9a2 2 0 01-2 2H5a2 2 0 01-2-2V4h-.5a1 1 0 01-1-1V2a1 1 0 011-1H6a1 1 0 011-1h2a1 1 0 011 1h3.5a1 1 0 011 1v1z"/>
					</svg>
				);
			default:
				return null;
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

	// Format value for display
	const formatValue = (value) => {
		if (value === null || value === undefined) {
			return 'null';
		}
		
		if (typeof value === 'boolean') {
			return value ? 'true' : 'false';
		}
		
		if (typeof value === 'object') {
			try {
				return JSON.stringify(value, null, 2);
			} catch (error) {
				return String(value);
			}
		}
		
		if (typeof value === 'string' && value.length === 0) {
			return '(empty string)';
		}
		
		return String(value);
	};

	return (
		<div className="space-y-4">
			{/* Stats Overview */}
			<div className="grid grid-cols-1 md:grid-cols-4 gap-4">
				<div className="rounded-lg border bg-card p-6 transition-colors hover:bg-accent/5">
					<div className="flex items-center justify-between">
						<div>
							<p className="text-sm font-medium text-muted-foreground">Total Changes</p>
							<p className="text-2xl font-medium tracking-tight mt-1">{logs.length}</p>
						</div>
						<div className="p-3 bg-muted/50 rounded-md">
							<svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-muted-foreground">
								<path d="M12 2L2 7V12C2 16.5 4.23 20.68 8 21.93C11.77 20.68 14 16.5 14 12V7L12 2Z" fill="currentColor" fillOpacity="0.2"/>
								<path d="M12 2L2 7V12C2 16.5 4.23 20.68 8 21.93C11.77 20.68 14 16.5 14 12V7L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
								<path d="M18 9V15M21 12H15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
							</svg>
						</div>
					</div>
				</div>

				<div className="rounded-lg border bg-card p-6 transition-colors hover:bg-accent/5">
					<div className="flex items-center justify-between">
						<div>
							<p className="text-sm font-medium text-muted-foreground">Created</p>
							<p className="text-2xl font-medium tracking-tight text-emerald-600 dark:text-emerald-400 mt-1">
								{logs.filter(log => log.action?.toLowerCase() === 'create').length}
							</p>
						</div>
						<div className="p-3 bg-emerald-500/10 rounded-md">
							<svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-emerald-600 dark:text-emerald-400">
								<circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
								<path d="M12 8V16M8 12H16" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
							</svg>
						</div>
					</div>
				</div>

				<div className="rounded-lg border bg-card p-6 transition-colors hover:bg-accent/5">
					<div className="flex items-center justify-between">
						<div>
							<p className="text-sm font-medium text-muted-foreground">Updated</p>
							<p className="text-2xl font-medium tracking-tight text-blue-600 dark:text-blue-400 mt-1">
								{logs.filter(log => log.action?.toLowerCase() === 'update').length}
							</p>
						</div>
						<div className="p-3 bg-blue-500/10 rounded-md">
							<svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-blue-600 dark:text-blue-400">
								<path d="M11 4H4C2.89543 4 2 4.89543 2 6V20C2 21.1046 2.89543 22 4 22H18C19.1046 22 20 21.1046 20 20V13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
								<path d="M18.5 2.50001C19.3284 1.67158 20.6716 1.67158 21.5 2.50001C22.3284 3.32844 22.3284 4.67158 21.5 5.50001L12 15L8 16L9 12L18.5 2.50001Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
							</svg>
						</div>
					</div>
				</div>

				<div className="rounded-lg border bg-card p-6 transition-colors hover:bg-accent/5">
					<div className="flex items-center justify-between">
						<div>
							<p className="text-sm font-medium text-muted-foreground">Deleted</p>
							<p className="text-2xl font-medium tracking-tight text-red-600 dark:text-red-400 mt-1">
								{logs.filter(log => log.action?.toLowerCase() === 'delete').length}
							</p>
						</div>
						<div className="p-3 bg-red-500/10 rounded-md">
							<svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-red-600 dark:text-red-400">
								<path d="M3 6H21M8 6V4C8 2.89543 8.89543 2 10 2H14C15.1046 2 16 2.89543 16 4V6M19 6V20C19 21.1046 18.1046 22 17 22H7C5.89543 22 5 21.1046 5 20V6H19Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
							</svg>
						</div>
					</div>
				</div>
			</div>

			{/* Filters and Search */}
			<div className="rounded-lg border bg-card p-6">
				<div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
					<div>
						<h2 className="text-lg font-medium tracking-tight">Application Change Log</h2>
						<p className="text-sm text-muted-foreground mt-1">Track changes to your application data</p>
					</div>
					<div className="flex flex-wrap gap-2">
						{/* Search */}
						<div className="relative">
							<input
								type="text"
								placeholder="Search logs..."
								value={searchTerm}
								onChange={(e) => setSearchTerm(e.target.value)}
								className="h-9 w-full sm:w-64 rounded-md border bg-background px-3 py-1 text-sm pl-9 placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
							/>
							<svg
								className="absolute left-2.5 top-2 h-4 w-4 text-muted-foreground"
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
							className="h-9 rounded-md border bg-background px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
						>
							<option value="">All Actions</option>
							<option value="create">Create</option>
							<option value="update">Update</option>
							<option value="delete">Delete</option>
						</select>
					</div>
				</div>
			</div>

			{/* Logs Timeline */}
			<div className="space-y-4">
				{loading ? (
					<div className="rounded-lg border bg-card p-12">
						<div className="flex items-center justify-center">
							<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
						</div>
					</div>
				) : logs.length === 0 ? (
					<div className="rounded-lg border bg-card p-12 text-center">
						<svg
							className="mx-auto h-12 w-12 text-muted-foreground/50"
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
						<p className="mt-2 text-sm text-muted-foreground">No application logs found</p>
					</div>
				) : (
					<div className="relative">
						{/* Timeline line */}
						<div className="absolute left-8 top-0 bottom-0 w-0.5 bg-border"></div>

						{logs.map((log, index) => {
							const isExpanded = expandedLogs[log.id];
							const changes = formatFieldChanges(log.field_changes);
							
							return (
								<div key={log.id} className="relative">
									{/* Timeline dot */}
									<div className={`absolute left-6 w-4 h-4 rounded-full border-4 border-background ${
										log.action?.toLowerCase() === 'create' ? 'bg-emerald-500' :
										log.action?.toLowerCase() === 'update' ? 'bg-blue-500' :
										log.action?.toLowerCase() === 'delete' ? 'bg-red-500' :
										'bg-muted-foreground'
									}`}></div>

									{/* Log card */}
									<div className="ml-16 mb-4">
										<div className="rounded-lg border bg-card text-card-foreground shadow-sm transition-all hover:shadow-md">
											<div
												className="p-6 cursor-pointer"
												onClick={() => toggleLogExpansion(log.id)}
											>
												<div className="flex items-start justify-between">
													<div className="flex-1">
														{/* Header */}
														<div className="flex items-center gap-3 mb-2">
															<span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border ${getActionBadgeColor(log.action)}`}>
																{getActionIcon(log.action)}
																{log.action}
															</span>
															<span className="text-sm text-muted-foreground">
																{formatTimestamp(log.action_time)}
															</span>
														</div>

														{/* Content */}
														<div className="space-y-2">
															<div className="flex items-center gap-2 text-foreground">
																<span className="font-medium">{log.actor || 'System'}</span>
																<span className="text-muted-foreground">{log.action?.toLowerCase()}d</span>
																<span className="inline-flex items-center gap-1 px-2.5 py-0.5 bg-primary/10 text-primary rounded-md font-medium text-sm border border-primary/20">
																	<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" className="opacity-60">
																		<path d="M8.186 1.113a.5.5 0 00-.372 0L1.846 3.5l2.404.961L10.404 2l-2.218-.887zm3.564 1.426L5.596 5 8 5.961 14.154 3.5l-2.404-.961zm3.25 1.7l-6.5 2.6v7.922l6.5-2.6V4.24zM7.5 14.762V6.838L1 4.239v7.923l6.5 2.6zM7.443.184a1.5 1.5 0 011.114 0l7.129 2.852A.5.5 0 0116 3.5v8.662a1 1 0 01-.629.928l-7.185 2.874a.5.5 0 01-.372 0L.63 13.09a1 1 0 01-.63-.928V3.5a.5.5 0 01.314-.464L7.443.184z"/>
																	</svg>
																	{log.table}
																</span>
																{log.object_repr && (
																	<>
																		<span className="text-muted-foreground">•</span>
																		<span className="font-medium">{log.object_repr}</span>
																	</>
																)}
															</div>

															{/* Preview of changes with field names */}
															{changes.length > 0 && !isExpanded && (
																<div className="mt-2 flex flex-wrap gap-2">
																	<span className="text-sm text-muted-foreground">Modified:</span>
																	{changes.slice(0, 3).map((change, idx) => (
																		<span key={idx} className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/20">
																			{change.field}
																		</span>
																	))}
																	{changes.length > 3 && (
																		<span className="text-sm text-muted-foreground">+{changes.length - 3} more</span>
																	)}
																</div>
															)}
														</div>
													</div>

													{/* Expand Icon */}
													<svg
														className={`h-4 w-4 text-muted-foreground transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
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
												<div className="border-t bg-muted/50 p-6">
													<div className="space-y-4">
														{/* Metadata */}
														<div className="rounded-lg border bg-card p-4 mb-4">
															<div className="grid grid-cols-2 gap-4 text-sm">
																<div>
																	<span className="text-muted-foreground">Object Type:</span>
																	<span className="ml-2 inline-flex items-center gap-1 px-2 py-0.5 bg-primary/10 text-primary rounded text-xs font-medium">
																		{log.table}
																	</span>
																</div>
																<div>
																	<span className="text-muted-foreground">Object ID:</span>
																	<span className="ml-2 font-mono">{log.object_id}</span>
																</div>
																<div>
																	<span className="text-muted-foreground">User Role:</span>
																	<span className="ml-2">{log.actor_role || 'N/A'}</span>
																</div>
																<div>
																	<span className="text-muted-foreground">Timestamp:</span>
																	<span className="ml-2">{new Date(log.action_time).toLocaleString()}</span>
																</div>
															</div>
														</div>

														{/* Field Changes */}
														{changes.length > 0 && (
															<div>
																<h4 className="text-sm font-medium mb-3 flex items-center gap-2">
																	<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" className="text-muted-foreground">
																		<path d="M15.502 1.94a.5.5 0 010 .706L14.459 3.69l-2-2L13.502.646a.5.5 0 01.707 0l1.293 1.293zm-1.75 2.456l-2-2L4.939 9.21a.5.5 0 00-.121.196l-.805 2.414a.25.25 0 00.316.316l2.414-.805a.5.5 0 00.196-.12l6.813-6.814z"/>
																	</svg>
																	Modified Fields ({changes.length})
																</h4>
																<div className="space-y-3">
																	{changes.map((change, idx) => (
																		<div key={idx} className="rounded-lg border bg-card overflow-hidden">
																			<div className="bg-muted px-4 py-2 border-b">
																				<span className="font-medium text-sm">{change.field}</span>
																			</div>
																			<div className="p-4">
																				<div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
																					<div>
																						<div className="flex items-center gap-2 mb-2">
																							<span className="w-2 h-2 bg-red-500 rounded-full"></span>
																							<span className="text-sm font-medium text-muted-foreground">Previous Value</span>
																						</div>
																						<div className="rounded-md bg-red-500/10 border border-red-500/20 p-3">
																							<pre className="font-mono text-xs text-red-700 dark:text-red-400 whitespace-pre-wrap break-all">
																								{formatValue(change.oldValue)}
																							</pre>
																						</div>
																					</div>
																					<div>
																						<div className="flex items-center gap-2 mb-2">
																							<span className="w-2 h-2 bg-emerald-500 rounded-full"></span>
																							<span className="text-sm font-medium text-muted-foreground">New Value</span>
																						</div>
																						<div className="rounded-md bg-emerald-500/10 border border-emerald-500/20 p-3">
																							<pre className="font-mono text-xs text-emerald-700 dark:text-emerald-400 whitespace-pre-wrap break-all">
																								{formatValue(change.newValue)}
																							</pre>
																						</div>
																					</div>
																				</div>
																			</div>
																		</div>
																	))}
																</div>
															</div>
														)}
													</div>
												</div>
											)}
										</div>
									</div>
								</div>
							);
						})}
					</div>
				)}
			</div>

			{/* Pagination */}
			{totalPages > 1 && (
				<div className="rounded-lg border bg-card px-6 py-3 flex items-center justify-between">
					<div className="flex items-center gap-2">
						<button
							onClick={() => setPage(p => Math.max(1, p - 1))}
							disabled={page === 1}
							className="h-8 w-8 rounded-md border bg-background hover:bg-accent hover:text-accent-foreground disabled:opacity-50 disabled:cursor-not-allowed transition-colors inline-flex items-center justify-center"
						>
							<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
								<path d="M10 12L6 8L10 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
							</svg>
						</button>
						<span className="text-sm text-muted-foreground">
							Page {page} of {totalPages}
						</span>
						<button
							onClick={() => setPage(p => Math.min(totalPages, p + 1))}
							disabled={page === totalPages}
							className="h-8 w-8 rounded-md border bg-background hover:bg-accent hover:text-accent-foreground disabled:opacity-50 disabled:cursor-not-allowed transition-colors inline-flex items-center justify-center"
						>
							<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
								<path d="M6 12L10 8L6 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
							</svg>
						</button>
					</div>
					<span className="text-sm text-muted-foreground">
						Showing {logs.length} of {totalPages * pageSize} logs
					</span>
				</div>
			)}
		</div>
	);
}