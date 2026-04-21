import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { Formik } from 'formik';
import * as Yup from 'yup';
import toast from 'react-hot-toast';
import useApi from '../../../hooks/useApi';
import Modal from '../../../components/Modal';
import InputField from '../../../components/Form/InputField.jsx';
import Toast from '../../../components/Notifications/Toast';

const PROVIDER_COLORS = {
	anthropic: '#6B5CE7',
	openai: '#10B981',
	azure_openai: '#346BD4',
	bedrock: '#F59E0B',
};

const PROVIDER_INITIALS = {
	anthropic: 'A',
	openai: 'O',
	azure_openai: 'Az',
	bedrock: 'B',
};

const DEFAULT_COLOR = '#8B5CF6';

function notify(type, title, description) {
	toast.custom(
		(t) => (
			<Toast
				type={type}
				toastRef={t}
				title={title}
				description={description}
			/>
		),
		{ duration: 5000, position: 'bottom-left' }
	);
}

function StatusBadge({ status }) {
	const isActive = status === 'active';
	return (
		<span className="flex items-center gap-[4px]">
			<span
				className={`inline-block h-[6px] w-[6px] rounded-full ${
					isActive ? 'bg-[#10B981]' : 'bg-[#6B7280]'
				}`}
			/>
			<span
				className={`font-lato text-[12px] font-medium capitalize ${
					isActive ? 'text-[#10B981]' : 'text-[#6B7280]'
				}`}
			>
				{status === 'active' ? 'Active' : 'Inactive'}
			</span>
		</span>
	);
}

function ConfirmationModal({ show, onClose, onConfirm, title, message, confirmLabel, confirmColor, loading }) {
	if (!show) return null;

	const colorClasses = {
		red: 'bg-[#EF4444] hover:bg-[#DC2626]',
		amber: 'bg-[#F59E0B] hover:bg-[#D97706]',
		green: 'bg-[#10B981] hover:bg-[#059669]',
		blue: 'bg-[#346BD4] hover:bg-[#2556B0]',
	};

	return (
		<Modal
			label={title}
			show={show}
			closeModal={onClose}
			ModalBody={
				<div className="flex flex-col gap-[24px]">
					<p className="font-lato text-[14px] leading-[22px] text-[#6B7280]">
						{message}
					</p>
					<div className="flex justify-end gap-[12px]">
						<button
							onClick={onClose}
							disabled={loading}
							className="rounded-[8px] border border-[#DDE2E5] px-[20px] py-[10px] font-lato text-[14px] font-medium text-[#111827] transition-colors hover:bg-[#F9FAFB] disabled:opacity-50"
						>
							Cancel
						</button>
						<button
							onClick={onConfirm}
							disabled={loading}
							className={`rounded-[8px] px-[20px] py-[10px] font-lato text-[14px] font-medium text-white transition-colors disabled:opacity-50 ${colorClasses[confirmColor] || colorClasses.blue}`}
						>
							{loading ? 'Processing...' : confirmLabel}
						</button>
					</div>
				</div>
			}
		/>
	);
}

