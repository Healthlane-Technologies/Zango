import React, { useState, useEffect } from 'react';
import GraphVisualization from './GraphVisualization';
import ModelDetailsModal from './ModelDetailsModal';

export default function DataModels({ data }) {
	const [searchTerm, setSearchTerm] = useState('');
	const [selectedModule, setSelectedModule] = useState('all');
	const [viewMode, setViewMode] = useState('list'); // 'list' or 'graph'
	const [selectedModel, setSelectedModel] = useState(null);
	const [showModelDetails, setShowModelDetails] = useState(false);

	if (!data) return null;

	// Extract all models from all modules
	const allModels = [];
	const moduleModelMap = {};
	
	data.modules?.forEach(module => {
		if (module.models && module.models.length > 0) {
			module.models.forEach(model => {
				const modelWithModule = { ...model, module: module.name };
				allModels.push(modelWithModule);
				
				if (!moduleModelMap[module.name]) {
					moduleModelMap[module.name] = [];
				}
				moduleModelMap[module.name].push(modelWithModule);
			});
		}
	});

	// Filter modules that have models
	const modulesWithModels = data.modules?.filter(module => module.models_count > 0) || [];
	
	// Filter based on search and selected module
	const filteredModels = allModels.filter(model => {
		const matchesSearch = model.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
							 model.module.toLowerCase().includes(searchTerm.toLowerCase());
		const matchesModule = selectedModule === 'all' || model.module === selectedModule;
		return matchesSearch && matchesModule;
	});

	const handleModelClick = (model) => {
		setSelectedModel(model);
		setShowModelDetails(true);
	};

	return (
		<div className="space-y-6">
			{/* Header */}
			<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
				<div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
					<div>
						<h2 className="text-xl font-semibold text-gray-900">Data Models</h2>
						<p className="text-sm text-gray-600 mt-1">
							Explore data models and their relationships
						</p>
					</div>
					<div className="flex flex-col sm:flex-row gap-3">
						{/* View Mode Toggle */}
						<div className="flex rounded-lg shadow-sm">
							<button
								onClick={() => setViewMode('list')}
								className={`px-4 py-2 text-sm font-medium rounded-l-lg border ${
									viewMode === 'list'
										? 'bg-blue-500 text-white border-blue-500'
										: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
								}`}
							>
								<svg className="w-4 h-4 inline-block mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
								</svg>
								List
							</button>
							<button
								onClick={() => setViewMode('graph')}
								className={`px-4 py-2 text-sm font-medium rounded-r-lg border ${
									viewMode === 'graph'
										? 'bg-blue-500 text-white border-blue-500'
										: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
								}`}
							>
								<svg className="w-4 h-4 inline-block mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
								</svg>
								Graph
							</button>
						</div>
						
						{/* Search */}
						<div className="relative">
							<input
								type="text"
								placeholder="Search models..."
								value={searchTerm}
								onChange={(e) => setSearchTerm(e.target.value)}
								disabled={viewMode === 'graph'}
								className={`pl-10 pr-4 py-2 border rounded-lg w-full sm:w-64 ${
									viewMode === 'graph'
										? 'border-gray-200 bg-gray-100 text-gray-400 cursor-not-allowed'
										: 'border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
								}`}
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
						
						{/* Module Filter */}
						<select
							value={selectedModule}
							onChange={(e) => setSelectedModule(e.target.value)}
							disabled={viewMode === 'graph'}
							className={`px-4 py-2 border rounded-lg ${
								viewMode === 'graph'
									? 'border-gray-200 bg-gray-100 text-gray-400 cursor-not-allowed'
									: 'border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
							}`}
						>
							<option value="all">All Modules</option>
							{modulesWithModels.map((module) => (
								<option key={module.name} value={module.name}>
									{module.name}
								</option>
							))}
						</select>
					</div>
				</div>
			</div>

			{/* Content based on view mode */}
			{viewMode === 'list' ? (
				<div className="space-y-6">
					{/* Stats */}
					<div className="grid grid-cols-1 md:grid-cols-3 gap-6">
						<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
							<div className="flex items-center justify-between">
								<div>
									<p className="text-sm font-medium text-gray-600">Total Models</p>
									<p className="text-2xl font-semibold text-gray-900 mt-1">{allModels.length}</p>
								</div>
								<svg width="32" height="32" viewBox="0 0 32 32" fill="none">
									<path d="M16 4C19.866 4 23 5.79086 23 8V24C23 26.2091 19.866 28 16 28C12.134 28 9 26.2091 9 24V8C9 5.79086 12.134 4 16 4Z" className="fill-blue-100 stroke-blue-600" strokeWidth="2"/>
								</svg>
							</div>
						</div>

						<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
							<div className="flex items-center justify-between">
								<div>
									<p className="text-sm font-medium text-gray-600">Relationships</p>
									<p className="text-2xl font-semibold text-purple-600 mt-1">
										{allModels.reduce((sum, model) => sum + model.relationships.length, 0)}
									</p>
								</div>
								<svg width="32" height="32" viewBox="0 0 32 32" fill="none">
									<circle cx="10" cy="10" r="4" className="fill-purple-100 stroke-purple-600" strokeWidth="2"/>
									<circle cx="22" cy="22" r="4" className="fill-purple-100 stroke-purple-600" strokeWidth="2"/>
									<path d="M13 13L19 19" className="stroke-purple-600" strokeWidth="2"/>
								</svg>
							</div>
						</div>

						<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
							<div className="flex items-center justify-between">
								<div>
									<p className="text-sm font-medium text-gray-600">Modules with Models</p>
									<p className="text-2xl font-semibold text-green-600 mt-1">{modulesWithModels.length}</p>
								</div>
								<svg width="32" height="32" viewBox="0 0 32 32" fill="none">
									<rect x="6" y="6" width="8" height="8" rx="1" className="fill-green-100 stroke-green-600" strokeWidth="2"/>
									<rect x="18" y="6" width="8" height="8" rx="1" className="fill-green-100 stroke-green-600" strokeWidth="2"/>
									<rect x="6" y="18" width="8" height="8" rx="1" className="fill-green-100 stroke-green-600" strokeWidth="2"/>
								</svg>
							</div>
						</div>
					</div>

					{/* Models List */}
					{filteredModels.length > 0 ? (
						<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
							{Object.entries(
								filteredModels.reduce((acc, model) => {
									if (!acc[model.module]) acc[model.module] = [];
									acc[model.module].push(model);
									return acc;
								}, {})
							).map(([moduleName, models]) => (
								<div key={moduleName} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
									<h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
										<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
											<rect x="3" y="3" width="14" height="14" rx="2" className="stroke-gray-600" strokeWidth="1.5" fill="none"/>
											<rect x="6" y="6" width="8" height="2" className="fill-gray-600"/>
											<rect x="6" y="10" width="5" height="2" className="fill-gray-400"/>
										</svg>
										{moduleName}
									</h3>
									<div className="space-y-3">
										{models.map((model, index) => (
											<div
												key={index}
												className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors cursor-pointer"
												onClick={() => handleModelClick(model)}
											>
												<div className="flex items-start justify-between mb-2">
													<h4 className="font-medium text-gray-900">{model.name}</h4>
													<div className="flex items-center gap-2">
														{model.relationships.length > 0 && (
															<span className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded">
																{model.relationships.length} relation{model.relationships.length !== 1 ? 's' : ''}
															</span>
														)}
													</div>
												</div>
												<div className="grid grid-cols-2 gap-2 text-sm">
													<div className="text-gray-600">
														Fields: <span className="font-medium text-gray-900">{model.fields.length}</span>
													</div>
													{model.meta.db_table && (
														<div className="text-gray-600">
															Table: <span className="font-mono text-xs text-gray-900">{model.meta.db_table}</span>
														</div>
													)}
												</div>
											</div>
										))}
									</div>
								</div>
							))}
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
									d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
								/>
							</svg>
							<h3 className="mt-2 text-sm font-medium text-gray-900">No data models found</h3>
							<p className="mt-1 text-sm text-gray-500">
								{searchTerm || selectedModule !== 'all'
									? 'Try adjusting your filters'
									: 'No models were detected in the codebase'}
							</p>
						</div>
					)}
				</div>
			) : (
				<GraphVisualization
					dotDiagram={data?.dot_diagram}
					models={filteredModels}
					onModelClick={handleModelClick}
				/>
			)}

			{/* Model Details Modal */}
			{showModelDetails && selectedModel && (
				<ModelDetailsModal
					model={selectedModel}
					onClose={() => {
						setShowModelDetails(false);
						setSelectedModel(null);
					}}
				/>
			)}
		</div>
	);
}