import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import useApi from '../../../../hooks/useApi';
import BreadCrumbs from '../../../app/components/BreadCrumbs';
import {
	setAddSecretModalOpen,
	setEditSecretModalOpen,
	setAppSecretsFormData,
	selectRerenderPage,
	selectAppSecretsData,
	setAppSecretsData
} from '../../slice/Index';
import AddSecretModal from '../Modals/AddSecretModal';
import EditSecretModal from '../Modals/EditSecretModal';

export default function Secrets() {
	const { appId } = useParams();
	const dispatch = useDispatch();
	const triggerApi = useApi();
	
	const rerenderPage = useSelector(selectRerenderPage);
	const appSecretsData = useSelector(selectAppSecretsData);
	
	const [loading, setLoading] = useState(true);
	const [searchTerm, setSearchTerm] = useState('');
	const [page, setPage] = useState(1);
	const [pageSize] = useState(20);
	const [totalPages, setTotalPages] = useState(1);
	const [viewMode, setViewMode] = useState('card'); // 'card' or 'list'
	const [visibleSecrets, setVisibleSecrets] = useState({}); // Track which secrets are visible
	const [loadingSecrets, setLoadingSecrets] = useState({}); // Track which secrets are loading

	const updateAppSecretsData = (value) => {
		dispatch(setAppSecretsData(value));
	};

	// Fetch secrets data
	const fetchSecrets = async () => {
		setLoading(true);
		try {
			const queryParams = new URLSearchParams({
				page: page.toString(),
				page_size: pageSize.toString(),
				include_dropdown_options: 'true',
				search: searchTerm,
			});

			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/secrets/?${queryParams.toString()}`,
				type: 'GET',
				loader: false,
			});

			if (success && response) {
				updateAppSecretsData(response);
				setTotalPages(response.secrets?.total_pages || 1);
			}
		} catch (error) {
			console.error('Error fetching secrets:', error);
		} finally {
			setLoading(false);
		}
	};

	useEffect(() => {
		fetchSecrets();
	}, [appId, page, searchTerm, rerenderPage]);

	// Format date
	const formatDate = (dateString) => {
		if (!dateString) return '-';
		
		// Handle the API format "12 May 2025 05:27"
		try {
			const date = new Date(dateString);
			const now = new Date();
			const diffMs = now - date;
			const diffDays = Math.floor(diffMs / 86400000);
			
			// If it's a valid date, use relative formatting
			if (!isNaN(date.getTime())) {
				if (diffDays === 0) return 'Today';
				if (diffDays === 1) return 'Yesterday';
				if (diffDays < 7) return `${diffDays} days ago`;
				
				return date.toLocaleDateString();
			}
			
			// If date parsing fails, return the original string
			return dateString;
		} catch (error) {
			// Fallback to original string if parsing fails
			return dateString;
		}
	};

	const handleAddSecret = () => {
		dispatch(setAddSecretModalOpen(true));
	};

	const handleEditSecret = (secret) => {
		// Set the secret data for editing
		dispatch(setAppSecretsFormData(secret));

		// Open the edit modal
		dispatch(setEditSecretModalOpen(true));
	};

	const handleViewSecret = async (secret, event) => {
		event?.stopPropagation(); // Prevent card click when clicking view button
		
		const secretId = secret.id;
		
		// If secret is already visible, hide it
		if (visibleSecrets[secretId]) {
			setVisibleSecrets(prev => ({
				...prev,
				[secretId]: null
			}));
			return;
		}
		
		// Set loading state
		setLoadingSecrets(prev => ({
			...prev,
			[secretId]: true
		}));
		
		try {
			const queryParams = new URLSearchParams({
				secret_id: secretId.toString(),
				action: 'get_secret_value'
			});
			
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/secrets/?${queryParams.toString()}`,
				type: 'GET',
				loader: false,
			});
			
			if (success && response) {
				// Store the secret value
				setVisibleSecrets(prev => ({
					...prev,
					[secretId]: response.secret_value || response.value || 'No value found'
				}));
			} else {
				console.error('Failed to fetch secret value');
			}
		} catch (error) {
			console.error('Error fetching secret value:', error);
		} finally {
			// Remove loading state
			setLoadingSecrets(prev => ({
				...prev,
				[secretId]: false
			}));
		}
	};

	const secrets = appSecretsData?.secrets?.records || [];
	const totalRecords = appSecretsData?.secrets?.total_records || 0;

	return (
		<>
			<div className="flex flex-col h-full bg-[#F8FAFC] overflow-hidden">
				{/* Header */}
				<div className="bg-white border-b border-[#E5E7EB] px-[40px] py-[20px] flex-shrink-0">
					<div className="flex items-center justify-between">
						<div>
							<BreadCrumbs />
							<div className="flex items-center gap-[12px] mt-[8px]">
								<div className="flex h-[40px] w-[40px] items-center justify-center rounded-[8px] bg-gradient-to-br from-[#7C3AED] to-[#5B21B6] shadow-lg">
									<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
										<path d="M6 10C6 8.89543 6.89543 8 8 8H16C17.1046 8 18 8.89543 18 10V18C18 19.1046 17.1046 20 16 20H8C6.89543 20 6 19.1046 6 18V10Z" stroke="white" strokeWidth="2"/>
										<path d="M10 8V6C10 4.89543 10.8954 4 12 4C13.1046 4 14 4.89543 14 6V8" stroke="white" strokeWidth="2" strokeLinecap="round"/>
									</svg>
								</div>
								<div>
									<h1 className="font-source-sans-pro text-[24px] font-semibold leading-[32px] text-[#111827]">
										Secrets
									</h1>
									<p className="font-lato text-[14px] leading-[20px] text-[#6B7280]">
										Manage your application secrets and environment variables
									</p>
								</div>
							</div>
						</div>
						<button
							type="button"
							onClick={handleAddSecret}
							className="flex items-center gap-[8px] rounded-[8px] bg-[#7C3AED] hover:bg-[#6D28D9] px-[16px] py-[8px] transition-colors"
						>
							<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
								<path d="M8 3V13M3 8H13" stroke="white" strokeWidth="2" strokeLinecap="round"/>
							</svg>
							<span className="font-medium text-[14px] text-white">Add Secret</span>
						</button>
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
										<p className="text-sm font-medium text-muted-foreground">Total Secrets</p>
										<p className="text-2xl font-medium tracking-tight mt-1">{totalRecords}</p>
									</div>
									<div className="p-3 bg-purple-500/10 rounded-md">
										<svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-purple-600">
											<path d="M6 10C6 8.89543 6.89543 8 8 8H16C17.1046 8 18 8.89543 18 10V18C18 19.1046 17.1046 20 16 20H8C6.89543 20 6 19.1046 6 18V10Z" stroke="currentColor" strokeWidth="2"/>
											<path d="M10 8V6C10 4.89543 10.8954 4 12 4C13.1046 4 14 4.89543 14 6V8" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
										</svg>
									</div>
								</div>
							</div>

							<div className="rounded-lg border bg-card p-6 transition-colors hover:bg-accent/5">
								<div className="flex items-center justify-between">
									<div>
										<p className="text-sm font-medium text-muted-foreground">Active Secrets</p>
										<p className="text-2xl font-medium tracking-tight text-emerald-600 dark:text-emerald-400 mt-1">
											{secrets.filter(secret => secret.is_active !== false).length}
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
										<p className="text-sm font-medium text-muted-foreground">Inactive Secrets</p>
										<p className="text-2xl font-medium tracking-tight text-red-600 dark:text-red-400 mt-1">
											{secrets.filter(secret => secret.is_active === false).length}
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

						{/* Search and View Toggle */}
						<div className="rounded-lg border bg-card p-6">
							<div className="flex flex-wrap gap-2 items-center justify-between">
								{/* Search */}
								<div className="relative">
									<input
										type="text"
										placeholder="Search secrets..."
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
											<path d="M1 2.5A1.5 1.5 0 012.5 1h3A1.5 1.5 0 017 2.5v3A1.5 1.5 0 015.5 7h-3A1.5 1.5 0 011 5.5v-3zm8 0A1.5 1.5 0 0110.5 1h3A1.5 1.5 0 0115 2.5v3A1.5 1.5 0 0113.5 7h-3A1.5 1.5 0 019 5.5v-3zm-8 8A1.5 1.5 0 012.5 9h3A1.5 1.5 0 017 10.5v3A1.5 1.5 0 75.5 15h-3A1.5 1.5 0 011 13.5v-3zm8 0A1.5 1.5 0 0110.5 9h3A1.5 1.5 0 0115 10.5v3A1.5 1.5 0 0113.5 15h-3A1.5 1.5 0 019 13.5v-3z"/>
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

						{/* Secrets List */}
						<div className="space-y-4">
							{loading ? (
								<div className="rounded-lg border bg-card p-12">
									<div className="flex items-center justify-center">
										<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
									</div>
								</div>
							) : secrets.length === 0 ? (
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
											d="M6 10C6 8.89543 6.89543 8 8 8H16C17.1046 8 18 8.89543 18 10V18C18 19.1046 17.1046 20 16 20H8C6.89543 20 6 19.1046 6 18V10Z"
										/>
										<path
											strokeLinecap="round"
											strokeLinejoin="round"
											strokeWidth={1.5}
											d="M10 8V6C10 4.89543 10.8954 4 12 4C13.1046 4 14 4.89543 14 6V8"
										/>
									</svg>
									<p className="mt-2 text-sm text-muted-foreground">
										{totalRecords === 0 ? 'No secrets found. Create your first secret to get started.' : 'No secrets match your current filters.'}
									</p>
									{totalRecords === 0 && (
										<button
											onClick={handleAddSecret}
											className="mt-4 px-4 py-2 bg-[#7C3AED] text-white rounded-md hover:bg-[#6D28D9] transition-colors"
										>
											Add Your First Secret
										</button>
									)}
								</div>
							) : viewMode === 'card' ? (
								<SecretsList
									secrets={secrets}
									formatDate={formatDate}
									onEdit={handleEditSecret}
									onView={handleViewSecret}
									visibleSecrets={visibleSecrets}
									loadingSecrets={loadingSecrets}
								/>
							) : (
								<SecretsTable
									secrets={secrets}
									formatDate={formatDate}
									onEdit={handleEditSecret}
									onView={handleViewSecret}
									visibleSecrets={visibleSecrets}
									loadingSecrets={loadingSecrets}
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
									Showing {((page - 1) * pageSize) + 1}-{Math.min(page * pageSize, totalRecords)} of {totalRecords} secrets
								</span>
							</div>
						)}
					</div>
				</div>
			</div>
			<AddSecretModal />
			<EditSecretModal />
		</>
	);
}

