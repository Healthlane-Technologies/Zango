import React from 'react';

export default function CodeSummary({ data }) {
	if (!data) return null;

	const stats = [
		{
			label: 'Total Modules',
			value: data.total_modules || 0,
			icon: (
				<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
					<rect x="3" y="3" width="7" height="7" rx="1" stroke="#346BD4" strokeWidth="2"/>
					<rect x="14" y="3" width="7" height="7" rx="1" stroke="#346BD4" strokeWidth="2"/>
					<rect x="3" y="14" width="7" height="7" rx="1" stroke="#346BD4" strokeWidth="2"/>
					<rect x="14" y="14" width="7" height="7" rx="1" stroke="#346BD4" strokeWidth="2"/>
				</svg>
			),
			bgColor: 'bg-blue-50',
		},
		{
			label: 'Total Packages',
			value: data.total_packages || 0,
			icon: (
				<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
					<path d="M12 2L4 7V12L12 17L20 12V7L12 2Z" stroke="#16A34A" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
					<path d="M12 17V12" stroke="#16A34A" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
					<path d="M4 7L12 12L20 7" stroke="#16A34A" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
				</svg>
			),
			bgColor: 'bg-green-50',
		},
		{
			label: 'Total Routes',
			value: data.total_routes || 0,
			icon: (
				<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
					<path d="M3 12H21" stroke="#EAB308" strokeWidth="2" strokeLinecap="round"/>
					<path d="M12 3V21" stroke="#EAB308" strokeWidth="2" strokeLinecap="round"/>
					<circle cx="12" cy="12" r="3" stroke="#EAB308" strokeWidth="2"/>
				</svg>
			),
			bgColor: 'bg-yellow-50',
		},
		{
			label: 'App Version',
			value: data.version || 'N/A',
			icon: (
				<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
					<path d="M12 2V12L20 8V18C20 19.1046 19.1046 20 18 20H6C4.89543 20 4 19.1046 4 18V8L12 2Z" stroke="#8B5CF6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
				</svg>
			),
			bgColor: 'bg-purple-50',
		},
	];

	return (
		<div className="space-y-6">
			{/* Stats Grid */}
			<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
				{stats.map((stat, index) => (
					<div key={index} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
						<div className="flex items-center justify-between">
							<div>
								<p className="text-sm font-medium text-gray-600">{stat.label}</p>
								<p className="text-2xl font-semibold text-gray-900 mt-1">{stat.value}</p>
							</div>
							<div className={`p-3 rounded-lg ${stat.bgColor}`}>
								{stat.icon}
							</div>
						</div>
					</div>
				))}
			</div>

			{/* Workspace Info */}
			<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
				<h3 className="text-lg font-semibold text-gray-900 mb-4">Workspace Information</h3>
				<div className="space-y-3">
					<div className="flex items-center justify-between">
						<span className="text-sm text-gray-600">App Name</span>
						<span className="text-sm font-medium text-gray-900">{data.app_name}</span>
					</div>
					<div className="flex items-center justify-between">
						<span className="text-sm text-gray-600">Workspace Path</span>
						<span className="text-sm font-mono text-gray-900">{data.workspace_path}</span>
					</div>
					<div className="flex items-center justify-between">
						<span className="text-sm text-gray-600">Settings File</span>
						<span className={`text-sm font-medium ${data.settings_file_exists ? 'text-green-600' : 'text-red-600'}`}>
							{data.settings_file_exists ? 'Found' : 'Not Found'}
						</span>
					</div>
					{data.last_modified && (
						<div className="flex items-center justify-between">
							<span className="text-sm text-gray-600">Last Modified</span>
							<span className="text-sm text-gray-900">
								{new Date(data.last_modified).toLocaleString()}
							</span>
						</div>
					)}
				</div>
			</div>

			{/* Modules Overview */}
			<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
				<h3 className="text-lg font-semibold text-gray-900 mb-4">Modules Overview</h3>
				<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
					{data.modules?.slice(0, 6).map((module, index) => (
						<div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
							<div className="flex items-center gap-2">
								<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
									<rect x="2" y="2" width="12" height="12" rx="2" stroke="#6B7280" strokeWidth="1.5"/>
								</svg>
								<span className="text-sm font-medium text-gray-900">{module.name}</span>
							</div>
							<div className="flex items-center gap-2 text-xs text-gray-500">
								{module.has_urls && (
									<span className="px-2 py-1 bg-blue-100 text-blue-700 rounded">URLs</span>
								)}
								{module.has_policies && (
									<span className="px-2 py-1 bg-green-100 text-green-700 rounded">Policies</span>
								)}
							</div>
						</div>
					))}
				</div>
				{data.modules?.length > 6 && (
					<p className="text-sm text-gray-500 mt-4">
						And {data.modules.length - 6} more modules...
					</p>
				)}
			</div>
		</div>
	);
}