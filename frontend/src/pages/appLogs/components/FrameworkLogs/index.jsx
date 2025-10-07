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
	const [totalRecords, setTotalRecords] = useState(0);
	const [pageSize, setPageSize] = useState(20);
	const [filters, setFilters] = useState({
		action: '',
		object_type: '',
		actor: '',
		date_range: null
	});
	const [dropdownOptions, setDropdownOptions] = useState({});
	const [totalStats, setTotalStats] = useState({
		total_changes: 0,
		total_created: 0,
		total_updated: 0,
		total_deleted: 0
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
				model_type: 'core_models'
			});

			// Add filters
			if (filters.action) {
				queryParams.append('search_action', filters.action);
			}
			if (filters.object_type) {
				queryParams.append('search_object_type', filters.object_type);
			}
			if (filters.actor) {
				queryParams.append('search_actor', filters.actor);
			}
			if (filters.date_range && filters.date_range.start && filters.date_range.end) {
				queryParams.append('search_timestamp', JSON.stringify({
					start: filters.date_range.start,
					end: filters.date_range.end
				}));
			}

			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/auditlog/?${queryParams.toString()}`,
				type: 'GET',
				loader: false,
			});

			if (success && response?.audit_logs) {
				setLogs(response.audit_logs.records || []);
				setTotalPages(response.audit_logs.total_pages || 1);
				setTotalRecords(response.audit_logs.total_records || 0);
				if (response.dropdown_options) {
					setDropdownOptions(response.dropdown_options);
				}
				if (response.total_stats) {
					setTotalStats(response.total_stats);
				}
			}
		} catch (error) {
			console.error('Error fetching framework audit logs:', error);
		} finally {
			setLoading(false);
		}
	};

	useEffect(() => {
		setPage(1); // Reset to page 1 when pageSize changes
	}, [pageSize]);

	useEffect(() => {
		fetchLogs();
	}, [appId, page, pageSize, searchTerm, filters]);

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
		if (!changes || (typeof changes === 'object' && Object.keys(changes).length === 0)) return [];
		
		try {
			const parsed = typeof changes === 'string' ? JSON.parse(changes) : changes;
			if (!parsed || typeof parsed !== 'object') return [];
			
			return Object.entries(parsed).map(([field, values]) => ({
				field,
				oldValue: Array.isArray(values) ? values[0] : values,
				newValue: Array.isArray(values) ? values[1] : values
			}));
		} catch (error) {
			console.warn('Error parsing field changes:', error);
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
				const jsonString = JSON.stringify(value, null, 2);
				// Truncate very long JSON
				return jsonString.length > 500 ? jsonString.substring(0, 500) + '...' : jsonString;
			} catch (error) {
				return String(value);
			}
		}
		
		if (typeof value === 'string') {
			if (value.length === 0) {
				return '(empty string)';
			}
			// Truncate very long strings but preserve structure for HTML/code
			if (value.length > 1000) {
				return value.substring(0, 1000) + '...';
			}
		}
		
		return String(value);
	};

	// Reset all filters
	const resetFilters = () => {
		setFilters({
			action: '',
			object_type: '',
			actor: '',
			date_range: null
		});
		setSearchTerm('');
		setPage(1);
	};

	return (
		<div className="space-y-6">
			{/* Stats Overview */}
			<div className="grid grid-cols-1 md:grid-cols-4 gap-6">
				<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
					<div className="flex items-center justify-between">
						<div>
							<p className="text-sm font-medium text-gray-600">Total Changes</p>
							<p className="text-2xl font-semibold text-gray-900 mt-1">{totalStats.total_changes}</p>
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
							<p className="text-sm font-medium text-gray-600">Created</p>
							<p className="text-2xl font-semibold text-emerald-600 mt-1">
								{totalStats.total_created}
							</p>
						</div>
						<div className="p-3 bg-emerald-100 rounded-lg">
							<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
								<circle cx="12" cy="12" r="10" stroke="#10B981" strokeWidth="2"/>
								<path d="M12 8V16M8 12H16" stroke="#10B981" strokeWidth="2" strokeLinecap="round"/>
							</svg>
						</div>
					</div>
				</div>

				<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
					<div className="flex items-center justify-between">
						<div>
							<p className="text-sm font-medium text-gray-600">Updated</p>
							<p className="text-2xl font-semibold text-blue-600 mt-1">
								{totalStats.total_updated}
							</p>
						</div>
						<div className="p-3 bg-blue-100 rounded-lg">
							<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
								<path d="M11 4H4C2.89543 4 2 4.89543 2 6V20C2 21.1046 2.89543 22 4 22H18C19.1046 22 20 21.1046 20 20V13" stroke="#3B82F6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
								<path d="M18.5 2.50001C19.3284 1.67158 20.6716 1.67158 21.5 2.50001C22.3284 3.32844 22.3284 4.67158 21.5 5.50001L12 15L8 16L9 12L18.5 2.50001Z" stroke="#3B82F6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
							</svg>
						</div>
					</div>
				</div>

				<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
					<div className="flex items-center justify-between">
						<div>
							<p className="text-sm font-medium text-gray-600">Deleted</p>
							<p className="text-2xl font-semibold text-red-600 mt-1">
								{totalStats.total_deleted}
							</p>
						</div>
						<div className="p-3 bg-red-100 rounded-lg">
							<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
								<path d="M3 6H21M8 6V4C8 2.89543 8.89543 2 10 2H14C15.1046 2 16 2.89543 16 4V6M19 6V20C19 21.1046 18.1046 22 17 22H7C5.89543 22 5 21.1046 5 20V6H19Z" stroke="#EF4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
							</svg>
						</div>
					</div>
				</div>
			</div>

			{/* Filters and Search */}
			<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
				<div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
					<div>
						<h2 className="text-lg font-semibold text-gray-900">Framework Audit Log</h2>
						<p className="text-sm text-gray-600 mt-1">System-level changes and platform updates</p>
					</div>
					<div className="flex flex-wrap gap-3">
						{/* Search */}
						<div className="relative">
							<input
								type="text"
								placeholder="Search framework logs by ID, actor, changes..."
								value={searchTerm}
								onChange={(e) => setSearchTerm(e.target.value)}
								className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent w-full sm:w-80"
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
							{dropdownOptions.action?.map((action) => (
								<option key={action.id} value={action.id}>
									{action.label}
								</option>
							))}
						</select>

						{/* Object Type Filter */}
						<select
							value={filters.object_type}
							onChange={(e) => setFilters({ ...filters, object_type: e.target.value })}
							className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
						>
							<option value="">All Models</option>
							{dropdownOptions.object_type?.map((type) => (
								<option key={type.id} value={type.id}>
									{type.label}
								</option>
							))}
						</select>

						{/* Date Range Filter */}
						<input
							type="date"
							value={filters.date_range?.start || ''}
							onChange={(e) => setFilters({ 
								...filters, 
								date_range: { 
									...filters.date_range, 
									start: e.target.value 
								} 
							})}
							className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
							placeholder="Start Date"
						/>
						<input
							type="date"
							value={filters.date_range?.end || ''}
							onChange={(e) => setFilters({ 
								...filters, 
								date_range: { 
									...filters.date_range, 
									end: e.target.value 
								} 
							})}
							className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
							placeholder="End Date"
						/>

						{/* Reset Filters Button */}
						{(filters.action || filters.object_type || filters.date_range?.start || filters.date_range?.end || searchTerm) && (
							<button
								onClick={resetFilters}
								className="px-4 py-2 text-sm bg-gray-100 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-transparent"
							>
								Clear Filters
							</button>
						)}
					</div>
				</div>
			</div>

			{/* Active Filters Indicator */}
			{(filters.action || filters.object_type || filters.date_range?.start || filters.date_range?.end) && (
				<div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
					<div className="flex items-center justify-between">
						<div className="flex items-center gap-2">
							<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" className="text-blue-600">
								<path d="M6 10.5a.5.5 0 01.5-.5h3a.5.5 0 010 1h-3a.5.5 0 01-.5-.5zM2 6a2 2 0 012-2h8a2 2 0 012 2v1a2 2 0 01-.586 1.414L11 10.828V14.5a.5.5 0 01-.5.5h-5a.5.5 0 01-.5-.5v-3.672L2.586 8.414A2 2 0 012 7V6z"/>
							</svg>
							<span className="text-sm font-medium text-blue-800">Active Filters:</span>
							<div className="flex flex-wrap gap-1">
								{filters.action && (
									<span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800">
										Action: {dropdownOptions.action?.find(a => a.id === filters.action)?.label || filters.action}
									</span>
								)}
								{filters.object_type && (
									<span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800">
										Model: {dropdownOptions.object_type?.find(t => t.id === filters.object_type)?.label || filters.object_type}
									</span>
								)}
								{filters.date_range?.start && (
									<span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800">
										From: {filters.date_range.start}
									</span>
								)}
								{filters.date_range?.end && (
									<span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800">
										To: {filters.date_range.end}
									</span>
								)}
							</div>
						</div>
						<button
							onClick={resetFilters}
							className="text-blue-600 hover:text-blue-800 text-sm font-medium"
						>
							Clear All
						</button>
					</div>
				</div>
			)}

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
						<p className="mt-2 text-sm text-gray-500">No framework audit logs found</p>
					</div>
				) : (
					<>
						{logs.map((log) => {
							const isExpanded = expandedLogs[log.id];
							const changes = formatFieldChanges(log.changes);
							
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
													<span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border ${getActionBadgeColor(log.action)}`}>
														{getActionIcon(log.action)}
														{log.action}
													</span>
													<span className="text-sm text-muted-foreground">
														{formatTimestamp(log.timestamp)}
													</span>
												</div>

												{/* Content */}
												<div className="flex items-center gap-2 text-gray-900">
													<span className="font-medium">{log.actor || (log.actor_type ? `${log.actor_type}` : 'System')}</span>
													<span className="text-gray-600">{log.action?.toLowerCase()}d</span>
													<span className="font-mono text-sm bg-gray-100 px-2 py-0.5 rounded">
														{log.object_type}
													</span>
													{log.object_uuid && (
														<>
															<span className="text-gray-600">•</span>
															<span className="text-gray-700 font-mono text-xs">{log.object_uuid.length > 8 ? log.object_uuid.substring(0, 8) + '...' : log.object_uuid}</span>
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
												<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
													<div>
														<span className="text-gray-600">Object Type:</span>
														<span className="ml-2 inline-flex items-center gap-1 px-2 py-0.5 bg-primary/10 text-primary rounded text-xs font-medium">
															{log.object_type}
														</span>
													</div>
													<div>
														<span className="text-gray-600">Object ID:</span>
														<span className="ml-2 font-mono text-gray-900">{log.object_id}</span>
													</div>
													{log.object_uuid && (
														<div>
															<span className="text-gray-600">Object UUID:</span>
															<span className="ml-2 font-mono text-gray-900 text-xs">{log.object_uuid}</span>
														</div>
													)}
													<div>
														<span className="text-gray-600">Timestamp:</span>
														<span className="ml-2 text-gray-900">
															{new Date(log.timestamp).toLocaleString()}
														</span>
													</div>
													{log.module && (
														<div>
															<span className="text-gray-600">Module:</span>
															<span className="ml-2 text-gray-900">{log.module}</span>
														</div>
													)}
													{log.actor_type && (
														<div>
															<span className="text-gray-600">Actor Type:</span>
															<span className="ml-2 text-gray-900">{log.actor_type}</span>
														</div>
													)}
												</div>

												{/* Field Changes */}
												{changes.length > 0 && (
													<div>
														<h4 className="text-sm font-medium text-gray-900 mb-3 flex items-center gap-2">
															<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" className="text-gray-600">
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
																					<span className="text-sm font-medium text-gray-600">Previous Value</span>
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
																					<span className="text-sm font-medium text-gray-600">New Value</span>
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
			{totalRecords > 0 && (
				<div className="bg-white rounded-lg shadow-sm border border-gray-200 px-6 py-3">
					<div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
						{/* Page Navigation */}
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

						{/* Page Info and Size Selector */}
						<div className="flex items-center gap-4">
							<span className="text-sm text-gray-600">
								Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, totalRecords)} of {totalRecords} logs
							</span>
							<div className="flex items-center gap-2">
								<label htmlFor="frameworkPageSize" className="text-sm text-gray-600">
									Rows:
								</label>
								<select
									id="frameworkPageSize"
									value={pageSize}
									onChange={(e) => setPageSize(Number(e.target.value))}
									className="px-3 py-1 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
								>
									<option value={10}>10</option>
									<option value={20}>20</option>
									<option value={50}>50</option>
									<option value={100}>100</option>
								</select>
							</div>
						</div>
					</div>
				</div>
			)}
		</div>
	);
}