function AddProviderFormBody({ formik, availableProviders }) {
	const selectedSlug = formik.values.provider_slug;
	const selectedProvider = availableProviders.find((p) => p.slug === selectedSlug);
	const supportedModels = selectedProvider?.supported_models || [];
	const configFields = selectedProvider?.config_fields || [];

	return (
		<form
			onSubmit={formik.handleSubmit}
			className="flex grow flex-col gap-[20px] overflow-y-auto"
		>
			<div>
				<label className="font-lato text-[12px] font-semibold uppercase tracking-[0.6px] text-[#6C747D]">
					Provider Type
				</label>
				<select
					name="provider_slug"
					value={formik.values.provider_slug}
					onChange={(e) => {
						formik.handleChange(e);
						const prov = availableProviders.find((p) => p.slug === e.target.value);
						if (prov && prov.supported_models.length > 0) {
							formik.setFieldValue('default_model', prov.supported_models[0].id);
						}
					}}
					onBlur={formik.handleBlur}
					className="mt-[4px] w-full rounded-[8px] border border-[#DDE2E5] px-[12px] py-[10px] font-lato text-[14px] text-[#111827] outline-none focus:border-[#5048ED] focus:ring-1 focus:ring-[#5048ED]"
				>
					<option value="">Select a provider...</option>
					{availableProviders.map((p) => (
						<option key={p.slug} value={p.slug}>
							{p.display_name}
						</option>
					))}
				</select>
				{formik.touched.provider_slug && formik.errors.provider_slug && (
					<p className="mt-[4px] font-lato text-[12px] text-[#EF4444]">
						{formik.errors.provider_slug}
					</p>
				)}
			</div>

			<InputField
				label="Configuration Name"
				name="name"
				id="name"
				placeholder="e.g. claude-primary, gpt4-fallback"
			/>
			<InputField
				label="Description"
				name="description"
				id="description"
				placeholder="e.g. Primary provider for production"
			/>

			{/* Dynamic config fields based on provider type */}
			{configFields.map((field) => {
				if (field.type === 'select' && field.options_from === 'supported_models') {
					return (
						<div key={field.name}>
							<label className="font-lato text-[12px] font-semibold uppercase tracking-[0.6px] text-[#6C747D]">
								{field.label}
							</label>
							<select
								name="default_model"
								value={formik.values.default_model}
								onChange={formik.handleChange}
								onBlur={formik.handleBlur}
								className="mt-[4px] w-full rounded-[8px] border border-[#DDE2E5] px-[12px] py-[10px] font-lato text-[14px] text-[#111827] outline-none focus:border-[#5048ED] focus:ring-1 focus:ring-[#5048ED]"
							>
								<option value="">Select a model...</option>
								{supportedModels.map((m) => (
									<option key={m.id} value={m.id}>
										{m.name} ({m.id})
									</option>
								))}
							</select>
						</div>
					);
				}
				const inputType = field.type === 'secret' ? 'password' : 'text';
				return (
					<InputField
						key={field.name}
						label={field.label}
						name={`config_${field.name}`}
						id={`config_${field.name}`}
						type={inputType}
						placeholder={field.help_text || `Enter ${field.label.toLowerCase()}`}
					/>
				);
			})}

			<InputField
				label="Rate Limit (req/min)"
				name="rate_limit_rpm"
				id="rate_limit_rpm"
				type="number"
				placeholder="e.g. 1000 (leave empty for unlimited)"
			/>
			<InputField
				label="Monthly Budget (USD)"
				name="monthly_budget_usd"
				id="monthly_budget_usd"
				type="number"
				placeholder="e.g. 500 (leave empty for unlimited)"
			/>

			<div className="flex justify-end gap-[12px] pt-[8px]">
				<button
					type="submit"
					disabled={formik.isSubmitting || !formik.isValid}
					className="rounded-[8px] bg-[#5048ED] px-[24px] py-[10px] font-lato text-[14px] font-medium text-white transition-colors hover:bg-[#4338CA] disabled:pointer-events-none disabled:opacity-50"
				>
					{formik.isSubmitting ? 'Adding...' : 'Add Provider'}
				</button>
			</div>
		</form>
	);
}

