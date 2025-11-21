import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import useApi from '../../../../hooks/useApi';

export default function Packages() {
	const { appId } = useParams();
	const triggerApi = useApi();
	const [packagesData, setPackagesData] = useState(null);
	const [loading, setLoading] = useState(true);
	const [searchTerm, setSearchTerm] = useState('');
	const [page, setPage] = useState(1);
	const [totalPages, setTotalPages] = useState(1);
	const [totalRecords, setTotalRecords] = useState(0);
	const [pageSize, setPageSize] = useState(10);
	const [configModalOpen, setConfigModalOpen] = useState(false);
	const [configUrl, setConfigUrl] = useState('');
	const [installModalOpen, setInstallModalOpen] = useState(false);
	const [selectedPackage, setSelectedPackage] = useState(null);
	const [selectedVersion, setSelectedVersion] = useState('');
	const [installing, setInstalling] = useState(false);

	// Fetch packages from API
	const fetchPackages = async () => {
		setLoading(true);
		try {
			const queryParams = new URLSearchParams({
				page: page.toString(),
				page_size: pageSize.toString(),
				search: searchTerm,
			});

			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/packages/?${queryParams.toString()}`,
				type: 'GET',
				loader: false,
			});

			if (success && response?.packages) {
				setPackagesData(response.packages);
				setTotalPages(response.packages.total_pages || 1);
				setTotalRecords(response.packages.total_records || 0);
			}
		} catch (error) {
			console.error('Error fetching packages:', error);
		} finally {
			setLoading(false);
		}
	};

	// Install package
	const installPackage = async () => {
		if (!selectedPackage || !selectedVersion) return;

		setInstalling(true);
		try {
			const formData = new FormData();
			formData.append('name', selectedPackage.name);
			formData.append('version', selectedVersion);

			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/packages/?action=install`,
				type: 'POST',
				loader: true,
				payload: formData,
			});

			if (success) {
				setInstallModalOpen(false);
				setSelectedPackage(null);
				setSelectedVersion('');
				fetchPackages(); // Refresh the packages list
			}
		} catch (error) {
			console.error('Error installing package:', error);
		} finally {
			setInstalling(false);
		}
	};

	// Open install modal
	const openInstallModal = (pkg) => {
		setSelectedPackage(pkg);
		setSelectedVersion(pkg.versions && pkg.versions.length > 0 ? pkg.versions[0] : '');
		setInstallModalOpen(true);
	};

	useEffect(() => {
		setPage(1); // Reset to page 1 when pageSize changes
	}, [pageSize]);

	useEffect(() => {
		fetchPackages();
	}, [appId, page, pageSize, searchTerm]);

	// Reset page to 1 when search term changes
	useEffect(() => {
		setPage(1);
	}, [searchTerm]);

	if (!packagesData && !loading) return null;

	const packages = packagesData?.records || [];

	return (
		<div className="space-y-6">
			{/* Header */}
			<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
				<div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
					<div>
						<h2 className="text-xl font-semibold text-gray-900">Packages</h2>
						<p className="text-sm text-gray-600 mt-1">
							Installed packages and their configurations
						</p>
					</div>
					<div className="relative">
						<input
							type="text"
							placeholder="Search packages..."
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
				</div>
			</div>

			{/* Stats */}
			<div className="grid grid-cols-1 md:grid-cols-2 gap-6">
				<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
					<div className="flex items-center justify-between">
						<div>
							<p className="text-sm font-medium text-gray-600">Total Packages</p>
							<p className="text-2xl font-semibold text-gray-900 mt-1">{packagesData?.total_records || 0}</p>
						</div>
						<svg width="32" height="32" viewBox="0 0 32 32" fill="none">
							<path d="M16 4L6 10V16L16 22L26 16V10L16 4Z" className="fill-blue-100 stroke-blue-600" strokeWidth="2"/>
							<path d="M6 10L16 16L26 10" className="stroke-blue-600" strokeWidth="2"/>
							<path d="M16 16V22" className="stroke-blue-600" strokeWidth="2"/>
						</svg>
					</div>
				</div>

				<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
					<div className="flex items-center justify-between">
						<div>
							<p className="text-sm font-medium text-gray-600">Installed Packages</p>
							<p className="text-2xl font-semibold text-purple-600 mt-1">{packagesData?.installed_count || 0}</p>
						</div>
						<svg width="32" height="32" viewBox="0 0 32 32" fill="none">
							<path d="M6 16H26" className="stroke-purple-600" strokeWidth="2" strokeLinecap="round"/>
							<path d="M16 6V26" className="stroke-purple-600" strokeWidth="2" strokeLinecap="round"/>
							<circle cx="16" cy="16" r="4" className="fill-purple-100 stroke-purple-600" strokeWidth="2"/>
						</svg>
					</div>
				</div>
			</div>

			{/* Packages List */}
			{loading ? (
				<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
					<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
					<p className="text-sm text-gray-500 mt-2">Loading packages...</p>
				</div>
			) : packages.length > 0 ? (
				<div className="space-y-4">
					{packages.map((pkg, index) => {
						return (
							<div key={index} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
								<div className="p-6 border-b border-gray-200">
									<div className="flex items-center justify-between">
										<div className="flex items-center gap-3">
											<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
												<path d="M12 2L4 7V12L12 17L20 12V7L12 2Z" className="fill-blue-100 stroke-blue-600" strokeWidth="1.5"/>
												<path d="M4 7L12 12L20 7" className="stroke-blue-600" strokeWidth="1.5"/>
												<path d="M12 12V17" className="stroke-blue-600" strokeWidth="1.5"/>
											</svg>
											<div>
												<h3 className="text-lg font-semibold text-gray-900">{pkg.name}</h3>
												<p className="text-sm text-gray-600">
													Status: <span className={`font-medium ${
														pkg.status === 'Installed' ? 'text-green-600' : 'text-gray-600'
													}`}>{pkg.status}</span>
												</p>
											</div>
										</div>
										<div className="flex items-center gap-2">
											{pkg.installed_version && (
												<span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
													v{pkg.installed_version}
												</span>
											)}
											{pkg.status === 'Installed' ? (
												pkg.config_url && (
													<button
														onClick={() => {
															setConfigUrl(pkg.config_url);
															setConfigModalOpen(true);
														}}
														className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 hover:border-blue-300 transition-colors"
													>
														<svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor">
															<path d="M8 2.5A5.5 5.5 0 002.5 8a5.5 5.5 0 0011 0A5.5 5.5 0 008 2.5zM4.5 8a.75.75 0 01.75-.75h2.25V4.75a.75.75 0 011.5 0v2.5h2.25a.75.75 0 010 1.5H8.75v2.25a.75.75 0 01-1.5 0V8.5H5a.75.75 0 01-.75-.75z"/>
														</svg>
														Configure
													</button>
												)
											) : (
												<button
													onClick={() => openInstallModal(pkg)}
													className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-green-600 bg-green-50 border border-green-200 rounded-lg hover:bg-green-100 hover:border-green-300 transition-colors"
												>
													<svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor">
														<path d="M7.25 10.25V6.75a.75.75 0 011.5 0v3.5h3.5a.75.75 0 010 1.5h-3.5v3.5a.75.75 0 01-1.5 0v-3.5h-3.5a.75.75 0 010-1.5h3.5z"/>
													</svg>
													Install
												</button>
											)}
										</div>
									</div>
								</div>
								
								<div className="p-6 bg-gray-50">
									<h4 className="text-sm font-medium text-gray-700 mb-3">Package Details</h4>
									<div className="space-y-3">
										<div className="text-sm">
											<span className="text-gray-600">Package Name: </span>
											<span className="font-mono text-gray-900">{pkg.name}</span>
										</div>
										<div className="text-sm">
											<span className="text-gray-600">Installed Version: </span>
											<span className="text-gray-900">{pkg.installed_version}</span>
										</div>
										{pkg.versions && pkg.versions.length > 0 && (
											<div className="text-sm">
												<div className="text-gray-600 mb-2">Available Versions:</div>
												<div className="flex flex-wrap gap-1">
													{pkg.versions.map((version, vIndex) => (
														<span key={vIndex} className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-700">
															v{version}
														</span>
													))}
												</div>
											</div>
										)}
									</div>
								</div>
							</div>
						);
					})}

					{/* Pagination */}
					{totalRecords > 0 && (
						<div className="bg-gray-50 px-6 py-3 border-t border-gray-200 rounded-lg">
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
										Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, totalRecords)} of {totalRecords} packages
									</span>
									<div className="flex items-center gap-2">
										<label htmlFor="packagesPageSize" className="text-sm text-gray-600">
											Rows:
										</label>
										<select
											id="packagesPageSize"
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
			) : (
				<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
					<svg
						className="mx-auto h-12 w-12 text-gray-400"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							strokeLinecap="round"
							strokeLinejoin="round"
							strokeWidth={2}
							d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
						/>
					</svg>
					<h3 className="mt-2 text-sm font-medium text-gray-900">No packages found</h3>
					<p className="mt-1 text-sm text-gray-500">
						{searchTerm 
							? 'Try adjusting your search term'
							: 'No packages are currently installed'}
					</p>
				</div>
			)}

			{/* Configuration Modal */}
			{configModalOpen && (
				<div className="fixed inset-0 z-40 overflow-hidden" style={{ left: '102px', top: '56px' }}>
					{/* Background overlay */}
					<div 
						className="absolute inset-0 bg-gray-500 bg-opacity-75"
						onClick={() => setConfigModalOpen(false)}
					></div>

					{/* Modal panel */}
					<div className="absolute inset-0 flex flex-col bg-white shadow-xl">
						{/* Modal header */}
						<div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-white flex-shrink-0">
							<h3 className="text-lg font-semibold text-gray-900">
								Package Configuration
							</h3>
							<button
								onClick={() => setConfigModalOpen(false)}
								className="text-gray-400 hover:text-gray-500 p-2 hover:bg-gray-100 rounded-lg transition-colors"
							>
								<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
								</svg>
							</button>
						</div>

						{/* Modal body - Takes remaining space */}
						<div className="flex-1 overflow-hidden">
							<iframe
								src={configUrl}
								className="w-full h-full border-0"
								title="Package Configuration"
								allow="fullscreen"
							></iframe>
						</div>
					</div>
				</div>
			)}

			{/* Install Modal */}
			{installModalOpen && (
				<div className="fixed inset-0 z-50 overflow-y-auto">
					<div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
						{/* Background overlay */}
						<div 
							className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
							onClick={() => setInstallModalOpen(false)}
						></div>

						{/* Modal panel */}
						<div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
							{/* Modal header */}
							<div className="bg-white px-6 pt-6 pb-4">
								<div className="flex items-center justify-between">
									<h3 className="text-lg font-semibold text-gray-900">
										Install Package
									</h3>
									<button
										onClick={() => setInstallModalOpen(false)}
										className="text-gray-400 hover:text-gray-500"
									>
										<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
										</svg>
									</button>
								</div>
								<p className="mt-2 text-sm text-gray-600">
									Package: <span className="font-medium">{selectedPackage?.name}</span>
								</p>
							</div>

							{/* Modal body */}
							<div className="px-6 pb-4">
								<div className="space-y-4">
									<div>
										<label className="block text-sm font-medium text-gray-700 mb-2">
											Select Version
										</label>
										{selectedPackage?.versions && selectedPackage.versions.length > 0 ? (
											<select
												value={selectedVersion}
												onChange={(e) => setSelectedVersion(e.target.value)}
												className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
											>
												{selectedPackage.versions.map((version, index) => (
													<option key={index} value={version}>
														v{version}
													</option>
												))}
											</select>
										) : (
											<p className="text-sm text-gray-500">No versions available</p>
										)}
									</div>
								</div>
							</div>

							{/* Modal footer */}
							<div className="bg-gray-50 px-6 py-3 flex justify-end gap-3">
								<button
									onClick={() => setInstallModalOpen(false)}
									className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
								>
									Cancel
								</button>
								<button
									onClick={installPackage}
									disabled={!selectedVersion || installing}
									className="px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
								>
									{installing && (
										<div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
									)}
									{installing ? 'Installing...' : 'Install Package'}
								</button>
							</div>
						</div>
					</div>
				</div>
			)}
		</div>
	);
}