import React, { useEffect, useRef, useState } from 'react';

export default function TableVisualization({ models, onModelClick }) {
	const containerRef = useRef(null);
	const [positions, setPositions] = useState({});
	const [dragging, setDragging] = useState(null);
	const [offset, setOffset] = useState({ x: 0, y: 0 });

	// Initialize positions for models
	useEffect(() => {
		const newPositions = {};
		const cols = Math.ceil(Math.sqrt(models.length));
		const spacing = 320;
		const startX = 50;
		const startY = 50;

		models.forEach((model, index) => {
			const row = Math.floor(index / cols);
			const col = index % cols;
			newPositions[`${model.module}.${model.name}`] = {
				x: startX + col * spacing,
				y: startY + row * spacing
			};
		});

		setPositions(newPositions);
	}, [models]);

	// Handle drag start
	const handleMouseDown = (e, modelKey) => {
		const rect = containerRef.current.getBoundingClientRect();
		setDragging(modelKey);
		setOffset({
			x: e.clientX - positions[modelKey].x - rect.left,
			y: e.clientY - positions[modelKey].y - rect.top
		});
		e.preventDefault();
	};

	// Handle drag
	useEffect(() => {
		const handleMouseMove = (e) => {
			if (dragging && containerRef.current) {
				const rect = containerRef.current.getBoundingClientRect();
				setPositions(prev => ({
					...prev,
					[dragging]: {
						x: e.clientX - rect.left - offset.x,
						y: e.clientY - rect.top - offset.y
					}
				}));
			}
		};

		const handleMouseUp = () => {
			setDragging(null);
		};

		if (dragging) {
			document.addEventListener('mousemove', handleMouseMove);
			document.addEventListener('mouseup', handleMouseUp);
			return () => {
				document.removeEventListener('mousemove', handleMouseMove);
				document.removeEventListener('mouseup', handleMouseUp);
			};
		}
	}, [dragging, offset]);

	// Get field type color
	const getFieldTypeColor = (type) => {
		const typeColors = {
			'CharField': 'text-blue-600',
			'TextField': 'text-blue-700',
			'IntegerField': 'text-green-600',
			'FloatField': 'text-green-700',
			'DecimalField': 'text-green-800',
			'BooleanField': 'text-purple-600',
			'DateField': 'text-orange-600',
			'DateTimeField': 'text-orange-700',
			'ForeignKey': 'text-red-600',
			'OneToOneField': 'text-red-700',
			'ManyToManyField': 'text-red-800',
			'ZForeignKey': 'text-red-600',
			'ZOneToOneField': 'text-red-700',
			'ZManyToManyField': 'text-red-800',
			'JSONField': 'text-indigo-600',
			'UUIDField': 'text-pink-600',
			'EmailField': 'text-cyan-600',
			'PhoneNumberField': 'text-teal-600',
			'ZFileField': 'text-amber-600'
		};
		return typeColors[type] || 'text-gray-600';
	};

	// Draw relationships
	const drawRelationships = () => {
		const lines = [];
		
		models.forEach(model => {
			const sourceKey = `${model.module}.${model.name}`;
			const sourcePos = positions[sourceKey];
			
			if (!sourcePos) return;
			
			model.relationships.forEach(rel => {
				// Find target model
				const targetModel = models.find(m => 
					m.name === rel.related_model || 
					`${m.module}.${m.name}` === rel.related_model
				);
				
				if (targetModel) {
					const targetKey = `${targetModel.module}.${targetModel.name}`;
					const targetPos = positions[targetKey];
					
					if (targetPos) {
						const lineKey = `${sourceKey}-${targetKey}-${rel.name}`;
						
						// Calculate connection points (from right side of source to left side of target)
						const sourceX = sourcePos.x + 280; // Approximate table width
						const sourceY = sourcePos.y + 50; // Approximate header height
						const targetX = targetPos.x;
						const targetY = targetPos.y + 50;
						
						// Create curved path
						const midX = (sourceX + targetX) / 2;
						
						lines.push(
							<g key={lineKey}>
								<path
									d={`M ${sourceX} ${sourceY} C ${midX} ${sourceY}, ${midX} ${targetY}, ${targetX} ${targetY}`}
									fill="none"
									stroke="#9CA3AF"
									strokeWidth="2"
									strokeDasharray="5,5"
								/>
								<circle cx={targetX} cy={targetY} r="4" fill="#9CA3AF" />
								<text
									x={midX}
									y={(sourceY + targetY) / 2}
									textAnchor="middle"
									className="text-xs fill-gray-500"
									dy="-5"
								>
									{rel.name} ({rel.type})
								</text>
							</g>
						);
					}
				}
			});
		});
		
		return lines;
	};

	return (
		<div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
			<div className="p-4 border-b border-gray-200 bg-gray-50">
				<p className="text-sm text-gray-600">
					Drag tables to rearrange. Click on a table to view details.
				</p>
			</div>
			<div 
				ref={containerRef}
				className="relative overflow-auto bg-gray-50"
				style={{ height: '600px' }}
			>
				{/* SVG for relationship lines */}
				<svg
					className="absolute inset-0 pointer-events-none"
					style={{ width: '100%', height: '100%' }}
				>
					{drawRelationships()}
				</svg>

				{/* Tables */}
				{models.map(model => {
					const modelKey = `${model.module}.${model.name}`;
					const position = positions[modelKey];
					
					if (!position) return null;
					
					return (
						<div
							key={modelKey}
							className={`absolute bg-white border-2 rounded-lg shadow-lg cursor-move ${
								dragging === modelKey ? 'border-blue-500 shadow-xl' : 'border-gray-300'
							}`}
							style={{
								left: `${position.x}px`,
								top: `${position.y}px`,
								width: '280px'
							}}
							onMouseDown={(e) => handleMouseDown(e, modelKey)}
						>
							{/* Table Header */}
							<div 
								className="bg-gradient-to-r from-blue-500 to-blue-600 text-white px-4 py-3 rounded-t-md cursor-pointer"
								onClick={() => onModelClick(model)}
							>
								<h3 className="font-semibold text-sm">{model.name}</h3>
								<p className="text-xs opacity-80">{model.module}</p>
							</div>

							{/* Fields */}
							<div className="max-h-[200px] overflow-y-auto">
								{/* Regular Fields */}
								{model.fields.slice(0, 5).map((field, index) => (
									<div key={index} className="px-4 py-2 border-b border-gray-100 hover:bg-gray-50">
										<div className="flex items-center justify-between">
											<span className="text-sm font-medium text-gray-900">{field.name}</span>
											<span className={`text-xs ${getFieldTypeColor(field.type)}`}>
												{field.type}
											</span>
										</div>
										{field.attributes?.max_length && (
											<span className="text-xs text-gray-500">
												max_length: {field.attributes.max_length}
											</span>
										)}
									</div>
								))}
								
								{model.fields.length > 5 && (
									<div className="px-4 py-2 text-xs text-gray-500 text-center">
										... and {model.fields.length - 5} more fields
									</div>
								)}

								{/* Relationships */}
								{model.relationships.length > 0 && (
									<>
										<div className="px-4 py-1 bg-gray-100 text-xs font-semibold text-gray-700">
											Relationships
										</div>
										{model.relationships.map((rel, index) => (
											<div key={index} className="px-4 py-2 border-b border-gray-100 hover:bg-red-50">
												<div className="flex items-center justify-between">
													<span className="text-sm font-medium text-gray-900">
														{rel.name}
													</span>
													<span className={`text-xs ${getFieldTypeColor(rel.type)}`}>
														{rel.type}
													</span>
												</div>
												<span className="text-xs text-gray-600">
													→ {rel.related_model}
												</span>
											</div>
										))}
									</>
								)}
							</div>

							{/* Table Footer */}
							<div className="px-4 py-2 bg-gray-50 border-t border-gray-200 rounded-b-md">
								<div className="flex items-center justify-between text-xs text-gray-600">
									<span>{model.fields.length} fields</span>
									<span>{model.relationships.length} relationships</span>
								</div>
							</div>
						</div>
					);
				})}
			</div>
		</div>
	);
}