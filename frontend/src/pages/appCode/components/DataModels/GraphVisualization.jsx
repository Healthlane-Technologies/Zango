import React, { useEffect, useRef, useState } from 'react';
import * as Viz from '@viz-js/viz';

export default function GraphVisualization({ dotDiagram, models, onModelClick }) {
	const containerRef = useRef(null);
	const [vizInstance, setVizInstance] = useState(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState(null);
	const [currentSvgElement, setCurrentSvgElement] = useState(null);
	const [exporting, setExporting] = useState(false);

	// Initialize Viz.js instance
	useEffect(() => {
		const initViz = async () => {
			try {
				setLoading(true);
				const instance = await Viz.instance();
				setVizInstance(instance);
				setError(null);
			} catch (err) {
				console.error('Failed to initialize Viz.js:', err);
				setError('Failed to initialize graph visualization library');
			} finally {
				setLoading(false);
			}
		};

		initViz();
	}, []);

	// Render DOT diagram when viz instance is ready and dotDiagram is available
	useEffect(() => {
		if (!vizInstance || !dotDiagram || !containerRef.current) {
			return;
		}

		const renderDiagram = async () => {
			try {
				setLoading(true);
				setError(null);

				// Clear previous content
				containerRef.current.innerHTML = '';

				// Render the DOT diagram as SVG
				const svgElement = vizInstance.renderSVGElement(dotDiagram);
				
				// Add click handling to model nodes
				if (onModelClick && models) {
					addClickHandlers(svgElement);
				}

				// Style the SVG
				svgElement.style.width = '100%';
				svgElement.style.height = 'auto';
				svgElement.style.maxWidth = '100%';

				// Store reference to SVG element for export
				setCurrentSvgElement(svgElement);

				// Append to container
				containerRef.current.appendChild(svgElement);

			} catch (err) {
				console.error('Failed to render DOT diagram:', err);
				setError(`Failed to render diagram: ${err.message}`);
			} finally {
				setLoading(false);
			}
		};

		renderDiagram();
	}, [vizInstance, dotDiagram, models, onModelClick]);

	// Add click handlers to model nodes in the SVG
	const addClickHandlers = (svgElement) => {
		if (!models || !onModelClick) return;

		// Find all graph nodes (model tables)
		const nodes = svgElement.querySelectorAll('g.node');
		
		nodes.forEach(node => {
			// Get the title element which contains the model name
			const titleElement = node.querySelector('title');
			if (!titleElement) return;

			const modelName = titleElement.textContent.trim();
			
			// Find the corresponding model in our data
			const model = models.find(m => m.name === modelName);
			if (!model) return;

			// Make the node clickable
			node.style.cursor = 'pointer';
			node.addEventListener('click', (e) => {
				e.preventDefault();
				e.stopPropagation();
				onModelClick(model);
			});

			// Add hover effects
			node.addEventListener('mouseenter', () => {
				const rect = node.querySelector('polygon, rect, ellipse');
				if (rect) {
					rect.style.filter = 'brightness(1.1)';
					rect.style.stroke = '#3B82F6';
					rect.style.strokeWidth = '2';
				}
			});

			node.addEventListener('mouseleave', () => {
				const rect = node.querySelector('polygon, rect, ellipse');
				if (rect) {
					rect.style.filter = '';
					rect.style.stroke = '';
					rect.style.strokeWidth = '';
				}
			});
		});
	};

	// Generate a fallback diagram if no DOT diagram is provided
	const generateFallbackDiagram = () => {
		if (!models || models.length === 0) {
			return 'digraph { label="No models found"; }';
		}

		let dot = 'digraph Models {\n';
		dot += '  rankdir=TB;\n';
		dot += '  node [shape=record, style=filled, fillcolor=lightblue];\n\n';

		// Add model nodes
		models.forEach(model => {
			const fields = model.fields.slice(0, 5).map(f => f.name).join('\\l');
			dot += `  "${model.name}" [label="{${model.name}|${fields}\\l}"];\n`;
		});

		// Add relationships
		models.forEach(model => {
			model.relationships.forEach(rel => {
				const targetModel = models.find(m => 
					m.name === rel.related_model || 
					`${m.module}.${m.name}` === rel.related_model
				);
				if (targetModel) {
					dot += `  "${model.name}" -> "${targetModel.name}" [label="${rel.name}"];\n`;
				}
			});
		});

		dot += '}';
		return dot;
	};

	const diagramToRender = dotDiagram || generateFallbackDiagram();

	// Export SVG as JPG image
	const exportAsJpg = async () => {
		if (!currentSvgElement) {
			alert('No diagram available to export');
			return;
		}

		try {
			setExporting(true);

			// Clone the SVG element to avoid modifying the original
			const svgClone = currentSvgElement.cloneNode(true);
			
			// Get SVG dimensions
			const bbox = currentSvgElement.getBBox();
			const width = bbox.width || 800;
			const height = bbox.height || 600;
			
			// Set explicit dimensions on the clone
			svgClone.setAttribute('width', width);
			svgClone.setAttribute('height', height);
			svgClone.setAttribute('viewBox', `${bbox.x} ${bbox.y} ${width} ${height}`);
			
			// Convert SVG to string
			const svgData = new XMLSerializer().serializeToString(svgClone);
			const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
			const svgUrl = URL.createObjectURL(svgBlob);

			// Create canvas to convert SVG to JPG
			const canvas = document.createElement('canvas');
			const ctx = canvas.getContext('2d');
			
			// Set canvas size with some padding and higher resolution for better quality
			const scale = 2; // 2x resolution for better quality
			canvas.width = width * scale;
			canvas.height = height * scale;
			
			// Scale the context to maintain image quality
			ctx.scale(scale, scale);
			
			// Fill canvas with white background (JPG doesn't support transparency)
			ctx.fillStyle = 'white';
			ctx.fillRect(0, 0, width, height);

			// Create an image element to load the SVG
			const img = new Image();
			
			img.onload = function() {
				// Draw the SVG image onto the canvas
				ctx.drawImage(img, 0, 0, width, height);
				
				// Convert canvas to JPG blob
				canvas.toBlob((blob) => {
					if (blob) {
						// Create download link
						const url = URL.createObjectURL(blob);
						const link = document.createElement('a');
						link.href = url;
						link.download = `model-diagram-${new Date().toISOString().split('T')[0]}.jpg`;
						
						// Trigger download
						document.body.appendChild(link);
						link.click();
						document.body.removeChild(link);
						
						// Clean up URLs
						URL.revokeObjectURL(url);
						URL.revokeObjectURL(svgUrl);
					}
					
					setExporting(false);
				}, 'image/jpeg', 0.9); // 90% quality
			};

			img.onerror = function() {
				console.error('Failed to load SVG image for export');
				alert('Failed to export image. Please try again.');
				URL.revokeObjectURL(svgUrl);
				setExporting(false);
			};

			// Load the SVG
			img.src = svgUrl;

		} catch (error) {
			console.error('Export error:', error);
			alert('Failed to export image. Please try again.');
			setExporting(false);
		}
	};

	if (loading) {
		return (
			<div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
				<div className="p-4 border-b border-gray-200 bg-gray-50">
					<h3 className="text-sm font-medium text-gray-900">Graph Visualization</h3>
					<p className="text-sm text-gray-600">
						Rendering model relationships diagram...
					</p>
				</div>
				<div className="flex items-center justify-center h-96">
					<div className="flex flex-col items-center">
						<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
						<p className="mt-2 text-sm text-gray-600">Loading visualization...</p>
					</div>
				</div>
			</div>
		);
	}

	if (error) {
		return (
			<div className="bg-white rounded-lg shadow-sm border border-red-200 overflow-hidden">
				<div className="p-4 border-b border-red-200 bg-red-50">
					<h3 className="text-sm font-medium text-red-900">Graph Visualization Error</h3>
					<p className="text-sm text-red-600">
						Failed to render the model diagram.
					</p>
				</div>
				<div className="p-4">
					<div className="bg-red-50 border border-red-200 rounded-md p-3">
						<p className="text-sm text-red-700">{error}</p>
					</div>
					{!dotDiagram && (
						<p className="mt-2 text-sm text-gray-600">
							No DOT diagram data available from the API. Please check the backend implementation.
						</p>
					)}
				</div>
			</div>
		);
	}

	return (
		<div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
			<div className="p-4 border-b border-gray-200 bg-gray-50">
				<div className="flex items-center justify-between">
					<div>
						<h3 className="text-sm font-medium text-gray-900">Graph Visualization</h3>
						<p className="text-sm text-gray-600">
							Interactive model relationships diagram. Click on nodes to view details.
						</p>
					</div>
					<div className="flex items-center space-x-3">
						<div className="flex items-center space-x-2 text-xs text-gray-500">
							{dotDiagram ? (
								<span className="inline-flex items-center px-2 py-1 rounded-full bg-green-100 text-green-700">
									API Generated
								</span>
							) : (
								<span className="inline-flex items-center px-2 py-1 rounded-full bg-yellow-100 text-yellow-700">
									Fallback
								</span>
							)}
						</div>

						{/* Export Button */}
						<button
							onClick={exportAsJpg}
							disabled={!currentSvgElement || exporting}
							className={`inline-flex items-center px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
								!currentSvgElement || exporting
									? 'bg-gray-100 text-gray-400 cursor-not-allowed'
									: 'bg-blue-100 text-blue-700 hover:bg-blue-200'
							}`}
							title="Export diagram as JPG image"
						>
							{exporting ? (
								<>
									<svg className="w-3 h-3 mr-1.5 animate-spin" fill="none" viewBox="0 0 24 24">
										<circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
										<path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
									</svg>
									Exporting...
								</>
							) : (
								<>
									<svg className="w-3 h-3 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
									</svg>
									Export JPG
								</>
							)}
						</button>
					</div>
				</div>
			</div>
			<div className="p-4 bg-gray-50">
				<div
					ref={containerRef}
					className="bg-white border border-gray-200 rounded-md overflow-auto"
					style={{
						minHeight: '400px',
						maxHeight: '600px'
					}}
				/>
			</div>
		</div>
	);
}