function EditProviderFormBody({ formik, configFields }) {
	return (
		<form
			onSubmit={formik.handleSubmit}
			className="flex grow flex-col gap-[20px] overflow-y-auto"
		>
			<InputField
				label="Configuration Name"
				name="name"
				id="name"
				placeholder="e.g. claude-primary"
			/>
			<InputField
				label="Description"
				name="description"
				id="description"
				placeholder="Description"
			/>

			{configFields.map((field) => {
				if (field.type === 'select' && field.options_from === 'supported_models') {
					return null; // default_model handled separately
				}
				const inputType = field.type === 'secret' ? 'password' : 'text';
				return (
					<InputField
						key={field.name}
						label={field.label}
						name={`config_${field.name}`}
						id={`config_${field.name}`}
						type={inputType}
						placeholder={field.help_text || `Enter ${field.label.toLowerCase()}`}
					/>
				);
			})}

			<InputField
				label="Rate Limit (req/min)"
				name="rate_limit_rpm"
				id="rate_limit_rpm"
				type="number"
				placeholder="Leave empty for unlimited"
			/>
			<InputField
				label="Monthly Budget (USD)"
				name="monthly_budget_usd"
				id="monthly_budget_usd"
				type="number"
				placeholder="Leave empty for unlimited"
			/>

			<div className="flex justify-end gap-[12px] pt-[8px]">
				<button
					type="submit"
					disabled={formik.isSubmitting || !formik.isValid}
					className="rounded-[8px] bg-[#5048ED] px-[24px] py-[10px] font-lato text-[14px] font-medium text-white transition-colors hover:bg-[#4338CA] disabled:pointer-events-none disabled:opacity-50"
				>
					{formik.isSubmitting ? 'Saving...' : 'Save Changes'}
				</button>
			</div>
		</form>
	);
}

