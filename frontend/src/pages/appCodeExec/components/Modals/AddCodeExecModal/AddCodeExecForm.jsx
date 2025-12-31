import { useState } from 'react';
import { useDispatch } from 'react-redux';
import { useParams } from 'react-router-dom';
import { createCodeExecution } from '../../../../../services/codeexecApi';
import { toggleRerenderPage } from '../../../slice/Index';

export default function AddCodeExecForm({ onClose }) {
	const { appId } = useParams();
	const dispatch = useDispatch();

	const [formData, setFormData] = useState({
		name: '',
		description: '',
		code: '',
	});

	const [errors, setErrors] = useState({});
	const [isSubmitting, setIsSubmitting] = useState(false);

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
			const response = await createCodeExecution(appId, {
				name: formData.name,
				description: formData.description,
				code: formData.code,
			});

			if (response.ok) {
				const data = await response.json();
				if (data.success) {
					dispatch(toggleRerenderPage());
					onClose();
				} else {
					setErrors({
						submit: data.response?.message || 'Error creating code execution',
					});
				}
			} else {
				setErrors({
					submit: 'Error creating code execution',
				});
			}
		} catch (error) {
			console.error('Error creating code execution:', error);
			setErrors({
				submit: 'Error creating code execution',
			});
		} finally {
			setIsSubmitting(false);
		}
	};

	return (
		<form onSubmit={handleSubmit} className="form-container">
			{errors.submit && (
				<div className="form-error-message">{errors.submit}</div>
			)}

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
					rows="3"
				/>
			</div>

			<div className="form-group">
				<label htmlFor="code">
					Code <span className="required">*</span>
				</label>
				<textarea
					id="code"
					name="code"
					value={formData.code}
					onChange={handleChange}
					placeholder="Enter Python code"
					className={`form-textarea code-input ${errors.code ? 'error' : ''}`}
					rows="10"
					spellCheck="false"
				/>
				{errors.code && (
					<span className="field-error">{errors.code}</span>
				)}
			</div>

			<div className="form-actions">
				<button
					type="button"
					onClick={onClose}
					className="btn btn-secondary"
					disabled={isSubmitting}
				>
					Cancel
				</button>
				<button
					type="submit"
					className="btn btn-primary"
					disabled={isSubmitting}
				>
					{isSubmitting ? 'Creating...' : 'Create Code Execution'}
				</button>
			</div>
		</form>
	);
}
