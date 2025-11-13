import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import useApi from '../../../../hooks/useApi';

export default function AsyncTasks() {
	const { appId } = useParams();
	const triggerApi = useApi();
	const [tasks, setTasks] = useState([]);
	const [loading, setLoading] = useState(true);
	const [searchTerm, setSearchTerm] = useState('');
	const [expandedTasks, setExpandedTasks] = useState({});
	const [page, setPage] = useState(1);
	const [totalPages, setTotalPages] = useState(1);
	const [totalRecords, setTotalRecords] = useState(0);
	const [pageSize, setPageSize] = useState(10);
	const [filters, setFilters] = useState({
		is_enabled: null
	});
	const [editModalOpen, setEditModalOpen] = useState(false);
	const [editingTask, setEditingTask] = useState(null);
	const [editFormData, setEditFormData] = useState({
		is_enabled: false,
		crontab_exp: {
			minute: '*',
			hour: '*',
			day_of_week: '*',
			day_of_month: '*',
			month_of_year: '*'
		},
		kwargs: '{}'
	});
	const [historyModalOpen, setHistoryModalOpen] = useState(false);
	const [selectedTaskHistory, setSelectedTaskHistory] = useState(null);
	const [taskHistory, setTaskHistory] = useState([]);
	const [historyLoading, setHistoryLoading] = useState(false);

	// Fetch tasks
	const fetchTasks = async () => {
		setLoading(true);
		try {
			const queryParams = new URLSearchParams({
				page: page.toString(),
				page_size: pageSize.toString(),
				include_dropdown_options: 'true',
				search: searchTerm,
			});

			if (filters.is_enabled !== null) {
				queryParams.append('search_is_enabled', filters.is_enabled.toString());
			}

			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/tasks/?${queryParams.toString()}`,
				type: 'GET',
				loader: false,
			});

			if (success && response?.tasks) {
				setTasks(response.tasks.records || []);
				setTotalPages(response.tasks.total_pages || 1);
				setTotalRecords(response.tasks.total_records || 0);
			}
		} catch (error) {
			console.error('Error fetching tasks:', error);
		} finally {
			setLoading(false);
		}
	};

	useEffect(() => {
		setPage(1); // Reset to page 1 when pageSize changes
	}, [pageSize]);

	useEffect(() => {
		fetchTasks();
	}, [appId, page, pageSize, searchTerm, filters]);

	// Reset page to 1 when search term or filters change
	useEffect(() => {
		setPage(1);
	}, [searchTerm, filters]);

	// Toggle task details expansion
	const toggleTaskExpansion = (taskId) => {
		setExpandedTasks(prev => ({
			...prev,
			[taskId]: !prev[taskId]
		}));
	};

	// Get status badge
	const getStatusBadge = (isEnabled) => {
		if (isEnabled) {
			return (
				<span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
					<span className="w-1.5 h-1.5 bg-green-600 rounded-full"></span>
					Active
				</span>
			);
		}
		return (
			<span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
				<span className="w-1.5 h-1.5 bg-gray-600 rounded-full"></span>
				Inactive
			</span>
		);
	};

	// Format cron schedule
	const formatSchedule = (task) => {
		if (task.schedule) return task.schedule;
		if (task.crontab) {
			const { minute, hour, day_of_week, day_of_month, month_of_year } = task.crontab;
			return `${minute} ${hour} ${day_of_week} ${day_of_month} ${month_of_year}`;
		}
		return 'No schedule';
	};

	// Sync tasks
	const syncTasks = async () => {
		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/tasks/`,
			type: 'POST',
			loader: true,
		});

		if (success) {
			fetchTasks();
		}
	};

	// Open edit modal
	const openEditModal = (task) => {
		setEditingTask(task);
		setEditFormData({
			is_enabled: task.is_enabled,
			crontab_exp: task.crontab || {
				minute: '*',
				hour: '*',
				day_of_week: '*',
				day_of_month: '*',
				month_of_year: '*'
			},
			kwargs: task.kwargs ? JSON.stringify(task.kwargs, null, 2) : '{}'
		});
		setEditModalOpen(true);
	};

	// Close edit modal
	const closeEditModal = () => {
		setEditModalOpen(false);
		setEditingTask(null);
	};

	// Update task
	const updateTask = async () => {
		console.log("updating task");
		console.log("editFormData:", editFormData);

		if (!editingTask) return;

		console.log("No returns");

		try {
			// Parse kwargs to ensure it's valid JSON
			const parsedKwargs = JSON.parse(editFormData.kwargs);
			
			// Create FormData
			const formData = new FormData();
			formData.append('crontab_exp', JSON.stringify(editFormData.crontab_exp));
			formData.append('is_enabled', editFormData.is_enabled);
			formData.append('kwargs', JSON.stringify(parsedKwargs));
			
			console.log("FormData contents:");
			for (let [key, value] of formData.entries()) {
				console.log(key, value);
			}
			
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/tasks/${editingTask.id}/`,
				type: 'POST',
				loader: true,
				payload: formData
			});

			console.log("API response:", { response, success });

			if (success) {
				closeEditModal();
				fetchTasks();
			}
		} catch (error) {
			console.error('Invalid JSON in kwargs:', error);
			// You could add user feedback here for invalid JSON
		}
	};

	// Update crontab field
	const updateCrontabField = (field, value) => {
		setEditFormData(prev => ({
			...prev,
			crontab_exp: {
				...prev.crontab_exp,
				[field]: value
			}
		}));
	};

	// Fetch task execution history
	const fetchTaskHistory = async (taskId) => {
		setHistoryLoading(true);
		try {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/tasks/${taskId}/`,
				type: 'GET',
				loader: false,
			});

			if (success && response?.task) {
				setTaskHistory(response.task.run_history || []);
			}
		} catch (error) {
			console.error('Error fetching task history:', error);
			setTaskHistory([]);
		} finally {
			setHistoryLoading(false);
		}
	};

	// Open history modal
	const openHistoryModal = (task) => {
		setSelectedTaskHistory(task);
		setHistoryModalOpen(true);
		fetchTaskHistory(task.id);
	};

	// Close history modal
	const closeHistoryModal = () => {
		setHistoryModalOpen(false);
		setSelectedTaskHistory(null);
		setTaskHistory([]);
	};

	return (
		<div className="space-y-6">
			{/* Header */}
			<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
				<div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
					<div>
						<h2 className="text-xl font-semibold text-gray-900">Async Tasks</h2>
						<p className="text-sm text-gray-600 mt-1">
							Background tasks and scheduled jobs for your application
						</p>
					</div>
					<div className="flex flex-wrap gap-3">
						{/* Search */}
						<div className="relative">
							<input
								type="text"
								placeholder="Search tasks..."
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

						{/* Status Filter */}
						<select
							value={filters.is_enabled === null ? '' : filters.is_enabled.toString()}
							onChange={(e) => setFilters({ ...filters, is_enabled: e.target.value === '' ? null : e.target.value === 'true' })}
							className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
						>
							<option value="">All Status</option>
							<option value="true">Active</option>
							<option value="false">Inactive</option>
						</select>

						{/* Sync Button */}
						<button
							onClick={syncTasks}
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
							Sync Tasks
						</button>
					</div>
				</div>
			</div>

			{/* Tasks List */}
			<div className="bg-white rounded-lg shadow-sm border border-gray-200">
				{loading ? (
					<div className="flex items-center justify-center py-12">
						<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
					</div>
				) : tasks.length === 0 ? (
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
								d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
							/>
						</svg>
						<p className="mt-2 text-sm text-gray-500">No tasks found</p>
						<button
							onClick={syncTasks}
							className="mt-4 text-sm text-blue-600 hover:text-blue-700 font-medium"
						>
							Sync tasks from codebase
						</button>
					</div>
				) : (
					<>
						<div className="overflow-x-auto">
							<table className="min-w-full divide-y divide-gray-200">
								<thead>
									<tr>
										<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
											Task Name
										</th>
										<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
											Status
										</th>
										<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
											Schedule
										</th>
									</tr>
								</thead>
								<tbody className="bg-white divide-y divide-gray-200">
									{tasks.map((task) => {
										const isExpanded = expandedTasks[task.id];
										
										return (
											<React.Fragment key={task.id}>
												<tr className={`hover:bg-gray-50 ${isExpanded ? 'bg-gray-50' : ''}`}>
													<td className="px-6 py-4 whitespace-nowrap">
														<div className="flex items-center gap-2">
															<button
																onClick={() => toggleTaskExpansion(task.id)}
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
															<div className="flex-1">
																<div className="text-sm font-medium text-gray-900">
																	{task.name}
																</div>
																<div className="text-sm text-gray-500">
																	ID: {task.id}
																</div>
															</div>
															<div className="flex items-center gap-2">
																<button 
																	onClick={() => openEditModal(task)}
																	className="px-3 py-1 text-xs bg-blue-100 text-blue-700 hover:bg-blue-200 rounded-md transition-colors font-medium"
																>
																	Edit
																</button>
																<button 
																	onClick={() => openHistoryModal(task)}
																	className="px-3 py-1 text-xs bg-green-100 text-green-700 hover:bg-green-200 rounded-md transition-colors font-medium"
																	title="View execution history"
																>
																	<svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor" className="mr-1">
																		<path d="M8 0C3.584 0 0 3.584 0 8s3.584 8 8 8 8-3.584 8-8-3.584-8-8-8zm0 14.4c-3.536 0-6.4-2.864-6.4-6.4S4.464 1.6 8 1.6s6.4 2.864 6.4 6.4-2.864 6.4-6.4 6.4z"/>
																		<path d="M8 4.8c-.44 0-.8.36-.8.8v2.4l2.08 1.248c.368.22.848.104 1.068-.264.22-.368.104-.848-.264-1.068L8.8 7.2V5.6c0-.44-.36-.8-.8-.8z"/>
																	</svg>
																	History
																</button>
															</div>
														</div>
													</td>
													<td className="px-6 py-4 whitespace-nowrap">
														{getStatusBadge(task.is_enabled)}
													</td>
													<td className="px-6 py-4 whitespace-nowrap">
														<code className="text-xs font-mono bg-gray-100 px-2 py-1 rounded">
															{formatSchedule(task)}
														</code>
													</td>
												</tr>

												{isExpanded && (
													<tr>
														<td colSpan="3" className="p-0">
															<div className="bg-blue-50 border-t border-b border-blue-100">
																<div className="px-6 py-4">
																	<div className="space-y-4">
																		{/* Task Details */}
																		<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
																			<div>
																				<h5 className="text-sm font-medium text-gray-900 mb-2">Task Details</h5>
																				<div className="space-y-2">
																					<div className="flex items-start gap-2">
																						<span className="text-xs text-gray-500 font-medium min-w-[80px]">Created:</span>
																						<span className="text-xs text-gray-700">
																							{task.created_at}
																						</span>
																					</div>
																					<div className="flex items-start gap-2">
																						<span className="text-xs text-gray-500 font-medium min-w-[80px]">Modified:</span>
																						<span className="text-xs text-gray-700">
																							{task.modified_at}
																						</span>
																					</div>
																					{task.kwargs && (
																						<div className="flex items-start gap-2">
																							<span className="text-xs text-gray-500 font-medium min-w-[80px]">Arguments:</span>
																							<code className="text-xs bg-white px-2 py-1 rounded border border-gray-200">
																								{JSON.stringify(task.kwargs)}
																							</code>
																						</div>
																					)}
																				</div>
																			</div>

																			{/* Attached Policies */}
																			{task.attached_policies?.length > 0 && (
																				<div>
																					<h5 className="text-sm font-medium text-gray-900 mb-2">Attached Policies</h5>
																					<div className="space-y-1">
																						{task.attached_policies.map((policy, idx) => (
																							<div key={idx} className="flex items-center gap-2">
																								<svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor" className="text-gray-400">
																									<path d="M8 2L3 5V8C3 11.04 4.88 13.64 8 14C11.12 13.64 13 11.04 13 8V5L8 2Z" />
																								</svg>
																								<span className="text-xs text-gray-700">{policy.name}</span>
																							</div>
																						))}
																					</div>
																				</div>
																			)}
																		</div>

																		{/* Code Preview */}
																		{task.code && (
																			<div>
																				<h5 className="text-sm font-medium text-gray-900 mb-2">Task Code</h5>
																				<pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-xs max-w-full whitespace-pre-wrap break-words">
																					<code className="block max-w-full">{task.code}</code>
																				</pre>
																			</div>
																		)}

																		{/* Run History */}
																		{task.run_history?.length > 0 && (
																			<div>
																				<h5 className="text-sm font-medium text-gray-900 mb-2">Recent Runs</h5>
																				<div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
																					<table className="min-w-full divide-y divide-gray-200">
																						<thead className="bg-gray-50">
																							<tr>
																								<th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Started</th>
																								<th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Completed</th>
																								<th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Status</th>
																							</tr>
																						</thead>
																						<tbody className="divide-y divide-gray-200">
																							{task.run_history.slice(0, 5).map((run, idx) => (
																								<tr key={idx}>
																									<td className="px-4 py-2 text-xs text-gray-700">{run.date_started}</td>
																									<td className="px-4 py-2 text-xs text-gray-700">{run.date_done}</td>
																									<td className="px-4 py-2">
																										{run.traceback ? (
																											<span className="text-xs text-red-600 font-medium">Failed</span>
																										) : (
																											<span className="text-xs text-green-600 font-medium">Success</span>
																										)}
																									</td>
																								</tr>
																							))}
																						</tbody>
																					</table>
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
						{totalRecords > 0 && (
							<div className="bg-gray-50 px-6 py-3 border-t border-gray-200">
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
											Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, totalRecords)} of {totalRecords} tasks
										</span>
										<div className="flex items-center gap-2">
											<label htmlFor="tasksPageSize" className="text-sm text-gray-600">
												Rows:
											</label>
											<select
												id="tasksPageSize"
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
					</>
				)}
			</div>

			{/* Edit Modal */}
			{editModalOpen && (
				<div className="fixed inset-0 z-50 overflow-y-auto">
					<div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
						{/* Background overlay */}
						<div 
							className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
							onClick={closeEditModal}
						></div>

						{/* Modal panel */}
						<div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
							{/* Modal header */}
							<div className="bg-white px-6 pt-6 pb-4">
								<div className="flex items-center justify-between">
									<h3 className="text-lg font-semibold text-gray-900">
										Edit Task: {editingTask?.name}
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
							</div>

							{/* Modal body */}
							<div className="px-6 pb-4">
								<div className="space-y-4">
									{/* Enable/Disable toggle */}
									<div className="flex items-center justify-between">
										<label className="text-sm font-medium text-gray-700">
											Task Status
										</label>
										<div className="flex items-center gap-3">
											<span className={`text-sm font-medium ${
												editFormData.is_enabled ? 'text-gray-400' : 'text-gray-900'
											}`}>
												Disabled
											</span>
											<button
												onClick={() => setEditFormData(prev => ({ ...prev, is_enabled: !prev.is_enabled }))}
												className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
													editFormData.is_enabled ? 'bg-blue-600' : 'bg-gray-200'
												}`}
											>
												<span
													className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
														editFormData.is_enabled ? 'translate-x-6' : 'translate-x-1'
													}`}
												/>
											</button>
											<span className={`text-sm font-medium ${
												editFormData.is_enabled ? 'text-gray-900' : 'text-gray-400'
											}`}>
												Enabled
											</span>
										</div>
									</div>

									{/* Crontab Schedule */}
									<div>
										<label className="block text-sm font-medium text-gray-700 mb-2">
											Cron Schedule
										</label>
										<div className="grid grid-cols-5 gap-2">
											<div>
												<label className="block text-xs text-gray-500 mb-1">Minute</label>
												<input
													type="text"
													value={editFormData.crontab_exp.minute}
													onChange={(e) => updateCrontabField('minute', e.target.value)}
													className="w-full px-2 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
													placeholder="*"
												/>
											</div>
											<div>
												<label className="block text-xs text-gray-500 mb-1">Hour</label>
												<input
													type="text"
													value={editFormData.crontab_exp.hour}
													onChange={(e) => updateCrontabField('hour', e.target.value)}
													className="w-full px-2 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
													placeholder="*"
												/>
											</div>
											<div>
												<label className="block text-xs text-gray-500 mb-1">Day (Week)</label>
												<input
													type="text"
													value={editFormData.crontab_exp.day_of_week}
													onChange={(e) => updateCrontabField('day_of_week', e.target.value)}
													className="w-full px-2 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
													placeholder="*"
												/>
											</div>
											<div>
												<label className="block text-xs text-gray-500 mb-1">Day (Month)</label>
												<input
													type="text"
													value={editFormData.crontab_exp.day_of_month}
													onChange={(e) => updateCrontabField('day_of_month', e.target.value)}
													className="w-full px-2 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
													placeholder="*"
												/>
											</div>
											<div>
												<label className="block text-xs text-gray-500 mb-1">Month</label>
												<input
													type="text"
													value={editFormData.crontab_exp.month_of_year}
													onChange={(e) => updateCrontabField('month_of_year', e.target.value)}
													className="w-full px-2 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
													placeholder="*"
												/>
											</div>
										</div>
										<p className="mt-2 text-xs text-gray-500">
											Current schedule: {editFormData.crontab_exp.minute} {editFormData.crontab_exp.hour} {editFormData.crontab_exp.day_of_week} {editFormData.crontab_exp.day_of_month} {editFormData.crontab_exp.month_of_year}
										</p>
									</div>

									{/* Common presets */}
									<div>
										<label className="block text-sm font-medium text-gray-700 mb-2">
											Quick Presets
										</label>
										<div className="flex flex-wrap gap-2">
											<button
												onClick={() => setEditFormData(prev => ({
													...prev,
													crontab_exp: { minute: '0', hour: '*', day_of_week: '*', day_of_month: '*', month_of_year: '*' }
												}))}
												className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-md"
											>
												Every hour
											</button>
											<button
												onClick={() => setEditFormData(prev => ({
													...prev,
													crontab_exp: { minute: '0', hour: '0', day_of_week: '*', day_of_month: '*', month_of_year: '*' }
												}))}
												className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-md"
											>
												Daily at midnight
											</button>
											<button
												onClick={() => setEditFormData(prev => ({
													...prev,
													crontab_exp: { minute: '0', hour: '9', day_of_week: '1', day_of_month: '*', month_of_year: '*' }
												}))}
												className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-md"
											>
												Weekly on Monday 9AM
											</button>
										</div>
									</div>

									{/* Kwargs Field */}
									<div>
										<label className="block text-sm font-medium text-gray-700 mb-2">
											Task Arguments (JSON)
										</label>
										<textarea
											value={editFormData.kwargs}
											onChange={(e) => setEditFormData(prev => ({ ...prev, kwargs: e.target.value }))}
											className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm font-mono"
											rows={4}
											placeholder='{"key": "value"}'
										/>
										<p className="mt-1 text-xs text-gray-500">
											Enter valid JSON format for task arguments
										</p>
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
									onClick={updateTask}
									className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700"
								>
									Save Changes
								</button>
							</div>
						</div>
					</div>
				</div>
			)}

			{/* History Modal */}
			{historyModalOpen && selectedTaskHistory && (
				<div className="fixed inset-0 z-50 overflow-y-auto">
					<div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
						{/* Background overlay */}
						<div 
							className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
							onClick={closeHistoryModal}
						></div>

						{/* Modal panel */}
						<div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
							{/* Modal header */}
							<div className="bg-white px-6 pt-6 pb-4">
								<div className="flex items-center justify-between">
									<h3 className="text-lg font-semibold text-gray-900">
										Execution History: {selectedTaskHistory.name}
									</h3>
									<button
										onClick={closeHistoryModal}
										className="text-gray-400 hover:text-gray-500"
									>
										<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
										</svg>
									</button>
								</div>
							</div>

							{/* Modal body */}
							<div className="px-6 pb-6 max-h-96 overflow-y-auto">
								{historyLoading ? (
									<div className="flex items-center justify-center py-12">
										<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
										<span className="ml-3 text-gray-600">Loading execution history...</span>
									</div>
								) : taskHistory.length === 0 ? (
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
												d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
											/>
										</svg>
										<p className="mt-2 text-sm text-gray-500">No execution history found</p>
										<p className="text-xs text-gray-400">This task hasn't been executed yet</p>
									</div>
								) : (
									<div className="space-y-4">
										{taskHistory.map((execution, idx) => (
											<div key={execution.id || idx} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
												<div className="flex items-start justify-between mb-3">
													<div>
														<div className="flex items-center gap-2 mb-1">
															<span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
																execution.status === 'SUCCESS' 
																	? 'bg-green-100 text-green-800'
																	: execution.status === 'FAILURE'
																	? 'bg-red-100 text-red-800'
																	: 'bg-yellow-100 text-yellow-800'
															}`}>
																{execution.status || 'PENDING'}
															</span>
															<span className="text-sm font-medium text-gray-900">
																Execution #{idx + 1}
															</span>
														</div>
														<div className="space-y-1 text-xs text-gray-600">
															{execution.date_started && (
																<div><span className="font-medium">Started:</span> {execution.date_started}</div>
															)}
															{execution.date_done && (
																<div><span className="font-medium">Completed:</span> {execution.date_done}</div>
															)}
														</div>
													</div>
													<div className="flex flex-col gap-1">
														{execution.worker && (
															<span className="text-xs text-gray-500">
																<span className="font-medium">Worker:</span> {execution.worker}
															</span>
														)}
														{execution.task_args && (
															<span className="text-xs text-gray-500">
																<span className="font-medium">Args:</span> {execution.task_args}
															</span>
														)}
														{execution.task_kwargs && execution.task_kwargs !== '"{}"' && (
															<span className="text-xs text-gray-500">
																<span className="font-medium">Kwargs:</span> {execution.task_kwargs}
															</span>
														)}
													</div>
												</div>

												{/* Result */}
												{execution.result && execution.result !== 'null' && (
													<div className="mt-3">
														<h5 className="text-xs font-medium text-gray-700 mb-1">Result</h5>
														<pre className="bg-green-50 border border-green-200 rounded p-2 text-xs text-green-800 overflow-x-auto">
															{execution.result}
														</pre>
													</div>
												)}


												{execution.traceback && (
													<div className="mt-3">
														<h5 className="text-xs font-medium text-red-700 mb-1">Traceback</h5>
														<pre className="bg-red-50 border border-red-200 rounded p-2 text-xs text-red-800 overflow-x-auto whitespace-pre-wrap">
															{execution.traceback}
														</pre>
													</div>
												)}
											</div>
										))}
									</div>
								)}
							</div>

							{/* Modal footer */}
							<div className="bg-gray-50 px-6 py-3 flex justify-end">
								<button
									onClick={closeHistoryModal}
									className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
								>
									Close
								</button>
							</div>
						</div>
					</div>
				</div>
			)}
		</div>
	);
}