function ProviderRow({ provider, onEdit, onToggleStatus, onTestConnection, onDelete, testingId }) {
	const [expanded, setExpanded] = useState(false);
	const color = PROVIDER_COLORS[provider.provider_slug] || DEFAULT_COLOR;
	const initial = PROVIDER_INITIALS[provider.provider_slug] || provider.name.charAt(0).toUpperCase();
	const maskedConfig = provider.masked_config || {};
	const enabledModels = provider.enabled_models || [];
	const budgetStatus = provider.budget_status || {};
	const isTesting = testingId === provider.id;

	return (
		<div className="rounded-[8px] border border-[#E5E7EB] bg-white">
			<div className="flex items-center px-[24px] py-[16px]">
				<button
					onClick={() => setExpanded(!expanded)}
					className="mr-[16px] text-[#6B7280] transition-colors hover:text-[#111827]"
				>
					<svg
						width="12"
						height="12"
						viewBox="0 0 12 12"
						fill="currentColor"
						className={`transition-transform ${expanded ? 'rotate-90' : ''}`}
					>
						<path d="M4.5 2L8.5 6L4.5 10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
					</svg>
				</button>

				<div
					className="mr-[12px] flex h-[40px] w-[40px] items-center justify-center rounded-full"
					style={{ backgroundColor: color }}
				>
					<span className="font-source-sans-pro text-[16px] font-semibold text-white">
						{initial}
					</span>
				</div>

				<div className="mr-[24px] min-w-[120px]">
					<div className="flex items-center gap-[8px]">
						<span className="font-source-sans-pro text-[16px] font-semibold text-[#111827]">
							{provider.name}
						</span>
						<StatusBadge status={provider.status} />
					</div>
					<span className="font-lato text-[12px] text-[#6B7280]">
						{provider.description || provider.provider_slug}
					</span>
				</div>

				<div className="ml-auto flex items-center gap-[24px]">
					<div>
						<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
							Models
						</span>
						<div className="flex items-center gap-[4px]">
							<svg width="14" height="14" viewBox="0 0 14 14" fill="none">
								<path d="M7 1L1.5 3.5V7L7 9.5L12.5 7V3.5L7 1Z" stroke="#6B7280" strokeWidth="1" fill="none"/>
							</svg>
							<span className="font-lato text-[14px] text-[#111827]">{provider.models_count}</span>
						</div>
					</div>

					<div>
						<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
							Monthly Spend
						</span>
						<p className="font-lato text-[14px] text-[#111827]">
							${parseFloat(provider.current_month_spend_usd || 0).toFixed(2)}
						</p>
					</div>

					<div>
						<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
							Invocations
						</span>
						<p className="font-lato text-[14px] text-[#111827]">
							{provider.total_invocations || 0}
						</p>
					</div>

					<button
						onClick={() => onEdit(provider)}
						className="flex items-center gap-[6px] rounded-[6px] border border-[#DDE2E5] px-[12px] py-[6px] font-lato text-[13px] text-[#111827] transition-colors hover:bg-[#F9FAFB]"
					>
						<svg width="14" height="14" viewBox="0 0 14 14" fill="none">
							<circle cx="7" cy="7" r="5.5" stroke="#6B7280" strokeWidth="1.2"/>
							<path d="M7 4.5V7L8.5 8.5" stroke="#6B7280" strokeWidth="1.2" strokeLinecap="round"/>
						</svg>
						Configure
					</button>
				</div>
			</div>

			{expanded && (
				<div className="border-t border-[#E5E7EB] px-[24px] py-[20px]">
					<div className="mb-[16px] grid grid-cols-4 gap-[24px]">
						<div>
							<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
								Provider Type
							</span>
							<p className="mt-[4px] font-lato text-[14px] text-[#111827]">
								{provider.provider_slug}
							</p>
						</div>
						<div>
							<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
								API Key
							</span>
							<p className="mt-[4px] font-mono font-lato text-[14px] text-[#111827]">
								{maskedConfig.api_key || maskedConfig.aws_access_key_id || '****'}
							</p>
						</div>
						<div>
							<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
								Default Model
							</span>
							<p className="mt-[4px] font-lato text-[14px] text-[#111827]">
								{provider.default_model}
							</p>
						</div>
						<div>
							<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
								Rate Limit
							</span>
							<p className="mt-[4px] font-lato text-[14px] text-[#111827]">
								{provider.rate_limit_rpm ? `${provider.rate_limit_rpm} req/min` : 'Unlimited'}
							</p>
						</div>
					</div>

					<div className="mb-[16px] grid grid-cols-4 gap-[24px]">
						<div className="col-span-2">
							<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
								Enabled Models
							</span>
							<div className="mt-[4px] flex flex-wrap gap-[8px]">
								{enabledModels.filter((m) => m.is_enabled).map((model) => (
									<span
										key={model.model_id}
										className="rounded-[4px] bg-[#EFF6FF] px-[8px] py-[2px] font-lato text-[13px] text-[#346BD4]"
									>
										{model.display_name || model.model_id}
									</span>
								))}
								{enabledModels.filter((m) => m.is_enabled).length === 0 && (
									<span className="font-lato text-[13px] text-[#9CA3AF]">No models configured</span>
								)}
							</div>
						</div>
						<div>
							<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
								Monthly Budget
							</span>
							<p className="mt-[4px] font-lato text-[14px] text-[#111827]">
								{provider.monthly_budget_usd
									? `$${parseFloat(provider.monthly_budget_usd).toFixed(2)}`
									: 'Unlimited'}
							</p>
						</div>
						<div>
							<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
								Budget Used
							</span>
							<p className="mt-[4px] font-lato text-[14px] font-semibold text-[#111827]">
								{budgetStatus.pct != null ? `${budgetStatus.pct}%` : 'N/A'}
							</p>
						</div>
					</div>

					<div className="mb-[16px] grid grid-cols-4 gap-[24px]">
						<div>
							<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
								Validated
							</span>
							<p className={`mt-[4px] font-lato text-[14px] ${provider.is_validated ? 'text-[#10B981]' : 'text-[#9CA3AF]'}`}>
								{provider.is_validated ? 'Yes' : 'Not validated'}
							</p>
						</div>
						<div>
							<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
								Total Cost
							</span>
							<p className="mt-[4px] font-lato text-[14px] text-[#111827]">
								${parseFloat(provider.total_cost_usd || 0).toFixed(2)}
							</p>
						</div>
						<div>
							<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
								Total Tokens
							</span>
							<p className="mt-[4px] font-lato text-[14px] text-[#111827]">
								{((provider.total_input_tokens || 0) + (provider.total_output_tokens || 0)).toLocaleString()}
							</p>
						</div>
					</div>

					<div className="flex items-center gap-[12px]">
						<button
							onClick={() => onTestConnection(provider)}
							disabled={isTesting}
							className="flex items-center gap-[6px] rounded-[6px] border border-[#10B981] px-[12px] py-[6px] font-lato text-[13px] text-[#10B981] transition-colors hover:bg-[#ECFDF5] disabled:opacity-50"
						>
							{isTesting ? (
								<span className="inline-block h-[12px] w-[12px] animate-spin rounded-full border-[2px] border-[#10B981] border-t-transparent" />
							) : (
								<svg width="12" height="12" viewBox="0 0 12 12" fill="none">
									<path d="M3 6L5 9L10 3" stroke="#10B981" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
								</svg>
							)}
							{isTesting ? 'Testing...' : 'Test Connection'}
						</button>
						<button
							onClick={() => onEdit(provider)}
							className="flex items-center gap-[6px] rounded-[6px] border border-[#DDE2E5] px-[12px] py-[6px] font-lato text-[13px] text-[#111827] transition-colors hover:bg-[#F9FAFB]"
						>
							<svg width="12" height="12" viewBox="0 0 12 12" fill="none">
								<path d="M8.5 1.5L10.5 3.5L4 10H2V8L8.5 1.5Z" stroke="#6B7280" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
							</svg>
							Edit
						</button>
						<button
							onClick={() => onToggleStatus(provider)}
							className={`flex items-center gap-[6px] rounded-[6px] border px-[12px] py-[6px] font-lato text-[13px] transition-colors ${
								provider.status === 'active'
									? 'border-[#EF4444] text-[#EF4444] hover:bg-[#FEF2F2]'
									: 'border-[#10B981] text-[#10B981] hover:bg-[#ECFDF5]'
							}`}
						>
							{provider.status === 'active' ? (
								<svg width="12" height="12" viewBox="0 0 12 12" fill="none">
									<circle cx="6" cy="6" r="5" stroke="#EF4444" strokeWidth="1.2" fill="none"/>
									<path d="M4 4L8 8M8 4L4 8" stroke="#EF4444" strokeWidth="1.2" strokeLinecap="round"/>
								</svg>
							) : (
								<svg width="12" height="12" viewBox="0 0 12 12" fill="none">
									<path d="M3 6L5 9L10 3" stroke="#10B981" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
								</svg>
							)}
							{provider.status === 'active' ? 'Disable' : 'Enable'}
						</button>
						<button
							onClick={() => onDelete(provider)}
							className="flex items-center gap-[6px] rounded-[6px] border border-[#EF4444] px-[12px] py-[6px] font-lato text-[13px] text-[#EF4444] transition-colors hover:bg-[#FEF2F2]"
						>
							<svg width="12" height="12" viewBox="0 0 12 12" fill="none">
								<path d="M2 3H10M4 3V2H8V3M5 5V9M7 5V9M3 3L3.5 10H8.5L9 3" stroke="#EF4444" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
							</svg>
							Delete
						</button>
					</div>
				</div>
			)}
		</div>
	);
}

