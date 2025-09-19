import React, { useState } from 'react';

export default function Routes({ data }) {
	const [activeTab, setActiveTab] = useState('app');
	const [searchTerm, setSearchTerm] = useState('');
	const [expandedRoutes, setExpandedRoutes] = useState({});

	if (!data) return null;

	const appRoutes = data.app_routes || [];
	const packageRoutes = data.package_routes || [];

	// Filter routes based on search
	const filterRoutes = (routes) => {
		return routes.filter(route => {
			const searchLower = searchTerm.toLowerCase();
			return (
				route.re_path?.toLowerCase().includes(searchLower) ||
				route.module?.toLowerCase().includes(searchLower) ||
				route.package?.toLowerCase().includes(searchLower) ||
				route.url?.toLowerCase().includes(searchLower)
			);
		});
	};

	const filteredAppRoutes = filterRoutes(appRoutes);
	const filteredPackageRoutes = filterRoutes(packageRoutes);

	// Get sub-routes for a given route from the route tree
	const getSubRoutes = (route) => {
		if (!data.route_tree || !data.route_tree.children) return [];
		
		// Find the matching route in the tree
		const findRouteInTree = (node) => {
			if (node.pattern === route.re_path) {
				return node.children || [];
			}
			if (node.children) {
				for (let child of node.children) {
					const result = findRouteInTree(child);
					if (result) return result;
				}
			}
			return null;
		};
		
		for (let child of data.route_tree.children) {
			const subRoutes = findRouteInTree(child);
			if (subRoutes) return subRoutes;
		}
		
		return [];
	};

	// Toggle expanded state for a route
	const toggleRouteExpansion = (routeKey) => {
		setExpandedRoutes(prev => ({
			...prev,
			[routeKey]: !prev[routeKey]
		}));
	};

	return (
		<div className="space-y-6">
			{/* Header */}
			<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
				<div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
					<div>
						<h2 className="text-xl font-semibold text-gray-900">Routes Configuration</h2>
						<p className="text-sm text-gray-600 mt-1">
							Application and package routes defined in settings.json
						</p>
					</div>
					<div className="relative">
						<input
							type="text"
							placeholder="Search routes..."
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

			{/* Tabs */}
			<div className="bg-white rounded-lg shadow-sm border border-gray-200">
				<div className="border-b border-gray-200">
					<nav className="flex -mb-px">
						<button
							onClick={() => setActiveTab('app')}
							className={`py-3 px-6 text-sm font-medium border-b-2 transition-colors ${
								activeTab === 'app'
									? 'border-blue-500 text-blue-600'
									: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
							}`}
						>
							App Routes ({filteredAppRoutes.length})
						</button>
						<button
							onClick={() => setActiveTab('package')}
							className={`py-3 px-6 text-sm font-medium border-b-2 transition-colors ${
								activeTab === 'package'
									? 'border-blue-500 text-blue-600'
									: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
							}`}
						>
							Package Routes ({filteredPackageRoutes.length})
						</button>
					</nav>
				</div>

				{/* Content */}
				<div className="p-6">
					{activeTab === 'app' && (
						<div className="space-y-4">
							{filteredAppRoutes.length > 0 ? (
								<div className="overflow-x-auto">
									<table className="min-w-full divide-y divide-gray-200">
										<thead>
											<tr>
												<th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
													Path Pattern
												</th>
												<th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
													Module
												</th>
												<th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
													URL File
												</th>
												<th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
													View
												</th>
											</tr>
										</thead>
										<tbody className="bg-white divide-y divide-gray-200">
											{filteredAppRoutes.map((route, index) => {
												const subRoutes = getSubRoutes(route);
												const routeKey = `app-${index}`;
												const isExpanded = expandedRoutes[routeKey];
												
												return (
													<React.Fragment key={index}>
														<tr 
															className={`hover:bg-gray-50 cursor-pointer ${isExpanded ? 'bg-gray-50' : ''}`}
															onClick={() => subRoutes.length > 0 && toggleRouteExpansion(routeKey)}
														>
															<td className="px-4 py-3 whitespace-nowrap">
																<div className="flex items-center gap-2">
																	{subRoutes.length > 0 && (
																		<svg 
																			className={`w-4 h-4 text-gray-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`} 
																			fill="none" 
																			viewBox="0 0 24 24" 
																			stroke="currentColor"
																		>
																			<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
																		</svg>
																	)}
																	<code className="text-sm font-mono bg-gray-100 px-2 py-1 rounded">
																		{route.re_path}
																	</code>
																</div>
															</td>
															<td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
																{route.module}
															</td>
															<td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
																{route.url}
															</td>
															<td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
																—
															</td>
														</tr>
														
														{isExpanded && subRoutes.length > 0 && (
															<tr>
																<td colSpan="4" className="p-0">
																	<div className="bg-blue-50 border-t border-b border-blue-100">
																		<div className="px-4 py-3">
																			<h5 className="text-sm font-medium text-blue-900 mb-3">Sub Routes</h5>
																			<div className="space-y-2">
																				{subRoutes.map((subRoute, subIndex) => (
																					<div key={subIndex} className="bg-white rounded-lg border border-blue-200 p-3">
																						<div className="grid grid-cols-2 gap-4">
																							<div>
																								<span className="text-xs text-gray-500 block mb-1">Pattern</span>
																								<code className="text-sm font-mono bg-gray-50 px-2 py-1 rounded">
																									{subRoute.pattern}
																								</code>
																							</div>
																							<div>
																								<span className="text-xs text-gray-500 block mb-1">View</span>
																								<code className="text-sm text-gray-700">
																									{subRoute.view || 'No view specified'}
																								</code>
																							</div>
																						</div>
																					</div>
																				))}
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
							) : (
								<div className="text-center py-12">
									<p className="text-sm text-gray-500">No app routes found</p>
								</div>
							)}
						</div>
					)}

					{activeTab === 'package' && (
						<div className="space-y-4">
							{filteredPackageRoutes.length > 0 ? (
								<div className="overflow-x-auto">
									<table className="min-w-full divide-y divide-gray-200">
										<thead>
											<tr>
												<th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
													Path Pattern
												</th>
												<th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
													Package
												</th>
												<th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
													URL File
												</th>
												<th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
													View
												</th>
											</tr>
										</thead>
										<tbody className="bg-white divide-y divide-gray-200">
											{filteredPackageRoutes.map((route, index) => {
												const subRoutes = getSubRoutes(route);
												const routeKey = `pkg-${index}`;
												const isExpanded = expandedRoutes[routeKey];
												
												return (
													<React.Fragment key={index}>
														<tr 
															className={`hover:bg-gray-50 cursor-pointer ${isExpanded ? 'bg-gray-50' : ''}`}
															onClick={() => subRoutes.length > 0 && toggleRouteExpansion(routeKey)}
														>
															<td className="px-4 py-3 whitespace-nowrap">
																<div className="flex items-center gap-2">
																	{subRoutes.length > 0 && (
																		<svg 
																			className={`w-4 h-4 text-gray-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`} 
																			fill="none" 
																			viewBox="0 0 24 24" 
																			stroke="currentColor"
																		>
																			<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
																		</svg>
																	)}
																	<code className="text-sm font-mono bg-gray-100 px-2 py-1 rounded">
																		{route.re_path}
																	</code>
																</div>
															</td>
															<td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
																{route.package}
															</td>
															<td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
																{route.url}
															</td>
															<td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
																—
															</td>
														</tr>
														
														{isExpanded && subRoutes.length > 0 && (
															<tr>
																<td colSpan="4" className="p-0">
																	<div className="bg-purple-50 border-t border-b border-purple-100">
																		<div className="px-4 py-3">
																			<h5 className="text-sm font-medium text-purple-900 mb-3">Sub Routes</h5>
																			<div className="space-y-2">
																				{subRoutes.map((subRoute, subIndex) => (
																					<div key={subIndex} className="bg-white rounded-lg border border-purple-200 p-3">
																						<div className="grid grid-cols-2 gap-4">
																							<div>
																								<span className="text-xs text-gray-500 block mb-1">Pattern</span>
																								<code className="text-sm font-mono bg-gray-50 px-2 py-1 rounded">
																									{subRoute.pattern}
																								</code>
																							</div>
																							<div>
																								<span className="text-xs text-gray-500 block mb-1">View</span>
																								<code className="text-sm text-gray-700">
																									{subRoute.view || 'No view specified'}
																								</code>
																							</div>
																						</div>
																					</div>
																				))}
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
							) : (
								<div className="text-center py-12">
									<p className="text-sm text-gray-500">No package routes found</p>
								</div>
							)}
						</div>
					)}
				</div>
			</div>
		</div>
	);
}