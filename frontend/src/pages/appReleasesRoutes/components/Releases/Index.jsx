import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import useApi from '../../../../hooks/useApi';
import BreadCrumbs from '../../../app/components/BreadCrumbs';
import {
	selectRerenderPage,
	selectAppReleasesData,
	setAppReleasesData
} from '../../slice/Index';

export default function Releases() {
	const { appId } = useParams();
	const dispatch = useDispatch();
	const triggerApi = useApi();
	
	const rerenderPage = useSelector(selectRerenderPage);
	const appReleasesData = useSelector(selectAppReleasesData);
	
	const [loading, setLoading] = useState(true);
	const [searchTerm, setSearchTerm] = useState('');
	const [filters, setFilters] = useState({
		status: '',
		version: ''
	});
	const [page, setPage] = useState(1);
	const [pageSize] = useState(20);
	const [totalPages, setTotalPages] = useState(1);
	const [viewMode, setViewMode] = useState('card'); // 'card' or 'list'

	const updateAppReleasesData = (value) => {
		dispatch(setAppReleasesData(value));
	};

	// Fetch releases data
	const fetchReleases = async () => {
		setLoading(true);
		try {
			const queryParams = new URLSearchParams({
				page: page.toString(),
				page_size: pageSize.toString(),
				include_dropdown_options: 'true',
				search: searchTerm,
			});

			// Add filters
			if (filters.status !== '') {
				queryParams.append('search_status', filters.status);
			}
			if (filters.version) {
				queryParams.append('search_version', filters.version);
			}

			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/releases/?${queryParams.toString()}`,
				type: 'GET',
				loader: false,
			});

			if (success && response) {
				updateAppReleasesData(response);
				setTotalPages(response.releases?.total_pages || 1);
			}
		} catch (error) {
			console.error('Error fetching releases:', error);
		} finally {
			setLoading(false);
		}
	};

	useEffect(() => {
		fetchReleases();
	}, [appId, page, searchTerm, filters, rerenderPage]);

	// Format date
	const formatDate = (dateString) => {
		if (!dateString) return '-';
		const date = new Date(dateString);
		const now = new Date();
		const diffMs = now - date;
		const diffDays = Math.floor(diffMs / 86400000);
		
		if (diffDays === 0) return 'Today';
		if (diffDays === 1) return 'Yesterday';
		if (diffDays < 7) return `${diffDays} days ago`;
		
		return date.toLocaleDateString();
	};

	const releases = appReleasesData?.releases?.records || [];
	const statusOptions = appReleasesData?.dropdown_options?.status || [];
	const versionOptions = appReleasesData?.dropdown_options?.version || [];

	return (
		<>
			<div className="flex flex-col h-full bg-[#F8FAFC] overflow-hidden">
				{/* Header */}
				<div className="bg-white border-b border-[#E5E7EB] px-[40px] py-[20px] flex-shrink-0">
					<div className="flex items-center justify-between">
						<div>
							<BreadCrumbs />
							<div className="flex items-center gap-[12px] mt-[8px]">
								<div className="flex h-[40px] w-[40px] items-center justify-center rounded-[8px] bg-gradient-to-br from-[#10B981] to-[#059669] shadow-lg">
									<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
										<path d="M7 4V2C7 1.44772 7.44772 1 8 1H16C16.5523 1 17 1.44772 17 2V4H20C20.5523 4 21 4.44772 21 5C21 5.55228 20.5523 6 20 6H19V19C19 20.1046 18.1046 21 17 21H7C5.89543 21 5 20.1046 5 19V6H4C3.44772 6 3 5.55228 3 5C3 4.44772 3.44772 4 4 4H7ZM9 3V4H15V3H9ZM7 6V19H17V6H7ZM9 8C9.55228 8 10 8.44772 10 9V17C10 17.5523 9.55228 18 9 18C8.44772 18 8 17.5523 8 17V9C8 8.44772 8.44772 8 9 8ZM15 8C15.5523 8 16 8.44772 16 9V17C16 17.5523 15.5523 18 15 18C14.4477 18 14 17.5523 14 17V9C14 8.44772 14.4477 8 15 8Z" fill="white"/>
									</svg>
								</div>
								<div>
									<h1 className="font-source-sans-pro text-[24px] font-semibold leading-[32px] text-[#111827]">
										Releases
									</h1>
									<p className="font-lato text-[14px] leading-[20px] text-[#6B7280]">
										Manage your application releases and deployments
									</p>
								</div>
							</div>
						</div>
					</div>
				</div>

				{/* Content */}
				<div className="flex-1 px-[40px] py-[32px] bg-[#F8FAFC] overflow-y-auto">
					<div className="space-y-6">
						{/* Stats Cards */}
						<div className="grid grid-cols-1 md:grid-cols-3 gap-4">
							<div className="rounded-lg border bg-card p-6 transition-colors hover:bg-accent/5">
								<div className="flex items-center justify-between">
									<div>
										<p className="text-sm font-medium text-muted-foreground">Total Releases</p>
										<p className="text-2xl font-medium tracking-tight mt-1">{releases.length}</p>
									</div>
									<div className="p-3 bg-green-500/10 rounded-md">
										<svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-green-600">
											<path d="M12 2L13.09 8.26L22 9.27L17 14.14L18.18 23.02L12 19.77L5.82 23.02L7 14.14L2 9.27L10.91 8.26L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
										</svg>
									</div>
								</div>
							</div>

							<div className="rounded-lg border bg-card p-6 transition-colors hover:bg-accent/5">
								<div className="flex items-center justify-between">
									<div>
										<p className="text-sm font-medium text-muted-foreground">Successful Releases</p>
										<p className="text-2xl font-medium tracking-tight text-emerald-600 dark:text-emerald-400 mt-1">
											{releases.filter(release => release.status === 'Success' || release.status === 'Completed').length}
										</p>
									</div>
									<div className="p-3 bg-emerald-500/10 rounded-md">
										<svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-emerald-600 dark:text-emerald-400">
											<circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
											<path d="M8 12L11 15L16 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
										</svg>
									</div>
								</div>
							</div>

							<div className="rounded-lg border bg-card p-6 transition-colors hover:bg-accent/5">
								<div className="flex items-center justify-between">
									<div>
										<p className="text-sm font-medium text-muted-foreground">Failed Releases</p>
										<p className="text-2xl font-medium tracking-tight text-red-600 dark:text-red-400 mt-1">
											{releases.filter(release => release.status === 'Failed' || release.status === 'Error').length}
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
						<div className="rounded-lg border bg-card p-6">
							<div className="flex flex-wrap gap-2">
								{/* Search */}
								<div className="relative">
									<input
										type="text"
										placeholder="Search releases..."
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

								{/* Status Filter */}
								<select
									value={filters.status}
									onChange={(e) => setFilters({ ...filters, status: e.target.value })}
									className="h-9 rounded-md border bg-background px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
								>
									<option value="">All Status</option>
									{statusOptions.map(status => (
										<option key={status.id} value={status.id}>{status.label}</option>
									))}
								</select>

								{/* Version Filter */}
								<select
									value={filters.version}
									onChange={(e) => setFilters({ ...filters, version: e.target.value })}
									className="h-9 rounded-md border bg-background px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
								>
									<option value="">All Versions</option>
									{versionOptions.map(version => (
										<option key={version.id} value={version.id}>{version.label}</option>
									))}
								</select>

								{/* View Toggle */}
								<div className="flex items-center gap-1 border rounded-md p-1">
									<button
										onClick={() => setViewMode('card')}
										className={`h-7 px-3 rounded-sm text-xs font-medium transition-colors ${
											viewMode === 'card'
												? 'bg-primary text-primary-foreground'
												: 'hover:bg-accent hover:text-accent-foreground'
										}`}
										title="Card View"
									>
										<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
											<path d="M1 2.5A1.5 1.5 0 012.5 1h3A1.5 1.5 0 017 2.5v3A1.5 1.5 0 015.5 7h-3A1.5 1.5 0 011 5.5v-3zm8 0A1.5 1.5 0 0110.5 1h3A1.5 1.5 0 0115 2.5v3A1.5 1.5 0 0113.5 7h-3A1.5 1.5 0 019 5.5v-3zm-8 8A1.5 1.5 0 012.5 9h3A1.5 1.5 0 017 10.5v3A1.5 1.5 0 015.5 15h-3A1.5 1.5 0 011 13.5v-3zm8 0A1.5 1.5 0 0110.5 9h3A1.5 1.5 0 0115 10.5v3A1.5 1.5 0 0113.5 15h-3A1.5 1.5 0 019 13.5v-3z"/>
										</svg>
									</button>
									<button
										onClick={() => setViewMode('list')}
										className={`h-7 px-3 rounded-sm text-xs font-medium transition-colors ${
											viewMode === 'list'
												? 'bg-primary text-primary-foreground'
												: 'hover:bg-accent hover:text-accent-foreground'
										}`}
										title="List View"
									>
										<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
											<path fillRule="evenodd" d="M2.5 12a.5.5 0 01.5-.5h10a.5.5 0 010 1H3a.5.5 0 01-.5-.5zm0-4a.5.5 0 01.5-.5h10a.5.5 0 010 1H3a.5.5 0 01-.5-.5zm0-4a.5.5 0 01.5-.5h10a.5.5 0 010 1H3a.5.5 0 01-.5-.5z"/>
										</svg>
									</button>
								</div>
							</div>
						</div>

						{/* Releases List */}
						<div className="space-y-4">
							{loading ? (
								<div className="rounded-lg border bg-card p-12">
									<div className="flex items-center justify-center">
										<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
									</div>
								</div>
							) : releases.length === 0 ? (
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
											d="M12 2L13.09 8.26L22 9.27L17 14.14L18.18 23.02L12 19.77L5.82 23.02L7 14.14L2 9.27L10.91 8.26L12 2Z"
										/>
									</svg>
									<p className="mt-2 text-sm text-muted-foreground">No releases found</p>
								</div>
							) : viewMode === 'card' ? (
								<ReleasesList
									releases={releases}
									formatDate={formatDate}
								/>
							) : (
								<ReleasesTable
									releases={releases}
									formatDate={formatDate}
								/>
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
									Showing {releases.length} of {totalPages * pageSize} releases
								</span>
							</div>
						)}
					</div>
				</div>
			</div>
		</>
	);
}

// Releases List Component (Card View)
function ReleasesList({ releases, formatDate }) {
	return (
		<>
			{releases.map((release) => (
				<ReleaseCard
					key={release.id}
					release={release}
					formatDate={formatDate}
				/>
			))}
		</>
	);
}

// Release Card Component
function ReleaseCard({ release, formatDate }) {
	const getStatusColor = (status) => {
		switch (status?.toLowerCase()) {
			case 'success':
			case 'completed':
				return 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20';
			case 'failed':
			case 'error':
				return 'bg-red-500/10 text-red-700 dark:text-red-400 border border-red-500/20';
			case 'pending':
			case 'in_progress':
				return 'bg-yellow-500/10 text-yellow-700 dark:text-yellow-400 border border-yellow-500/20';
			default:
				return 'bg-gray-500/10 text-gray-700 dark:text-gray-400 border border-gray-500/20';
		}
	};

	const getStatusDot = (status) => {
		switch (status?.toLowerCase()) {
			case 'success':
			case 'completed':
				return 'bg-emerald-600';
			case 'failed':
			case 'error':
				return 'bg-red-600';
			case 'pending':
			case 'in_progress':
				return 'bg-yellow-600';
			default:
				return 'bg-gray-600';
		}
	};

	return (
		<div className="rounded-lg border bg-card overflow-hidden transition-all hover:shadow-md">
			<div className="p-6">
				<div className="flex items-start justify-between">
					<div className="flex items-start gap-4">
						{/* Release Icon */}
						<div className="w-12 h-12 bg-gradient-to-br from-green-500 to-green-600 rounded-full flex items-center justify-center text-white font-semibold">
							<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
								<path d="M12 2L13.09 8.26L22 9.27L17 14.14L18.18 23.02L12 19.77L5.82 23.02L7 14.14L2 9.27L10.91 8.26L12 2Z" fill="currentColor"/>
							</svg>
						</div>

						{/* Release Info */}
						<div className="space-y-2">
							<div className="flex items-center gap-3">
								<h3 className="font-medium text-lg">Release {release.version}</h3>
								<span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(release.status)}`}>
									<span className={`w-1.5 h-1.5 rounded-full ${getStatusDot(release.status)}`}></span>
									{release.status}
								</span>
							</div>
							
							<div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
								<span className="flex items-center gap-1">
									<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" className="opacity-50">
										<path d="M8 4a.75.75 0 01.75.75v3.5h2.5a.75.75 0 010 1.5h-3.25A.75.75 0 017.25 9V4.75A.75.75 0 018 4z"/>
										<path d="M8 15A7 7 0 108 1a7 7 0 000 14zm0 1A8 8 0 108 0a8 8 0 000 16z"/>
									</svg>
									Version: {release.version}
								</span>
								<span className="flex items-center gap-1">
									<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" className="opacity-50">
										<path d="M3.5 0a.5.5 0 01.5.5V1h8V.5a.5.5 0 011 0V1h1a2 2 0 012 2v11a2 2 0 01-2 2H2a2 2 0 01-2-2V3a2 2 0 012-2h1V.5a.5.5 0 01.5 0zM1 4v10a1 1 0 001 1h12a1 1 0 001-1V4H1z"/>
									</svg>
									{formatDate(release.created_at)}
								</span>
								{release.last_git_hash && (
									<span className="flex items-center gap-1">
										<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" className="opacity-50">
											<path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.012 8.012 0 0 0 16 8c0-4.42-3.58-8-8-8z"/>
										</svg>
										{release.last_git_hash.substring(0, 8)}
									</span>
								)}
							</div>

							{/* Description */}
							{release.description && (
								<div className="mt-2">
									<p className="text-sm text-muted-foreground">{release.description}</p>
								</div>
							)}
						</div>
					</div>
				</div>
			</div>
		</div>
	);
}