export default function Providers() {
	const { appId } = useParams();
	const triggerApi = useApi();

	const [providers, setProviders] = useState([]);
	const [availableProviders, setAvailableProviders] = useState([]);
	const [addModalOpen, setAddModalOpen] = useState(false);
	const [editModalOpen, setEditModalOpen] = useState(false);
	const [editingProvider, setEditingProvider] = useState(null);
	const [confirmModal, setConfirmModal] = useState({ show: false, type: null, provider: null });
	const [testingId, setTestingId] = useState(null);
	const [actionLoading, setActionLoading] = useState(false);

	// Fetch configured providers
	const fetchProviders = useCallback(async () => {
		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/ai/providers/`,
			type: 'GET',
			loader: false,
		});
		if (success && response?.providers) {
			const records = response.providers.records || response.providers;
			setProviders(Array.isArray(records) ? records : []);
		}
	}, [appId, triggerApi]);

	// Fetch available provider types from registry
	const fetchAvailableProviders = useCallback(async () => {
		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/ai/providers/available/`,
			type: 'GET',
			loader: false,
		});
		if (success && response?.providers) {
			setAvailableProviders(response.providers);
		}
	}, [appId, triggerApi]);

	useEffect(() => {
		fetchProviders();
		fetchAvailableProviders();
	}, [appId]);

	// Add provider
	const handleAddProvider = async (values, { resetForm, setSubmitting }) => {
		const providerMeta = availableProviders.find((p) => p.slug === values.provider_slug);
		const configFields = providerMeta?.config_fields || [];

		// Build the config object from form values
		const config = {};
		configFields.forEach((field) => {
			const formKey = `config_${field.name}`;
			if (values[formKey] !== undefined && values[formKey] !== '') {
				config[field.name] = field.type === 'integer' ? parseInt(values[formKey], 10) : values[formKey];
			} else if (field.default !== undefined) {
				config[field.name] = field.default;
			}
		});

		const payload = {
			name: values.name,
			description: values.description,
			provider_slug: values.provider_slug,
			config,
			default_model: values.default_model,
			rate_limit_rpm: values.rate_limit_rpm ? parseInt(values.rate_limit_rpm, 10) : null,
			monthly_budget_usd: values.monthly_budget_usd || null,
		};

		const { success, response } = await triggerApi({
			url: `/api/v1/apps/${appId}/ai/providers/`,
			type: 'POST',
			loader: true,
			payload,
			showErrorModal: false,
		});

		setSubmitting(false);
		if (success) {
			setAddModalOpen(false);
			resetForm();
			notify('success', 'Provider Added', `${values.name} has been added successfully.`);
			fetchProviders();
		} else {
			notify('error', 'Failed to Add Provider', response?.message || 'An error occurred.');
		}
	};

	// Edit provider
	const handleEditProvider = async (values, { resetForm, setSubmitting }) => {
		if (!editingProvider) return;

		const providerMeta = availableProviders.find((p) => p.slug === editingProvider.provider_slug);
		const configFields = providerMeta?.config_fields || [];

		const config = {};
		configFields.forEach((field) => {
			const formKey = `config_${field.name}`;
			if (values[formKey] !== undefined && values[formKey] !== '') {
				config[field.name] = field.type === 'integer' ? parseInt(values[formKey], 10) : values[formKey];
			}
		});

		const payload = {
			name: values.name,
			description: values.description,
			config,
			rate_limit_rpm: values.rate_limit_rpm ? parseInt(values.rate_limit_rpm, 10) : null,
			monthly_budget_usd: values.monthly_budget_usd || null,
		};

		const { success } = await triggerApi({
			url: `/api/v1/apps/${appId}/ai/providers/${editingProvider.id}/`,
			type: 'PUT',
			loader: true,
			payload,
		});

		setSubmitting(false);
		if (success) {
			setEditModalOpen(false);
			setEditingProvider(null);
			resetForm();
			notify('success', 'Provider Updated', `${values.name} has been updated successfully.`);
			fetchProviders();
		}
	};

	const openEdit = (provider) => {
		setEditingProvider(provider);
		setEditModalOpen(true);
	};

	// Toggle status
	const handleToggleStatus = (provider) => {
		const isDisabling = provider.status === 'active';
		setConfirmModal({
			show: true,
			type: 'toggle',
			provider,
			title: isDisabling ? 'Disable Provider' : 'Enable Provider',
			message: isDisabling
				? `Are you sure you want to disable ${provider.name}? Any agents using this provider will stop working.`
				: `Are you sure you want to enable ${provider.name}?`,
			confirmLabel: isDisabling ? 'Disable' : 'Enable',
			confirmColor: isDisabling ? 'red' : 'green',
		});
	};

	const confirmToggleStatus = async () => {
		const provider = confirmModal.provider;
		const newEnabled = provider.status !== 'active';
		setActionLoading(true);

		const { success } = await triggerApi({
			url: `/api/v1/apps/${appId}/ai/providers/${provider.id}/toggle/`,
			type: 'POST',
			loader: false,
			payload: { is_enabled: newEnabled },
		});

		setActionLoading(false);
		setConfirmModal({ show: false, type: null, provider: null });

		if (success) {
			notify(
				'success',
				newEnabled ? 'Provider Enabled' : 'Provider Disabled',
				`${provider.name} has been ${newEnabled ? 'enabled' : 'disabled'}.`
			);
			fetchProviders();
		}
	};

	// Delete provider
	const handleDelete = (provider) => {
		setConfirmModal({
			show: true,
			type: 'delete',
			provider,
			title: 'Delete Provider',
			message: `Are you sure you want to delete ${provider.name}? ${
				provider.total_invocations > 0
					? 'This provider has invocation history and will be disabled instead of permanently deleted.'
					: 'This action cannot be undone.'
			}`,
			confirmLabel: 'Delete',
			confirmColor: 'red',
		});
	};

	const confirmDelete = async () => {
		const provider = confirmModal.provider;
		setActionLoading(true);

		const { success } = await triggerApi({
			url: `/api/v1/apps/${appId}/ai/providers/${provider.id}/`,
			type: 'DELETE',
			loader: false,
		});

		setActionLoading(false);
		setConfirmModal({ show: false, type: null, provider: null });

		if (success) {
			notify('success', 'Provider Deleted', `${provider.name} has been removed.`);
			fetchProviders();
		}
	};

	// Test connection
	const handleTestConnection = async (provider) => {
		if (testingId) return;
		setTestingId(provider.id);

		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/ai/providers/${provider.id}/validate/`,
			type: 'POST',
			loader: false,
			showErrorModal: false,
		});

		setTestingId(null);
		if (success) {
			notify('success', 'Connection Successful', `${provider.name} credentials are valid.`);
			fetchProviders(); // refresh to show updated is_validated
		} else {
			notify('error', 'Connection Failed', response?.message || 'Could not validate provider credentials.');
		}
	};

	const handleConfirm = () => {
		if (confirmModal.type === 'toggle') confirmToggleStatus();
		else if (confirmModal.type === 'delete') confirmDelete();
	};

	const activeCount = providers.filter((p) => p.status === 'active').length;
	const totalModels = providers.reduce((sum, p) => sum + (p.models_count || 0), 0);

	// Build add form initial values
	const addInitialValues = {
		name: '',
		description: '',
		provider_slug: '',
		default_model: '',
		rate_limit_rpm: '',
		monthly_budget_usd: '',
	};
	// Add dynamic config fields
	availableProviders.forEach((prov) => {
		(prov.config_fields || []).forEach((field) => {
			const key = `config_${field.name}`;
			if (!(key in addInitialValues)) {
				addInitialValues[key] = field.default != null ? String(field.default) : '';
			}
		});
	});

	// Build edit form initial values
	const editConfigFields = editingProvider
		? (availableProviders.find((p) => p.slug === editingProvider.provider_slug)?.config_fields || [])
		: [];
	const editInitialValues = editingProvider
		? (() => {
				const vals = {
					name: editingProvider.name,
					description: editingProvider.description || '',
					rate_limit_rpm: editingProvider.rate_limit_rpm || '',
					monthly_budget_usd: editingProvider.monthly_budget_usd || '',
				};
				editConfigFields.forEach((field) => {
					const maskedVal = editingProvider.masked_config?.[field.name];
					vals[`config_${field.name}`] = maskedVal != null ? String(maskedVal) : '';
				});
				return vals;
		  })()
		: addInitialValues;

	const addValidationSchema = Yup.object({
		name: Yup.string().required('Name is required'),
		provider_slug: Yup.string().required('Provider type is required'),
		default_model: Yup.string().required('Default model is required'),
	});

	const editValidationSchema = Yup.object({
		name: Yup.string().required('Name is required'),
	});

	return (
		<div className="flex flex-col gap-[24px]">
			{/* Summary card */}
			<div className="rounded-[16px] border border-[#E5E7EB] bg-white p-[24px]">
				<div className="mb-[16px] flex items-center justify-between">
					<div>
						<h2 className="font-source-sans-pro text-[18px] font-semibold text-[#111827]">
							LLM Providers
						</h2>
						<p className="font-lato text-[14px] text-[#6B7280]">
							Configure and manage connections to AI model providers
						</p>
					</div>
					<button
						onClick={() => setAddModalOpen(true)}
						className="flex items-center gap-[6px] rounded-[8px] bg-[#5048ED] px-[16px] py-[8px] font-lato text-[14px] font-medium text-white transition-colors hover:bg-[#4338CA]"
					>
						+ Add Provider
					</button>
				</div>
				<div className="flex items-center gap-[16px]">
					<div className="flex items-center gap-[8px]">
						<span className="font-lato text-[14px] text-[#6B7280]">Total Providers</span>
						<span className="font-lato text-[14px] font-semibold text-[#111827]">{providers.length}</span>
					</div>
					<div className="h-[16px] w-[1px] bg-[#E5E7EB]" />
					<div className="flex items-center gap-[8px]">
						<span className="font-lato text-[14px] text-[#6B7280]">Active</span>
						<span className="font-lato text-[14px] font-semibold text-[#10B981]">{activeCount}</span>
					</div>
					<div className="h-[16px] w-[1px] bg-[#E5E7EB]" />
					<div className="flex items-center gap-[8px]">
						<span className="font-lato text-[14px] text-[#6B7280]">Total Models</span>
						<span className="font-lato text-[14px] font-semibold text-[#111827]">{totalModels}</span>
					</div>
				</div>
			</div>

			{/* Provider list */}
			<div className="flex flex-col gap-[12px]">
				{providers.length === 0 && (
					<div className="rounded-[8px] border border-dashed border-[#D1D5DB] bg-white px-[24px] py-[48px] text-center">
						<p className="font-lato text-[14px] text-[#9CA3AF]">
							No providers configured yet. Click "Add Provider" to get started.
						</p>
					</div>
				)}
				{providers.map((provider) => (
					<ProviderRow
						key={provider.id}
						provider={provider}
						onEdit={openEdit}
						onToggleStatus={handleToggleStatus}
						onTestConnection={handleTestConnection}
						onDelete={handleDelete}
						testingId={testingId}
					/>
				))}
			</div>

			{/* Add Provider Modal */}
			<Formik
				initialValues={addInitialValues}
				validationSchema={addValidationSchema}
				onSubmit={handleAddProvider}
				enableReinitialize
			>
				{(formik) => (
					<Modal
						label="Add Provider"
						show={addModalOpen}
						closeModal={() => {
							setAddModalOpen(false);
							formik.resetForm();
						}}
						ModalBody={
							<AddProviderFormBody
								formik={formik}
								availableProviders={availableProviders}
							/>
						}
					/>
				)}
			</Formik>

			{/* Edit Provider Modal */}
			<Formik
				initialValues={editInitialValues}
				validationSchema={editValidationSchema}
				onSubmit={handleEditProvider}
				enableReinitialize
			>
				{(formik) => (
					<Modal
						label={`Edit Provider — ${editingProvider?.name || ''}`}
						show={editModalOpen}
						closeModal={() => {
							setEditModalOpen(false);
							setEditingProvider(null);
							formik.resetForm();
						}}
						ModalBody={
							<EditProviderFormBody
								formik={formik}
								configFields={editConfigFields}
							/>
						}
					/>
				)}
			</Formik>

			{/* Confirmation Modal */}
			<ConfirmationModal
				show={confirmModal.show}
				onClose={() => setConfirmModal({ show: false, type: null, provider: null })}
				onConfirm={handleConfirm}
				title={confirmModal.title}
				message={confirmModal.message}
				confirmLabel={confirmModal.confirmLabel}
				confirmColor={confirmModal.confirmColor}
				loading={actionLoading}
			/>
		</div>
	);
}
