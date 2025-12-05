import React from 'react';

export default function ModelDetailsModal({ model, onClose }) {
	// Get field type icon
	const getFieldIcon = (type) => {
		const baseClass = "w-4 h-4";
		
		switch(type) {
			case 'CharField':
			case 'TextField':
				return <svg className={baseClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
				</svg>;
			
			case 'IntegerField':
			case 'FloatField':
			case 'DecimalField':
				return <svg className={baseClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
				</svg>;
			
			case 'BooleanField':
				return <svg className={baseClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
				</svg>;
			
			case 'DateField':
			case 'DateTimeField':
				return <svg className={baseClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
				</svg>;
			
			case 'ForeignKey':
			case 'OneToOneField':
			case 'ManyToManyField':
				return <svg className={baseClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
				</svg>;
			
			default:
				return <svg className={baseClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
				</svg>;
		}
	};

	// Get field type color
	const getFieldTypeColor = (type) => {
		const typeColors = {
			'CharField': 'bg-blue-100 text-blue-700',
			'TextField': 'bg-blue-100 text-blue-800',
			'IntegerField': 'bg-green-100 text-green-700',
			'FloatField': 'bg-green-100 text-green-800',
			'DecimalField': 'bg-green-100 text-green-900',
			'BooleanField': 'bg-purple-100 text-purple-700',
			'DateField': 'bg-orange-100 text-orange-700',
			'DateTimeField': 'bg-orange-100 text-orange-800',
			'ForeignKey': 'bg-red-100 text-red-700',
			'OneToOneField': 'bg-red-100 text-red-800',
			'ManyToManyField': 'bg-red-100 text-red-900',
			'JSONField': 'bg-indigo-100 text-indigo-700',
			'UUIDField': 'bg-pink-100 text-pink-700'
		};
		return typeColors[type] || 'bg-gray-100 text-gray-700';
	};

	return (
		<div className="fixed inset-0 z-50 overflow-y-auto">
			<div className="flex items-center justify-center min-h-screen px-4">
				{/* Backdrop */}
				<div 
					className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
					onClick={onClose}
				/>

				{/* Modal */}
				<div className="relative bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
					{/* Header */}
					<div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white px-6 py-4">
						<div className="flex items-center justify-between">
							<div>
								<h2 className="text-2xl font-bold">{model.name}</h2>
								<p className="text-sm opacity-90 mt-1">Module: {model.module}</p>
							</div>
							<button
								onClick={onClose}
								className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition-colors"
							>
								<svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
								</svg>
							</button>
						</div>
					</div>

					{/* Content */}
					<div className="overflow-y-auto max-h-[calc(90vh-120px)]">
						{/* Meta Information */}
						{(model.meta.db_table || model.meta.verbose_name) && (
							<div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
								<h3 className="text-sm font-semibold text-gray-700 mb-2">Meta Information</h3>
								<div className="grid grid-cols-2 gap-4">
									{model.meta.db_table && (
										<div>
											<span className="text-sm text-gray-600">Database Table:</span>
											<code className="ml-2 text-sm font-mono bg-gray-200 px-2 py-1 rounded">
												{model.meta.db_table}
											</code>
										</div>
									)}
									{model.meta.verbose_name && (
										<div>
											<span className="text-sm text-gray-600">Verbose Name:</span>
											<span className="ml-2 text-sm font-medium text-gray-900">
												{model.meta.verbose_name}
											</span>
										</div>
									)}
								</div>
							</div>
						)}

						{/* Fields */}
						<div className="px-6 py-4">
							<h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
								<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
								</svg>
								Fields ({model.fields.length})
							</h3>
							<div className="space-y-3">
								{model.fields.map((field, index) => (
									<div key={index} className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors">
										<div className="flex items-start justify-between">
											<div className="flex items-center gap-3">
												<div className={`p-2 rounded-lg ${getFieldTypeColor(field.type).split(' ')[0]}`}>
													{getFieldIcon(field.type)}
												</div>
												<div>
													<h4 className="font-medium text-gray-900">{field.name}</h4>
													<span className={`inline-block mt-1 text-xs px-2 py-1 rounded-full ${getFieldTypeColor(field.type)}`}>
														{field.type}
													</span>
												</div>
											</div>
										</div>
										{Object.keys(field.attributes || {}).length > 0 && (
											<div className="mt-3 pt-3 border-t border-gray-100">
												<div className="flex flex-wrap gap-2">
													{Object.entries(field.attributes).map(([key, value]) => (
														<span key={key} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
															{key}: {typeof value === 'boolean' ? value.toString() : value}
														</span>
													))}
												</div>
											</div>
										)}
									</div>
								))}
							</div>
						</div>

						{/* Relationships */}
						{model.relationships.length > 0 && (
							<div className="px-6 py-4 border-t border-gray-200">
								<h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
									<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
									</svg>
									Relationships ({model.relationships.length})
								</h3>
								<div className="space-y-3">
									{model.relationships.map((rel, index) => (
										<div key={index} className="border border-red-200 rounded-lg p-4 bg-red-50">
											<div className="flex items-start justify-between">
												<div className="flex items-center gap-3">
													<div className="p-2 rounded-lg bg-red-100">
														{getFieldIcon(rel.type)}
													</div>
													<div>
														<h4 className="font-medium text-gray-900">{rel.name}</h4>
														<div className="flex items-center gap-2 mt-1">
															<span className={`inline-block text-xs px-2 py-1 rounded-full ${getFieldTypeColor(rel.type)}`}>
																{rel.type}
															</span>
															<span className="text-sm text-gray-600">→</span>
															<span className="text-sm font-medium text-gray-900">
																{rel.related_model}
															</span>
														</div>
													</div>
												</div>
											</div>
											{Object.keys(rel.attributes || {}).length > 0 && (
												<div className="mt-3 pt-3 border-t border-red-100">
													<div className="flex flex-wrap gap-2">
														{Object.entries(rel.attributes).map(([key, value]) => (
															<span key={key} className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded">
																{key}: {typeof value === 'boolean' ? value.toString() : value}
															</span>
														))}
													</div>
												</div>
											)}
										</div>
									))}
								</div>
							</div>
						)}
					</div>

					{/* Footer */}
					<div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
						<div className="flex items-center justify-between">
							<div className="text-sm text-gray-600">
								Total: {model.fields.length} fields, {model.relationships.length} relationships
							</div>
							<button
								onClick={onClose}
								className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
							>
								Close
							</button>
						</div>
					</div>
				</div>
			</div>
		</div>
	);
}