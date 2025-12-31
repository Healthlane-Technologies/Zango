import { useEffect, useState } from 'react';
import { useDispatch } from 'react-redux';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { createCodeExecution, updateCodeExecution, getCodeExecutionDetail } from '../../../../services/codeexecApi';
import { toggleRerenderPage } from '../../slice/Index';
import './Index.css';

// Dynamic Monaco Editor import
let MonacoEditor = null;

const loadMonacoEditor = async () => {
	if (!MonacoEditor) {
		const module = await import('@monaco-editor/react');
		MonacoEditor = module.default;
	}
	return MonacoEditor;
};

export default function CodeExecForm() {
	const { appId } = useParams();
	const navigate = useNavigate();
	const dispatch = useDispatch();
	const [searchParams] = useSearchParams();
	const codeexecId = searchParams.get('id');

	const [formData, setFormData] = useState({
		name: '',
		description: '',
		code: '',
	});

	const [errors, setErrors] = useState({});
	const [isSubmitting, setIsSubmitting] = useState(false);
	const [isLoading, setIsLoading] = useState(!!codeexecId);
	const [monacoReady, setMonacoReady] = useState(false);
	const [Editor, setEditor] = useState(null);

	// Load existing code execution if editing
	useEffect(() => {
		if (codeexecId) {
			const fetchExistingData = async () => {
				try {
					const response = await getCodeExecutionDetail(appId, codeexecId);
					if (response.ok) {
						const data = await response.json();
						const codeexec = data.response?.codeexec || data.codeexec;
						if (data.success && codeexec) {
							setFormData({
								name: codeexec.name || '',
								description: codeexec.description || '',
								code: codeexec.code || '',
							});
						}
					}
				} catch (error) {
					console.error('Error fetching code execution details:', error);
					setErrors({
						submit: 'Failed to load code execution details',
					});
				} finally {
					setIsLoading(false);
				}
			};

			fetchExistingData();
		}
	}, [codeexecId, appId]);

	// Load Monaco Editor
	useEffect(() => {
		loadMonacoEditor().then((EditorComponent) => {
			setEditor(() => EditorComponent);
			setMonacoReady(true);
		});
	}, []);

	const handleChange = (e) => {
		const { name, value } = e.target;
		setFormData((prev) => ({
			...prev,
			[name]: value,
		}));
		if (errors[name]) {
			setErrors((prev) => ({
				...prev,
				[name]: '',
			}));
		}
	};

	const handleCodeChange = (value) => {
		setFormData((prev) => ({
			...prev,
			code: value || '',
		}));
		if (errors.code) {
			setErrors((prev) => ({
				...prev,
				code: '',
			}));
		}
	};

	const validateForm = () => {
		const newErrors = {};

		if (!formData.name.trim()) {
			newErrors.name = 'Name is required';
		}
		if (!formData.code.trim()) {
			newErrors.code = 'Code is required';
		}

		setErrors(newErrors);
		return Object.keys(newErrors).length === 0;
	};

	const handleSubmit = async (e) => {
		e.preventDefault();

		if (!validateForm()) {
			return;
		}

		setIsSubmitting(true);

		try {
			const payload = {
				name: formData.name,
				description: formData.description,
				code: formData.code,
			};

			let response;
			if (codeexecId) {
				response = await updateCodeExecution(appId, codeexecId, payload);
			} else {
				response = await createCodeExecution(appId, payload);
			}

			if (response.ok) {
				const data = await response.json();
				if (data.success) {
					dispatch(toggleRerenderPage());
					navigate(`/platform/apps/${appId}/codeexec/`);
				} else {
					setErrors({
						submit: data.response?.message || 'Error saving code execution',
					});
				}
			} else {
				setErrors({
					submit: 'Error saving code execution',
				});
			}
		} catch (error) {
			console.error('Error saving code execution:', error);
			setErrors({
				submit: 'Error saving code execution',
			});
		} finally {
			setIsSubmitting(false);
		}
	};

	const handleCancel = () => {
		navigate(`/platform/apps/${appId}/codeexec/`);
	};

	if (isLoading) {
		return (
			<div className="codeexec-form-container">
				<p>Loading...</p>
			</div>
		);
	}

	return (
		<div className="codeexec-form-container">
			<div className="form-header">
				<div className="form-title-section">
					<h1>{codeexecId ? 'Edit Code Execution' : 'Create Code Execution'}</h1>
					<p>Write and manage your code snippets</p>
				</div>
				<div className="form-actions">
					<button
						type="button"
						onClick={handleCancel}
						className="btn-secondary"
						disabled={isSubmitting}
					>
						Cancel
					</button>
					<button
						type="submit"
						onClick={handleSubmit}
						className="btn-primary"
						disabled={isSubmitting}
					>
						{isSubmitting ? 'Saving...' : 'Save Code Execution'}
					</button>
				</div>
			</div>

			{errors.submit && (
				<div className="form-error-banner">{errors.submit}</div>
			)}

			<div className="form-wrapper">
				<div className="form-left">
					{monacoReady && Editor ? (
						<div className="editor-container">
							<label className="editor-label">Code</label>
							<Editor
								height="100%"
								defaultLanguage="python"
								value={formData.code}
								onChange={handleCodeChange}
								theme="vs-light"
								options={{
									minimap: { enabled: false },
									fontSize: 14,
									lineNumbers: 'on',
									scrollBeyondLastLine: false,
									automaticLayout: true,
									tabSize: 4,
									wordWrap: 'on',
								}}
							/>
							{errors.code && (
								<span className="field-error">{errors.code}</span>
							)}
						</div>
					) : (
						<div className="editor-loading">Loading Monaco Editor...</div>
					)}
				</div>

				<div className="form-right">
					<form className="form-fields">
						<div className="form-group">
							<label htmlFor="name">
								Name <span className="required">*</span>
							</label>
							<input
								type="text"
								id="name"
								name="name"
								value={formData.name}
								onChange={handleChange}
								placeholder="Enter code execution name"
								className={`form-input ${errors.name ? 'error' : ''}`}
								disabled={isSubmitting}
							/>
							{errors.name && (
								<span className="field-error">{errors.name}</span>
							)}
						</div>

						<div className="form-group">
							<label htmlFor="description">Description</label>
							<textarea
								id="description"
								name="description"
								value={formData.description}
								onChange={handleChange}
								placeholder="Enter description (optional)"
								className="form-textarea"
								rows="6"
								disabled={isSubmitting}
							/>
						</div>

						<div className="form-info">
							<div className="info-card">
								<h3>Available Functions</h3>
								<ul>
									<li>datetime - Date/time operations</li>
									<li>json - JSON parsing</li>
									<li>requests - HTTP requests</li>
									<li>boto3 - AWS SDK</li>
									<li>zlogger - Custom logging</li>
								</ul>
							</div>

							<div className="info-card">
								<h3>Tips</h3>
								<ul>
									<li>Use <code>zlogger</code> dict for logging output</li>
									<li>Access file with <code>obj</code> variable</li>
									<li>Define a <code>zelthy_codeexec_handler()</code> function</li>
									<li>Execution happens asynchronously</li>
								</ul>
							</div>
						</div>
					</form>
				</div>
			</div>
		</div>
	);
}