// Secrets List Component (Card View)
function SecretsList({ secrets, formatDate, onEdit, onView, visibleSecrets, loadingSecrets }) {
	return (
		<>
			{secrets.map((secret) => (
				<SecretCard
					key={secret.id}
					secret={secret}
					formatDate={formatDate}
					onEdit={onEdit}
					onView={onView}
					visibleSecrets={visibleSecrets}
					loadingSecrets={loadingSecrets}
				/>
			))}
		</>
	);
}

// Secret Card Component
function SecretCard({ secret, formatDate, onEdit, onView, visibleSecrets, loadingSecrets }) {
	const getStatusColor = (isActive) => {
		return isActive !== false
			? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20'
			: 'bg-red-500/10 text-red-700 dark:text-red-400 border border-red-500/20';
	};

	const getStatusDot = (isActive) => {
		return isActive !== false ? 'bg-emerald-600' : 'bg-red-600';
	};

	const getTypeIcon = (key) => {
		const upperKey = key?.toUpperCase() || '';
		
		// Database related
		if (upperKey.includes('DATABASE') || upperKey.includes('DB_') || upperKey.includes('_DB')) {
			return (
				<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
					<path d="M12 3C7.03 3 3 4.79 3 7V17C3 19.21 7.03 21 12 21S21 19.21 21 17V7C21 4.79 16.97 3 12 3ZM12 5C15.87 5 19 6.12 19 7S15.87 9 12 9 5 7.88 5 7 8.13 5 12 5ZM5 9.5C6.13 10.24 8.91 11 12 11S17.87 10.24 19 9.5V12C19 13.12 15.87 14 12 14S5 13.12 5 12V9.5ZM5 14.5C6.13 15.24 8.91 16 12 16S17.87 15.24 19 14.5V17C19 18.12 15.87 19 12 19S5 18.12 5 17V14.5Z"/>
				</svg>
			);
		}
		
		// API/Token related
		if (upperKey.includes('API') || upperKey.includes('TOKEN') || upperKey.includes('KEY') || upperKey.includes('SECRET')) {
			return (
				<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
					<path d="M7 14C5.9 14 5 13.1 5 12S5.9 10 7 10 9 10.9 9 12 8.1 14 7 14M12.6 10C11.8 7.7 9.6 6 7 6C3.7 6 1 8.7 1 12S3.7 18 7 18C9.6 18 11.8 16.3 12.6 14H16V18H20V14H23V10H12.6Z"/>
				</svg>
			);
		}
		
		// Environment variables (contains underscores or common env patterns)
		if (upperKey.includes('_') || upperKey.includes('ENV') || upperKey.includes('CONFIG')) {
			return (
				<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
					<path d="M13 2L3 14H12L11 22L21 10H12L13 2Z"/>
				</svg>
			);
		}
		
		// Default lock icon
		return (
			<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
				<path d="M12 1L3 5V11C3 16.55 6.84 21.74 12 23C17.16 21.74 21 16.55 21 11V5L12 1M12 7C13.4 7 14.8 8.6 14.8 10V11.5C15.4 11.5 16 12.4 16 13V16C16 17.4 15.4 18 14.8 18H9.2C8.6 18 8 17.4 8 16V13C8 12.4 8.6 11.5 9.2 11.5V10C9.2 8.6 10.6 7 12 7M12 8.2C11.2 8.2 10.5 8.7 10.5 10V11.5H13.5V10C13.5 8.7 12.8 8.2 12 8.2Z"/>
			</svg>
		);
	};

	return (
		<div className="rounded-lg border bg-card overflow-hidden transition-all hover:shadow-md hover:border-primary/20 group">
			<div className="p-6">
				<div className="flex items-start justify-between">
					<div className="flex items-start gap-4">
						{/* Secret Icon */}
						<div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-purple-600 rounded-full flex items-center justify-center text-white transition-transform group-hover:scale-105">
							{getTypeIcon(secret.key)}
						</div>

						{/* Secret Info */}
						<div className="space-y-2">
							<div className="flex items-center gap-3">
								<h3 className="font-medium text-lg">{secret.key}</h3>
								<span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(secret.is_active)}`}>
									<span className={`w-1.5 h-1.5 rounded-full ${getStatusDot(secret.is_active)}`}></span>
									{secret.is_active !== false ? 'Active' : 'Inactive'}
								</span>
							</div>
							
							<div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
								<span className="flex items-center gap-1">
									<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" className="opacity-50">
										<path d="M3.5 0a.5.5 0 01.5.5V1h8V.5a.5.5 0 011 0V1h1a2 2 0 012 2v11a2 2 0 01-2 2H2a2 2 0 01-2-2V3a2 2 0 012-2h1V.5a.5.5 0 01.5 0zM1 4v10a1 1 0 001 1h12a1 1 0 001-1V4H1z"/>
									</svg>
									{formatDate(secret.created_at)}
								</span>
								<span className="flex items-center gap-1">
									<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" className="opacity-50">
										<path d="M11 1a1 1 0 011 1v12a1 1 0 01-1 1H5a1 1 0 01-1-1V2a1 1 0 011-1h6zM5 0a2 2 0 00-2 2v12a2 2 0 002 2h6a2 2 0 002-2V2a2 2 0 00-2-2H5z"/>
									</svg>
									ID: {secret.id}
								</span>
								{secret.modified_at && (
									<span className="flex items-center gap-1">
										<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" className="opacity-50">
											<path d="M8 4a.75.75 0 01.75.75v3.5h2.5a.75.75 0 010 1.5h-3.25A.75.75 0 017.25 9V4.75A.75.75 0 018 4z"/>
											<path d="M8 15A7 7 0 108 1a7 7 0 000 14zm0 1A8 8 0 108 0a8 8 0 000 16z"/>
										</svg>
										Updated {formatDate(secret.modified_at)}
									</span>
								)}
							</div>

							{/* Value Preview */}
							<div className="mt-2">
								<div className="bg-muted/50 rounded-md p-3 font-mono text-sm border transition-colors">
									{loadingSecrets[secret.id] ? (
										<div className="flex items-center gap-2">
											<div className="w-3 h-3 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
											<span className="text-muted-foreground">Loading secret value...</span>
										</div>
									) : visibleSecrets[secret.id] ? (
										<span className="text-foreground break-all select-all bg-background/50 px-2 py-1 rounded border animate-in fade-in duration-300">{visibleSecrets[secret.id]}</span>
									) : (
										<span className="text-slate-600 dark:text-slate-300 tracking-wider select-none">••••••••••••••••••••</span>
									)}
								</div>
							</div>
						</div>
					</div>

					{/* Action Buttons */}
					<div className="flex items-start gap-1 ml-4">
						<button
							onClick={(e) => onView?.(secret, e)}
							className={`p-2 rounded-md transition-all ${
								loadingSecrets[secret.id] 
									? 'text-muted-foreground cursor-not-allowed opacity-50' 
									: visibleSecrets[secret.id]
										? 'text-blue-600 bg-blue-50 hover:bg-blue-100 border border-blue-200'
										: 'text-muted-foreground hover:text-blue-600 hover:bg-blue-50 border border-transparent hover:border-blue-200'
							}`}
							title={visibleSecrets[secret.id] ? 'Hide Secret' : 'View Secret'}
							disabled={loadingSecrets[secret.id]}
						>
							{loadingSecrets[secret.id] ? (
								<div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
							) : visibleSecrets[secret.id] ? (
								<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
									<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
									<path d="M1 1l22 22"/>
								</svg>
							) : (
								<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
									<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
									<circle cx="12" cy="12" r="3"/>
								</svg>
							)}
						</button>
						<button
							onClick={(e) => {
								e.stopPropagation();
								onEdit?.(secret);
							}}
							className="p-2 text-muted-foreground hover:text-purple-600 hover:bg-purple-50 rounded-md transition-all border border-transparent hover:border-purple-200"
							title="Edit Secret"
						>
							<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
								<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
								<path d="m18.5 2.5 a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
							</svg>
						</button>
					</div>
				</div>
			</div>
		</div>
	);
}

// Secrets Table Component (List View)
function SecretsTable({ secrets, formatDate, onEdit, onView, visibleSecrets, loadingSecrets }) {
	const getStatusColor = (isActive) => {
		return isActive !== false
			? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20'
			: 'bg-red-500/10 text-red-700 dark:text-red-400 border border-red-500/20';
	};

	const getStatusDot = (isActive) => {
		return isActive !== false ? 'bg-emerald-600' : 'bg-red-600';
	};

	return (
		<div className="rounded-lg border bg-card overflow-hidden">
			<div className="overflow-x-auto">
				<table className="w-full">
					<thead className="bg-muted/50 border-b">
						<tr>
							<th className="text-left p-4 font-medium text-sm text-muted-foreground">Key</th>
							<th className="text-left p-4 font-medium text-sm text-muted-foreground">Status</th>
							<th className="text-left p-4 font-medium text-sm text-muted-foreground">Value</th>
							<th className="text-left p-4 font-medium text-sm text-muted-foreground">Created</th>
							<th className="text-left p-4 font-medium text-sm text-muted-foreground">Modified</th>
							<th className="text-left p-4 font-medium text-sm text-muted-foreground">Actions</th>
						</tr>
					</thead>
					<tbody>
						{secrets.map((secret, index) => (
							<tr key={secret.id} className={`border-b hover:bg-muted/30 transition-colors group ${index === secrets.length - 1 ? 'border-b-0' : ''}`}>
								<td className="p-4">
									<div className="flex items-center gap-3">
										<div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-purple-600 rounded-full flex items-center justify-center text-white font-semibold text-sm transition-transform group-hover:scale-105">
											<svg width="16" height="16" viewBox="0 0 24 24" fill="none">
												<path d="M6 10C6 8.89543 6.89543 8 8 8H16C17.1046 8 18 8.89543 18 10V18C18 19.1046 17.1046 20 16 20H8C6.89543 20 6 19.1046 6 18V10Z" stroke="currentColor" strokeWidth="2"/>
												<path d="M10 8V6C10 4.89543 10.8954 4 12 4C13.1046 4 14 4.89543 14 6V8" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
											</svg>
										</div>
										<div>
											<div className="font-medium text-foreground">{secret.key}</div>
											<div className="text-sm text-muted-foreground">ID: {secret.id}</div>
										</div>
									</div>
								</td>
								<td className="p-4">
									<span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(secret.is_active)}`}>
										<span className={`w-1.5 h-1.5 rounded-full ${getStatusDot(secret.is_active)}`}></span>
										{secret.is_active !== false ? 'Active' : 'Inactive'}
									</span>
								</td>
								<td className="p-4">
									<div className="bg-muted/50 rounded-md p-2 font-mono text-sm max-w-xs border transition-colors">
										{loadingSecrets[secret.id] ? (
											<div className="flex items-center gap-2">
												<div className="w-3 h-3 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
												<span className="text-muted-foreground">Loading...</span>
											</div>
										) : visibleSecrets[secret.id] ? (
											<span className="text-foreground break-all select-all bg-background/50 px-1 py-0.5 rounded animate-in fade-in duration-300">{visibleSecrets[secret.id]}</span>
										) : (
											<span className="text-slate-600 dark:text-slate-300 tracking-wider select-none">••••••••••••••••</span>
										)}
									</div>
								</td>
								<td className="p-4">
									<span className="text-sm">{formatDate(secret.created_at)}</span>
								</td>
								<td className="p-4">
									{secret.modified_at ? (
										<span className="text-sm">{formatDate(secret.modified_at)}</span>
									) : (
										<span className="text-sm text-muted-foreground">-</span>
									)}
								</td>
								<td className="p-4">
									<div className="flex items-center gap-1">
										<button
											onClick={(e) => {
												e.stopPropagation();
												onView?.(secret, e);
											}}
											className={`p-1.5 rounded-md transition-all ${
												loadingSecrets[secret.id] 
													? 'text-muted-foreground cursor-not-allowed opacity-50' 
													: visibleSecrets[secret.id]
														? 'text-blue-600 bg-blue-50 hover:bg-blue-100 border border-blue-200'
														: 'text-muted-foreground hover:text-blue-600 hover:bg-blue-50 border border-transparent hover:border-blue-200'
											}`}
											title={visibleSecrets[secret.id] ? 'Hide Secret' : 'View Secret'}
											disabled={loadingSecrets[secret.id]}
										>
											{loadingSecrets[secret.id] ? (
												<div className="w-3 h-3 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
											) : visibleSecrets[secret.id] ? (
												<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
													<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
													<path d="M1 1l22 22"/>
												</svg>
											) : (
												<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
													<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
													<circle cx="12" cy="12" r="3"/>
												</svg>
											)}
										</button>
										<button
											onClick={(e) => {
												e.stopPropagation();
												onEdit?.(secret);
											}}
											className="p-1.5 text-muted-foreground hover:text-purple-600 hover:bg-purple-50 rounded-md transition-all border border-transparent hover:border-purple-200"
											title="Edit Secret"
										>
											<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
												<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
												<path d="m18.5 2.5 a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
											</svg>
										</button>
									</div>
								</td>
							</tr>
						))}
					</tbody>
				</table>
			</div>
		</div>
	);
}