// Releases Table Component (List View)
function ReleasesTable({ releases, formatDate }) {
	const getStatusColor = (status) => {
		switch (status?.toLowerCase()) {
			case 'success':
			case 'completed':
				return 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20';
			case 'failed':
			case 'error':
				return 'bg-red-500/10 text-red-700 dark:text-red-400 border border-red-500/20';
			case 'pending':
			case 'in_progress':
				return 'bg-yellow-500/10 text-yellow-700 dark:text-yellow-400 border border-yellow-500/20';
			default:
				return 'bg-gray-500/10 text-gray-700 dark:text-gray-400 border border-gray-500/20';
		}
	};

	const getStatusDot = (status) => {
		switch (status?.toLowerCase()) {
			case 'success':
			case 'completed':
				return 'bg-emerald-600';
			case 'failed':
			case 'error':
				return 'bg-red-600';
			case 'pending':
			case 'in_progress':
				return 'bg-yellow-600';
			default:
				return 'bg-gray-600';
		}
	};

	return (
		<div className="rounded-lg border bg-card overflow-hidden">
			<div className="overflow-x-auto">
				<table className="w-full">
					<thead className="bg-muted/50 border-b">
						<tr>
							<th className="text-left p-4 font-medium text-sm">Release</th>
							<th className="text-left p-4 font-medium text-sm">Version</th>
							<th className="text-left p-4 font-medium text-sm">Status</th>
							<th className="text-left p-4 font-medium text-sm">Date</th>
							<th className="text-left p-4 font-medium text-sm">Git Hash</th>
						</tr>
					</thead>
					<tbody>
						{releases.map((release, index) => (
							<tr key={release.id} className={`border-b hover:bg-muted/50 transition-colors ${index === releases.length - 1 ? 'border-b-0' : ''}`}>
								<td className="p-4">
									<div className="flex items-center gap-3">
										<div className="w-10 h-10 bg-gradient-to-br from-green-500 to-green-600 rounded-full flex items-center justify-center text-white font-semibold text-sm">
											<svg width="16" height="16" viewBox="0 0 24 24" fill="none">
												<path d="M12 2L13.09 8.26L22 9.27L17 14.14L18.18 23.02L12 19.77L5.82 23.02L7 14.14L2 9.27L10.91 8.26L12 2Z" fill="currentColor"/>
											</svg>
										</div>
										<div>
											<div className="font-medium">Release {release.version}</div>
											{release.description && (
												<div className="text-sm text-muted-foreground truncate max-w-xs">{release.description}</div>
											)}
										</div>
									</div>
								</td>
								<td className="p-4">
									<span className="font-mono text-sm">{release.version}</span>
								</td>
								<td className="p-4">
									<span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(release.status)}`}>
										<span className={`w-1.5 h-1.5 rounded-full ${getStatusDot(release.status)}`}></span>
										{release.status}
									</span>
								</td>
								<td className="p-4">
									<span className="text-sm">{formatDate(release.created_at)}</span>
								</td>
								<td className="p-4">
									{release.last_git_hash ? (
										<span className="font-mono text-sm text-muted-foreground">{release.last_git_hash.substring(0, 8)}</span>
									) : (
										<span className="text-sm text-muted-foreground">-</span>
									)}
								</td>
							</tr>
						))}
					</tbody>
				</table>
			</div>
		</div>
	);
}