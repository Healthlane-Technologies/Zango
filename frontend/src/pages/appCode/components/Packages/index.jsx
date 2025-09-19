import React, { useState } from 'react';

export default function Packages({ data }) {
	const [searchTerm, setSearchTerm] = useState('');

	if (!data) return null;

	const packageRoutes = data.package_routes || [];
	
	// Extract unique packages
	const uniquePackages = [...new Set(packageRoutes.map(route => route.package))].sort();
	
	// Filter packages based on search
	const filteredPackages = uniquePackages.filter(pkg => 
		pkg.toLowerCase().includes(searchTerm.toLowerCase())
	);

	// Get routes for a specific package
	const getPackageRoutes = (packageName) => {
		return packageRoutes.filter(route => route.package === packageName);
	};

	return (
		<div className="space-y-6">
			{/* Header */}
			<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
				<div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
					<div>
						<h2 className="text-xl font-semibold text-gray-900">Packages</h2>
						<p className="text-sm text-gray-600 mt-1">
							Installed packages and their route configurations
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
			<div className="grid grid-cols-1 md:grid-cols-3 gap-6">
				<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
					<div className="flex items-center justify-between">
						<div>
							<p className="text-sm font-medium text-gray-600">Total Packages</p>
							<p className="text-2xl font-semibold text-gray-900 mt-1">{data.total_packages || 0}</p>
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
							<p className="text-sm font-medium text-gray-600">Package Routes</p>
							<p className="text-2xl font-semibold text-purple-600 mt-1">{packageRoutes.length}</p>
						</div>
						<svg width="32" height="32" viewBox="0 0 32 32" fill="none">
							<path d="M6 16H26" className="stroke-purple-600" strokeWidth="2" strokeLinecap="round"/>
							<path d="M16 6V26" className="stroke-purple-600" strokeWidth="2" strokeLinecap="round"/>
							<circle cx="16" cy="16" r="4" className="fill-purple-100 stroke-purple-600" strokeWidth="2"/>
						</svg>
					</div>
				</div>

				<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
					<div className="flex items-center justify-between">
						<div>
							<p className="text-sm font-medium text-gray-600">Avg Routes/Package</p>
							<p className="text-2xl font-semibold text-green-600 mt-1">
								{uniquePackages.length > 0 
									? (packageRoutes.length / uniquePackages.length).toFixed(1)
									: '0'
								}
							</p>
						</div>
						<svg width="32" height="32" viewBox="0 0 32 32" fill="none">
							<rect x="8" y="20" width="4" height="8" className="fill-green-100 stroke-green-600" strokeWidth="1.5"/>
							<rect x="14" y="16" width="4" height="12" className="fill-green-100 stroke-green-600" strokeWidth="1.5"/>
							<rect x="20" y="12" width="4" height="16" className="fill-green-100 stroke-green-600" strokeWidth="1.5"/>
						</svg>
					</div>
				</div>
			</div>

			{/* Packages List */}
			{filteredPackages.length > 0 ? (
				<div className="space-y-4">
					{filteredPackages.map((packageName, index) => {
						const routes = getPackageRoutes(packageName);
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
												<h3 className="text-lg font-semibold text-gray-900">{packageName}</h3>
												<p className="text-sm text-gray-600">
													{routes.length} route{routes.length !== 1 ? 's' : ''} configured
												</p>
											</div>
										</div>
									</div>
								</div>
								
								<div className="p-6 bg-gray-50">
									<h4 className="text-sm font-medium text-gray-700 mb-3">Route Configuration</h4>
									<div className="space-y-2">
										{routes.map((route, routeIndex) => (
											<div key={routeIndex} className="flex items-center gap-4 text-sm">
												<code className="font-mono bg-white px-2 py-1 rounded border border-gray-200">
													{route.re_path}
												</code>
												<span className="text-gray-500">→</span>
												<span className="text-gray-700">{route.url}</span>
											</div>
										))}
									</div>
								</div>
							</div>
						);
					})}
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
							: 'No package routes are configured in settings.json'}
					</p>
				</div>
			)}
		</div>
	);
}