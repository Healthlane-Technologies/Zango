import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import useApi from '../../../../hooks/useApi';

export default function AccessLogs() {
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
		attempt_type: '',
		is_login_successful: '',
		role: '',
		date_range: null
	});
	const [dropdownOptions, setDropdownOptions] = useState({});
	const [totalRecords, setTotalRecords] = useState(0);
	const [totalFailedAttempts, setTotalFailedAttempts] = useState(0);

	// Fetch logs
	const fetchLogs = async () => {
		setLoading(true);
		try {
			const queryParams = new URLSearchParams({
				page: page.toString(),
				page_size: pageSize.toString(),
				include_dropdown_options: 'true',
				search: searchTerm,
			});

			// Add filters
			if (filters.attempt_type) {
				queryParams.append('search_attempt_type', filters.attempt_type);
			}
			if (filters.is_login_successful !== '') {
				queryParams.append('search_is_login_successful', filters.is_login_successful === 'true' ? 'successful' : 'failed');
			}
			if (filters.role) {
				queryParams.append('search_role', filters.role);
			}
			if (filters.date_range && filters.date_range.start && filters.date_range.end) {
				queryParams.append('search_attempt_time', JSON.stringify({
					start: filters.date_range.start,
					end: filters.date_range.end
				}));
			}

			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/access-logs/?${queryParams.toString()}`,
				type: 'GET',
				loader: false,
			});

			if (success && response?.access_logs) {
				setLogs(response.access_logs.records || []);
				setTotalPages(response.access_logs.total_pages || 1);
				setTotalRecords(response.access_logs.total_records || 0);
				setTotalFailedAttempts(response.total_failed_attempts || 0);
				if (response.dropdown_options) {
					setDropdownOptions(response.dropdown_options);
				}
			}
		} catch (error) {
			console.error('Error fetching access logs:', error);
		} finally {
			setLoading(false);
		}
	};

	useEffect(() => {
		fetchLogs();
	}, [appId, page, searchTerm, filters]);

	// Reset page to 1 when search term or filters change
	useEffect(() => {
		setPage(1);
	}, [searchTerm, filters]);

	// Toggle log expansion
	const toggleLogExpansion = (logId) => {
		setExpandedLogs(prev => ({
			...prev,
			[logId]: !prev[logId]
		}));
	};

	// Reset all filters
	const resetFilters = () => {
		setFilters({
			attempt_type: '',
			is_login_successful: '',
			role: '',
			date_range: null
		});
		setSearchTerm('');
		setPage(1);
	};

	return (
		<div className="space-y-4">
			{/* Header with Stats */}
			<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
				<div className="card p-6">
					<div className="flex items-center justify-between">
						<div>
							<p className="text-sm font-medium text-muted-foreground">Total Access Logs</p>
							<p className="text-2xl font-medium tracking-tight mt-1">
								{totalRecords}
							</p>
						</div>
						<div className="p-3 bg-blue-500/10 rounded-md">
							<svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-blue-600 dark:text-blue-400">
								<path d="M15 3H21V9M21 3L10 14M21 14V21H15M14 10L3 21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
							</svg>
						</div>
					</div>
				</div>

				<div className="card p-6">
					<div className="flex items-center justify-between">
						<div>
							<p className="text-sm font-medium text-muted-foreground">Failed Attempts</p>
							<p className="text-2xl font-medium tracking-tight text-red-600 dark:text-red-400 mt-1">
								{totalFailedAttempts}
							</p>
						</div>
						<div className="p-3 bg-red-500/10 rounded-md">
							<svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-red-600 dark:text-red-400">
								<circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
								<path d="M15 9L9 15M9 9L15 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
							</svg>
						</div>
					</div>
				</div>
			</div>

			{/* Filters and Search */}
			<div className="card p-6">
				<div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
					<div>
						<h2 className="text-lg font-medium tracking-tight">Access Log Activity</h2>
						<p className="text-sm text-muted-foreground mt-1">Track user authentication and access events</p>
					</div>
					<div className="flex flex-wrap gap-3">
						{/* Search */}
						<div className="relative">
							<input
								type="text"
								placeholder="Search by user, IP, or user agent..."
								value={searchTerm}
								onChange={(e) => {
									setSearchTerm(e.target.value);
									setPage(1);
								}}
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

						{/* Attempt Type Filter */}
						<select
							value={filters.attempt_type}
							onChange={(e) => {
								setFilters({ ...filters, attempt_type: e.target.value });
								setPage(1);
							}}
							className="h-9 rounded-md border bg-background px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
						>
							<option value="">All Types</option>
							<option value="login">Login</option>
							<option value="logout">Logout</option>
							<option value="switch_role">Switch Role</option>
						</select>

						{/* Success Filter */}
						<select
							value={filters.is_login_successful}
							onChange={(e) => {
								setFilters({ ...filters, is_login_successful: e.target.value });
								setPage(1);
							}}
							className="h-9 rounded-md border bg-background px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
						>
							<option value="">All Status</option>
							<option value="true">Successful</option>
							<option value="false">Failed</option>
						</select>

						{/* Role Filter */}
						<select
							value={filters.role}
							onChange={(e) => {
								setFilters({ ...filters, role: e.target.value });
								setPage(1);
							}}
							className="h-9 rounded-md border bg-background px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
						>
							<option value="">All Roles</option>
							{dropdownOptions.role?.map((role) => (
								<option key={role.id} value={role.id}>
									{role.label}
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
							className="h-9 rounded-md border bg-background px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
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
							className="h-9 rounded-md border bg-background px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
							placeholder="End Date"
						/>

						{/* Clear Filters Button */}
						{(filters.attempt_type || filters.is_login_successful || filters.role || filters.date_range?.start || filters.date_range?.end || searchTerm) && (
							<button
								onClick={resetFilters}
								className="h-9 px-3 py-1 text-sm bg-muted hover:bg-muted/80 rounded-md transition-colors inline-flex items-center gap-2"
							>
								<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
									<path d="M3 6h18M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6m3 0V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
									<line x1="10" y1="11" x2="10" y2="17"/>
									<line x1="14" y1="11" x2="14" y2="17"/>
								</svg>
								Clear Filters
							</button>
						)}
					</div>
				</div>
			</div>

			{/* Logs List */}
			<div className="space-y-4">
				{loading ? (
					<div className="card p-12">
						<div className="flex items-center justify-center">
							<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
						</div>
					</div>
				) : logs.length === 0 ? (
					<div className="card p-12 text-center">
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
						<p className="mt-2 text-sm text-muted-foreground">No access logs found</p>
					</div>
				) : (
					<>
						{logs.map((log) => {
							const isExpanded = expandedLogs[log.id];

							return (
								<div
									key={log.id}
									className="card overflow-hidden transition-all hover:shadow-md"
								>
									<div
										className="p-6 cursor-pointer"
										onClick={() => toggleLogExpansion(log.id)}
									>
										<div className="flex items-center justify-between">
											<div className="flex items-center gap-4">
												{/* User Avatar */}
												<div className="w-12 h-12 bg-gradient-to-br from-primary to-primary/60 rounded-full flex items-center justify-center text-primary-foreground font-semibold">
													{log.user ? log.user.charAt(0).toUpperCase() : 'U'}
												</div>

												{/* Log Info */}
												<div className="flex-1">
													<div className="flex items-center gap-3">
														<h3 className="font-medium">
															{log.user || log.username || 'Unknown User'}
														</h3>
														{log.is_login_successful ? (
															<span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20">
																<span className="w-1.5 h-1.5 bg-emerald-600 rounded-full"></span>
																Successful
															</span>
														) : (
															<span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-500/10 text-red-700 dark:text-red-400 border border-red-500/20">
																<span className="w-1.5 h-1.5 bg-red-600 rounded-full"></span>
																Failed
															</span>
														)}
														<span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-muted text-muted-foreground border border-border">
															{log.attempt_type}
														</span>
													</div>
													<div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
														<span className="flex items-center gap-1">
															<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" className="opacity-50">
																<path d="M8 3.5a.5.5 0 00-1 0V9a.5.5 0 00.252.434l3.5 2a.5.5 0 00.496-.868L8 8.71V3.5z"/>
																<path d="M8 16A8 8 0 108 0a8 8 0 000 16zm7-8A7 7 0 111 8a7 7 0 0114 0z"/>
															</svg>
															{new Date(log.attempt_time).toLocaleString()}
														</span>
														<span className="flex items-center gap-1">
															<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" className="opacity-50">
																<path d="M12.166 8.94c-.524 1.062-1.234 2.12-1.96 3.07A31.493 31.493 0 018 14.58a31.481 31.481 0 01-2.206-2.57c-.726-.95-1.436-2.008-1.96-3.07C3.304 7.867 3 6.862 3 6a5 5 0 0110 0c0 .862-.305 1.867-.834 2.94zM8 16s6-5.686 6-10A6 6 0 002 6c0 4.314 6 10 6 10z"/>
																<path d="M8 8a2 2 0 110-4 2 2 0 010 4zm0 1a3 3 0 100-6 3 3 0 000 6z"/>
															</svg>
															{log.ip_address}
														</span>
														{log.role && (
															<span className="flex items-center gap-1">
																<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" className="opacity-50">
																	<path d="M8 4.754a3.246 3.246 0 100 6.492 3.246 3.246 0 000-6.492zM5.754 8a2.246 2.246 0 114.492 0 2.246 2.246 0 01-4.492 0z"/>
																	<path d="M9.796 1.343c-.527-1.79-3.065-1.79-3.592 0l-.094.319a.873.873 0 01-1.255.52l-.292-.16c-1.64-.892-3.433.902-2.54 2.541l.159.292a.873.873 0 01-.52 1.255l-.319.094c-1.79.527-1.79 3.065 0 3.592l.319.094a.873.873 0 01.52 1.255l-.16.292c-.892 1.64.901 3.434 2.541 2.54l.292-.159a.873.873 0 011.255.52l.094.319c.527 1.79 3.065 1.79 3.592 0l.094-.319a.873.873 0 011.255-.52l.292.16c1.64.892 3.434-.902 2.54-2.541l-.159-.292a.873.873 0 01.52-1.255l.319-.094c1.79-.527 1.79-3.065 0-3.592l-.319-.094a.873.873 0 01-.52-1.255l.16-.292c.892-1.64-.902-3.433-2.541-2.54l-.292.159a.873.873 0 01-1.255-.52l-.094-.319zm-2.633.283c.246-.835 1.428-.835 1.674 0l.094.319a1.873 1.873 0 002.693 1.115l.291-.16c.764-.415 1.6.42 1.184 1.185l-.159.292a1.873 1.873 0 001.116 2.692l.318.094c.835.246.835 1.428 0 1.674l-.319.094a1.873 1.873 0 00-1.115 2.693l.16.291c.415.764-.42 1.6-1.185 1.184l-.291-.159a1.873 1.873 0 00-2.693 1.116l-.094.318c-.246.835-1.428.835-1.674 0l-.094-.319a1.873 1.873 0 00-2.692-1.115l-.292.16c-.764.415-1.6-.42-1.184-1.185l.159-.291A1.873 1.873 0 001.945 8.93l-.319-.094c-.835-.246-.835-1.428 0-1.674l.319-.094A1.873 1.873 0 003.06 4.377l-.16-.292c-.415-.764.42-1.6 1.185-1.184l.292.159a1.873 1.873 0 002.692-1.115l.094-.319z"/>
																</svg>
																{log.role}
															</span>
														)}
													</div>
													{/* User Agent */}
													{log.user_agent && (
														<div className="mt-2 text-xs text-muted-foreground font-mono">
															{log.user_agent}
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
											<div className="grid grid-cols-1 md:grid-cols-2 gap-6">
												<div>
													<h4 className="text-sm font-medium mb-3">Session Information</h4>
													<div className="space-y-2">
														<div className="flex text-sm">
															<span className="text-muted-foreground w-[160px] flex-shrink-0">ID:</span>
															<span className="font-mono">{log.id}</span>
														</div>
														<div className="flex text-sm">
															<span className="text-muted-foreground w-[160px] flex-shrink-0">User:</span>
															<span>{log.user}</span>
														</div>
														<div className="flex text-sm">
															<span className="text-muted-foreground w-[160px] flex-shrink-0">Username:</span>
															<span>{log.username}</span>
														</div>
														<div className="flex text-sm">
															<span className="text-muted-foreground w-[160px] flex-shrink-0">Attempt Time:</span>
															<span>{log.attempt_time}</span>
														</div>
														<div className="flex text-sm">
															<span className="text-muted-foreground w-[160px] flex-shrink-0">Attempt Type:</span>
															<span>{log.attempt_type}</span>
														</div>
														<div className="flex text-sm">
															<span className="text-muted-foreground w-[160px] flex-shrink-0">Login Successful:</span>
															<span>{log.is_login_successful ? 'Yes' : 'No'}</span>
														</div>
														<div className="flex text-sm">
															<span className="text-muted-foreground w-[160px] flex-shrink-0">Role:</span>
															<span>{log.role}</span>
														</div>
														<div className="flex text-sm">
															<span className="text-muted-foreground w-[160px] flex-shrink-0">Session Expired At:</span>
															<span>{log.session_expired_at}</span>
														</div>
													</div>
												</div>

												<div>
													<h4 className="text-sm font-medium mb-3">Device Information</h4>
													<div className="space-y-2">
														<div className="flex text-sm">
															<span className="text-muted-foreground w-[100px] flex-shrink-0">IP Address:</span>
															<span className="font-mono">{log.ip_address}</span>
														</div>
														<div className="text-sm">
															<span className="text-muted-foreground">User Agent:</span>
															<p className="mt-1 text-xs font-mono text-muted-foreground break-all">
																{log.user_agent}
															</p>
														</div>
													</div>
												</div>
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
				<div className="card px-6 py-3 flex items-center justify-between">
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