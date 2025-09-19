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
	const [pageSize] = useState(10);
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
		}
	});

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
				queryParams.append('is_enabled', filters.is_enabled.toString());
			}

			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/tasks/?${queryParams.toString()}`,
				type: 'GET',
				loader: false,
			});

			if (success && response?.tasks) {
				setTasks(response.tasks.records || []);
				setTotalPages(response.tasks.total_pages || 1);
			}
		} catch (error) {
			console.error('Error fetching tasks:', error);
		} finally {
			setLoading(false);
		}
	};

	useEffect(() => {
		fetchTasks();
	}, [appId, page, searchTerm, filters]);

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
			}
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
		if (!editingTask) return;

		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/tasks/${editingTask.id}/`,
			type: 'POST',
			loader: true,
			data: {
				is_enabled: editFormData.is_enabled,
				crontab_exp: JSON.stringify(editFormData.crontab_exp)
			}
		});

		if (success) {
			closeEditModal();
			fetchTasks();
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
										<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
											Policies
										</th>
										<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
											Actions
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
															<div>
																<div className="text-sm font-medium text-gray-900">
																	{task.name}
																</div>
																<div className="text-sm text-gray-500">
																	ID: {task.id}
																</div>
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
													<td className="px-6 py-4 whitespace-nowrap">
														<span className="text-sm text-gray-900">
															{task.attached_policies?.length || 0} policies
														</span>
													</td>
													<td className="px-6 py-4 whitespace-nowrap">
														<button 
															onClick={() => openEditModal(task)}
															className="text-blue-600 hover:text-blue-700 text-sm font-medium"
														>
															Edit
														</button>
													</td>
												</tr>

												{isExpanded && (
													<tr>
														<td colSpan="5" className="p-0">
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
																							{new Date(task.created_date).toLocaleString()}
																						</span>
																					</div>
																					<div className="flex items-start gap-2">
																						<span className="text-xs text-gray-500 font-medium min-w-[80px]">Modified:</span>
																						<span className="text-xs text-gray-700">
																							{new Date(task.modified_date).toLocaleString()}
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
																				<pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-xs">
																					<code>{task.code}</code>
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
									Showing {tasks.length} of {totalPages * pageSize} tasks
								</span>
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
						<div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
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
		</div>
	);
}