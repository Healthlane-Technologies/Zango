import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import useApi from '../../../hooks/useApi';
import StandardModal from '../../../components/StandardModal';
import Toast from '../../../components/Notifications/Toast';


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
	if (isActive) {
		return (
			<span className="inline-flex items-center gap-[5px] rounded-full border border-[#A7F3D0] bg-[#ECFDF5] px-[8px] py-[3px]">
				<span className="h-[6px] w-[6px] rounded-full bg-[#10B981]" />
				<span className="font-lato text-[11px] font-semibold text-[#065F46]">Active</span>
			</span>
		);
	}
	return (
		<span className="inline-flex items-center gap-[5px] rounded-full border border-[#E5E7EB] bg-[#F3F4F6] px-[8px] py-[3px]">
			<svg width="10" height="10" viewBox="0 0 12 12" fill="none">
				<circle cx="6" cy="6" r="4.5" stroke="#9CA3AF" strokeWidth="1.4"/>
				<path d="M2.8 2.8L9.2 9.2" stroke="#9CA3AF" strokeWidth="1.4" strokeLinecap="round"/>
			</svg>
			<span className="font-lato text-[11px] font-semibold text-[#6B7280]">Disabled</span>
		</span>
	);
}

function ConfirmationModal({ show, onClose, onConfirm, title, message, confirmLabel, confirmColor, loading }) {
	if (!show) return null;

	const confirmStyles = {
		red:   'bg-[#EF4444] hover:bg-[#DC2626] text-white',
		amber: 'bg-[#F59E0B] hover:bg-[#D97706] text-white',
		green: 'bg-[#10B981] hover:bg-[#059669] text-white',
		blue:  'bg-[#346BD4] hover:bg-[#2556B0] text-white',
	};

	const iconBg = {
		red:   'bg-[#FEF2F2]',
		amber: 'bg-[#FFFBEB]',
		green: 'bg-[#ECFDF5]',
		blue:  'bg-[#EFF6FF]',
	};

	const iconColor = {
		red:   '#EF4444',
		amber: '#F59E0B',
		green: '#10B981',
		blue:  '#346BD4',
	};

	const color = confirmColor || 'blue';

	return (
		<div className="fixed inset-0 z-50 flex items-center justify-center">
			<div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={!loading ? onClose : undefined} />
			<div className="relative w-full max-w-[400px] rounded-[16px] bg-white p-[28px] shadow-2xl">
				{/* Icon */}
				<div className={`mb-[16px] flex h-[44px] w-[44px] items-center justify-center rounded-full ${iconBg[color]}`}>
					{color === 'red' && (
						<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
							<path d="M10 6V10M10 14H10.01M19 10C19 14.9706 14.9706 19 10 19C5.02944 19 1 14.9706 1 10C1 5.02944 5.02944 1 10 1C14.9706 1 19 5.02944 19 10Z" stroke={iconColor[color]} strokeWidth="1.8" strokeLinecap="round"/>
						</svg>
					)}
					{color === 'amber' && (
						<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
							<path d="M10 6V10M10 14H10.01M19 10C19 14.9706 14.9706 19 10 19C5.02944 19 1 14.9706 1 10C1 5.02944 5.02944 1 10 1C14.9706 1 19 5.02944 19 10Z" stroke={iconColor[color]} strokeWidth="1.8" strokeLinecap="round"/>
						</svg>
					)}
					{color === 'green' && (
						<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
							<path d="M9 12L11 14L15 9M19 10C19 14.9706 14.9706 19 10 19C5.02944 19 1 14.9706 1 10C1 5.02944 5.02944 1 10 1C14.9706 1 19 5.02944 19 10Z" stroke={iconColor[color]} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
						</svg>
					)}
					{color === 'blue' && (
						<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
							<path d="M10 6V10M10 14H10.01M19 10C19 14.9706 14.9706 19 10 19C5.02944 19 1 14.9706 1 10C1 5.02944 5.02944 1 10 1C14.9706 1 19 5.02944 19 10Z" stroke={iconColor[color]} strokeWidth="1.8" strokeLinecap="round"/>
						</svg>
					)}
				</div>

				<h3 className="mb-[8px] font-source-sans-pro text-[18px] font-semibold text-[#111827]">{title}</h3>
				<p className="mb-[24px] font-lato text-[14px] leading-[22px] text-[#6B7280]">{message}</p>

				<div className="flex gap-[10px]">
					<button
						onClick={onClose}
						disabled={loading}
						className="flex-1 rounded-[8px] border border-[#DDE2E5] py-[10px] font-lato text-[14px] font-medium text-[#374151] transition-colors hover:bg-[#F9FAFB] disabled:opacity-50"
					>
						Cancel
					</button>
					<button
						onClick={onConfirm}
						disabled={loading}
						className={`flex flex-1 items-center justify-center gap-[8px] rounded-[8px] py-[10px] font-lato text-[14px] font-medium transition-colors disabled:opacity-50 ${confirmStyles[color]}`}
					>
						{loading && <span className="inline-block h-[13px] w-[13px] animate-spin rounded-full border-[2px] border-white border-t-transparent" />}
						{loading ? 'Processing…' : confirmLabel}
					</button>
				</div>
			</div>
		</div>
	);
}

// ── Provider logo SVGs (inline, no network dependency) ──────────────────────

function AnthropicLogo({ size = 28 }) {
	return (
		<svg width={size} height={size} viewBox="0 0 46 32" fill="none" xmlns="http://www.w3.org/2000/svg">
			<path d="M32.73 0h-6.945L38.74 32h6.945L32.73 0Z" fill="#181818"/>
			<path d="M13.055 0 0.315 32h7.109l2.656-6.8h13.6l2.656 6.8h7.11L18.705 0h-5.65Zm-.78 19.367 4.44-11.371 4.44 11.371h-8.88Z" fill="#181818"/>
		</svg>
	);
}

function OpenAILogo({ size = 28 }) {
	return (
		<svg width={size} height={size} viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
			<path d="M29.71 13.09A8.09 8.09 0 0 0 20.78 4a8.1 8.1 0 0 0-13.7 3A8.1 8.1 0 0 0 2.29 18.9 8.1 8.1 0 0 0 11.22 28a8.09 8.09 0 0 0 13.69-3A8.1 8.1 0 0 0 29.71 13.09Zm-12.4 17.3a6 6 0 0 1-3.84-1.39l.19-.11 6.37-3.68a1 1 0 0 0 .53-.92v-8.98l2.69 1.56a.09.09 0 0 1 .05.07v7.44a6 6 0 0 1-6 6.01Zm-12.89-5.5a6 6 0 0 1-.72-4 5.89 5.89 0 0 0 1 .17l6.37 3.68a1 1 0 0 0 1.06 0l7.78-4.49v3.12a.1.1 0 0 1-.04.08L13.48 27a6 6 0 0 1-8.06-2.11ZM3.29 10.52a6 6 0 0 1 3.13-2.64v7.58a1 1 0 0 0 .51.9l7.75 4.47-2.7 1.56a.1.1 0 0 1-.09 0L5.41 18.4a6 6 0 0 1-2.12-7.88Zm22.13 5.15-7.78-4.52 2.7-1.55a.1.1 0 0 1 .09 0l6.48 3.74a6 6 0 0 1-.93 10.82v-7.58a1.06 1.06 0 0 0-.56-.91Zm2.68-4.06a5.9 5.9 0 0 0-1-.17l-6.37-3.68a1 1 0 0 0-1.06 0L11.9 12.25V9.13a.09.09 0 0 1 .04-.08L18.43 5a6 6 0 0 1 9 6.61ZM10.55 17.1l-2.69-1.55a.09.09 0 0 1-.05-.07V8.03a6 6 0 0 1 9.84-4.6l-.19.11-6.37 3.68a1 1 0 0 0-.53.91l-.01 8.97Zm1.46-3.15 3.46-2 3.46 2v4l-3.46 2-3.46-2v-4Z" fill="#181818"/>
		</svg>
	);
}

function AzureLogo({ size = 28 }) {
	return (
		<svg width={size} height={size} viewBox="0 0 96 96" xmlns="http://www.w3.org/2000/svg">
			<defs>
				<linearGradient id="az1" x1="0.957" y1="39.859" x2="0.458" y2="40.44" gradientUnits="userSpaceOnUse">
					<stop offset="0" stopColor="#114a8b"/>
					<stop offset="1" stopColor="#0669bc"/>
				</linearGradient>
				<linearGradient id="az2" x1="0.654" y1="39.92" x2="0.946" y2="40.198" gradientUnits="userSpaceOnUse">
					<stop offset="0" stopOpacity=".3"/>
					<stop offset=".071" stopOpacity=".2"/>
					<stop offset=".321" stopOpacity=".1"/>
					<stop offset=".623" stopOpacity=".05"/>
					<stop offset="1" stopOpacity="0"/>
				</linearGradient>
				<linearGradient id="az3" x1="0.372" y1="39.128" x2="0.796" y2="40.473" gradientUnits="userSpaceOnUse">
					<stop offset="0" stopColor="#3ccbf4"/>
					<stop offset="1" stopColor="#2892df"/>
				</linearGradient>
			</defs>
			<path d="M33.338 6.544h26.038l-27.03 80.087a4.152 4.152 0 0 1-3.933 2.824H8.149a4.145 4.145 0 0 1-3.928-5.47L29.405 9.368a4.152 4.152 0 0 1 3.933-2.824z" fill="url(#az1)"/>
			<path d="M71.175 60.261h-41.29L53.44 6.544H29.395A4.15 4.15 0 0 0 25.47 9.37L.222 83.985a4.145 4.145 0 0 0 3.928 5.47h20.343a4.15 4.15 0 0 0 3.896-2.693z" fill="#0078d4"/>
			<path d="M33.338 6.544a4.12 4.12 0 0 0-3.924 2.848L.247 83.951a4.14 4.14 0 0 0 3.902 5.504h20.484a4.45 4.45 0 0 0 3.415-2.82l4.918-14.507 17.582 16.335a4.24 4.24 0 0 0 2.65.992H74.59L62.194 60.1l-17.055.005L59.47 6.544z" fill="url(#az2)"/>
			<path d="M66.595 9.368A4.145 4.145 0 0 0 62.67 6.54H33.648a4.145 4.145 0 0 1 3.925 2.828l25.184 74.616a4.145 4.145 0 0 1-3.925 5.472h29.02a4.145 4.145 0 0 0 3.924-5.472z" fill="url(#az3)"/>
		</svg>
	);
}

function BedrockLogo({ size = 28 }) {
	return (
		<svg width={size} height={size} viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
			<rect width="32" height="32" rx="4" fill="#232F3E"/>
			<path d="M16 4L4 10.5V21.5L16 28L28 21.5V10.5L16 4Z" fill="#FF9900"/>
			<path d="M16 4L28 10.5V21.5L16 28V4Z" fill="#FF9900" opacity="0.7"/>
			<path d="M16 4L4 10.5L16 17L28 10.5L16 4Z" fill="white" opacity="0.15"/>
			<text x="16" y="20" textAnchor="middle" fill="white" fontSize="9" fontFamily="sans-serif" fontWeight="bold">BR</text>
		</svg>
	);
}

const PROVIDER_LOGOS = {
	anthropic:    AnthropicLogo,
	openai:       OpenAILogo,
	azure_openai: AzureLogo,
	bedrock:      BedrockLogo,
};

const PROVIDER_META = {
	anthropic:    { bg: '#F5F2FF', border: '#E5DEFF', accent: '#6B5CE7', description: 'Claude Opus, Sonnet & Haiku' },
	openai:       { bg: '#F0FDF9', border: '#D1FAE5', accent: '#059669', description: 'GPT-4o, o3, o4-mini & more' },
	azure_openai: { bg: '#EFF6FF', border: '#DBEAFE', accent: '#2563EB', description: 'Azure-hosted OpenAI deployments' },
	bedrock:      { bg: '#FFFBEB', border: '#FDE68A', accent: '#D97706', description: 'AWS-managed foundation models' },
};

function CapabilityChip({ label, active }) {
	if (!active) return null;
	return (
		<span className="rounded-[4px] bg-[#EFF6FF] px-[6px] py-[2px] font-lato text-[11px] font-medium text-[#346BD4]">
			{label}
		</span>
	);
}

function ModelCard({ model, selected, onClick }) {
	const contextK = model.context_window ? `${Math.round(model.context_window / 1000)}K ctx` : null;
	const maxOut = model.max_output_tokens ? `${Math.round(model.max_output_tokens / 1000)}K out` : null;
	return (
		<button
			type="button"
			onClick={onClick}
			className={`w-full rounded-[8px] border p-[12px] text-left transition-all ${
				selected
					? 'border-[#5048ED] bg-[#F5F3FF] ring-1 ring-[#5048ED]'
					: 'border-[#E5E7EB] bg-white hover:border-[#C4B5FD] hover:bg-[#FAFAFA]'
			}`}
		>
			<div className="flex items-start justify-between gap-[8px]">
				<div className="min-w-0 flex-1">
					<p className="truncate font-lato text-[13px] font-semibold text-[#111827]">
						{model.name && model.name !== model.id ? model.name : model.id}
					</p>
					{model.name && model.name !== model.id && (
						<p className="mt-[1px] truncate font-mono text-[11px] text-[#9CA3AF]">{model.id}</p>
					)}
				</div>
				{selected && (
					<span className="mt-[1px] shrink-0">
						<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
							<circle cx="8" cy="8" r="7" fill="#5048ED"/>
							<path d="M5 8L7 10L11 6" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
						</svg>
					</span>
				)}
			</div>
			<div className="mt-[8px] flex flex-wrap items-center gap-[4px]">
				{contextK && <span className="rounded-[4px] bg-[#F3F4F6] px-[6px] py-[2px] font-lato text-[11px] text-[#6B7280]">{contextK}</span>}
				{maxOut && <span className="rounded-[4px] bg-[#F3F4F6] px-[6px] py-[2px] font-lato text-[11px] text-[#6B7280]">{maxOut}</span>}
				<CapabilityChip label="Vision" active={model.supports_vision} />
				<CapabilityChip label="Tools" active={model.supports_tools} />
				<CapabilityChip label="Streaming" active={model.supports_streaming} />
			</div>
		</button>
	);
}

function ModelSkeletonCard() {
	return (
		<div className="animate-pulse rounded-[8px] border border-[#E5E7EB] bg-white p-[12px]">
			<div className="mb-[8px] h-[14px] w-[60%] rounded bg-[#F3F4F6]" />
			<div className="h-[11px] w-[40%] rounded bg-[#F3F4F6]" />
			<div className="mt-[8px] flex gap-[4px]">
				<div className="h-[18px] w-[40px] rounded bg-[#F3F4F6]" />
				<div className="h-[18px] w-[32px] rounded bg-[#F3F4F6]" />
				<div className="h-[18px] w-[36px] rounded bg-[#F3F4F6]" />
			</div>
		</div>
	);
}

// Step indicator shown at the top of the drawer
function StepIndicator({ step }) {
	const steps = ['Provider & Credentials', 'Choose Model', 'Configuration'];
	return (
		<div className="flex items-center gap-0">
			{steps.map((label, i) => {
				const idx = i + 1;
				const done = step > idx;
				const active = step === idx;
				return (
					<div key={idx} className="flex items-center">
						<div className="flex flex-col items-center">
							<div className={`flex h-[22px] w-[22px] items-center justify-center rounded-full text-[11px] font-semibold transition-all ${
								done ? 'bg-[#5048ED] text-white' : active ? 'bg-[#5048ED] text-white ring-4 ring-[#EEF2FF]' : 'bg-[#F3F4F6] text-[#9CA3AF]'
							}`}>
								{done ? (
									<svg width="10" height="10" viewBox="0 0 10 10" fill="none">
										<path d="M2 5L4 7L8 3" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
									</svg>
								) : idx}
							</div>
							<span className={`mt-[4px] whitespace-nowrap font-lato text-[10px] font-medium ${active ? 'text-[#5048ED]' : done ? 'text-[#6B7280]' : 'text-[#9CA3AF]'}`}>
								{label}
							</span>
						</div>
						{i < steps.length - 1 && (
							<div className={`mx-[6px] mb-[14px] h-[1px] w-[24px] transition-colors ${done ? 'bg-[#5048ED]' : 'bg-[#E5E7EB]'}`} />
						)}
					</div>
				);
			})}
		</div>
	);
}

function AddProviderWizard({ onSubmit, availableProviders, appId, triggerApi }) {
	const [step, setStep] = useState(1);
	const [selectedSlug, setSelectedSlug] = useState('');
	const [credentials, setCredentials] = useState({});        // raw form values
	const [fetchState, setFetchState] = useState({ status: 'idle', models: [], error: null });
	const [selectedModel, setSelectedModel] = useState('');
	const [modelSearch, setModelSearch] = useState('');
	const [isSubmitting, setIsSubmitting] = useState(false);

	// Config
	const [name, setName] = useState('');
	const [description, setDescription] = useState('');
	const [rateLimitRpm, setRateLimitRpm] = useState('');
	const [monthlyBudget, setMonthlyBudget] = useState('');

	const selectedProvider = availableProviders.find((p) => p.slug === selectedSlug);
	const configFields = selectedProvider?.config_fields || [];
	const credentialFields = configFields.filter(
		(f) => !(f.type === 'select' && f.options_from === 'supported_models') && f.type !== 'integer'
	);
	const optionalFields = configFields.filter((f) => f.type === 'integer');

	// Reset everything when provider changes
	useEffect(() => {
		setCredentials({});
		setFetchState({ status: 'idle', models: [], error: null });
		setSelectedModel('');
		setModelSearch('');
	}, [selectedSlug]);

	const buildConfig = () => {
		const config = {};
		configFields.forEach((field) => {
			if (field.type === 'select' && field.options_from === 'supported_models') return;
			const val = credentials[field.name];
			if (val !== undefined && val !== '') {
				config[field.name] = field.type === 'integer' ? parseInt(val, 10) : val;
			} else if (field.default !== undefined) {
				config[field.name] = field.default;
			}
		});
		return config;
	};

	// Called when user clicks Continue on step 1 — validates credentials by fetching models
	const handleStep1Continue = async () => {
		// Show inline validating state on step 1 before moving
		setFetchState({ status: 'loading', models: [], error: null });

		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/ai/providers/fetch-models/`,
			type: 'POST',
			loader: false,
			showErrorModal: false,
			payload: { provider_slug: selectedSlug, config: buildConfig() },
		});

		if (success && response?.models?.length > 0) {
			// Valid key + models returned — advance
			const models = response.models;
			setFetchState({ status: 'success', models, error: null });
			setSelectedModel(models[0].id);
			setStep(2);
		} else {
			const message = response?.message || 'Could not fetch models from the provider.';
			// Backend classifies errors as 'auth_error' (block step 2) or 'unknown_error' (fallback)
			const errorType = response?.error_type || 'unknown_error';
			const fallbackModels = selectedProvider?.supported_models || [];

			if (errorType === 'auth_error' || fallbackModels.length === 0) {
				// Invalid credentials OR provider has no static fallback models (e.g. Bedrock, Azure)
				// — stay on step 1, show error inline
				setFetchState({ status: 'auth_error', models: [], error: message });
			} else {
				// Unknown error but provider has static fallback models — advance with them
				setFetchState({ status: 'error', models: fallbackModels, error: message });
				setSelectedModel(fallbackModels[0].id);
				setStep(2);
			}
		}
	};

	const handleStep1Back = () => { setStep(1); setModelSearch(''); };
	const handleStep2Continue = () => setStep(3);

	const handleSubmit = async () => {
		setIsSubmitting(true);
		await onSubmit({
			name,
			description,
			provider_slug: selectedSlug,
			config: buildConfig(),
			default_model: selectedModel,
			fetched_models: displayModels,   // send the live-fetched list to the backend
			rate_limit_rpm: rateLimitRpm ? parseInt(rateLimitRpm, 10) : null,
			monthly_budget_usd: monthlyBudget || null,
		});
		setIsSubmitting(false);
	};

	// Validation gates per step
	const step1Valid = selectedSlug && credentialFields.every((f) => {
		if (!f.required) return true;
		const val = credentials[f.name];
		return val !== undefined && val !== '';
	});
	const step2Valid = !!selectedModel;
	const step3Valid = name.trim().length > 0;

	const displayModels = fetchState.models.length > 0
		? fetchState.models
		: (selectedProvider?.supported_models || []);

	const filteredModels = modelSearch.trim()
		? displayModels.filter((m) => {
			const q = modelSearch.toLowerCase();
			return (
				m.id.toLowerCase().includes(q) ||
				(m.name && m.name.toLowerCase().includes(q))
			);
		  })
		: displayModels;

	return (
		<div className="flex flex-col">
			{/* Step indicator */}
			<div className="mb-[24px] flex justify-center">
				<StepIndicator step={step} />
			</div>

			{/* ── Step 1: Provider + Credentials ── */}
			{step === 1 && (
				<div className="flex flex-col gap-[20px]">
					{/* Provider picker — logo cards */}
					<div>
						<label className="font-lato text-[12px] font-semibold uppercase tracking-[0.6px] text-[#6C747D]">
							Select a Provider
						</label>
						<div className="mt-[10px] grid grid-cols-2 gap-[10px]">
							{availableProviders.map((p) => {
								const meta = PROVIDER_META[p.slug] || { bg: '#F9FAFB', border: '#E5E7EB', accent: '#6B7280', description: '' };
								const Logo = PROVIDER_LOGOS[p.slug];
								const isSelected = selectedSlug === p.slug;
								return (
									<button
										key={p.slug}
										type="button"
										onClick={() => setSelectedSlug(p.slug)}
										className={`group relative flex flex-col gap-[12px] rounded-[12px] border-2 p-[16px] text-left transition-all duration-150 ${
											isSelected
												? 'border-[#5048ED] shadow-[0_0_0_3px_rgba(80,72,237,0.12)]'
												: 'border-[#E5E7EB] hover:border-[#C4B5FD] hover:shadow-sm'
										}`}
										style={{ backgroundColor: isSelected ? meta.bg : 'white' }}
									>
										{/* Selected checkmark */}
										{isSelected && (
											<span className="absolute right-[10px] top-[10px]">
												<svg width="18" height="18" viewBox="0 0 18 18" fill="none">
													<circle cx="9" cy="9" r="9" fill="#5048ED"/>
													<path d="M5.5 9L7.5 11L12.5 6.5" stroke="white" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
												</svg>
											</span>
										)}
										{/* Logo */}
										<div className={`flex h-[44px] w-[44px] items-center justify-center rounded-[10px] border p-[8px] transition-colors`}
											style={{ borderColor: isSelected ? meta.border : '#F3F4F6', backgroundColor: isSelected ? 'white' : '#F9FAFB' }}>
											{Logo ? <Logo size={26} /> : (
												<span className="font-semibold text-[15px]" style={{ color: meta.accent }}>
													{p.display_name[0]}
												</span>
											)}
										</div>
										{/* Text */}
										<div>
											<p className="font-lato text-[14px] font-semibold text-[#111827]">{p.display_name}</p>
											<p className="mt-[2px] font-lato text-[12px] leading-[16px] text-[#6B7280]">{meta.description}</p>
										</div>
									</button>
								);
							})}
						</div>
					</div>

					{/* Credential fields — animate in when provider selected */}
					{selectedSlug && credentialFields.length > 0 && (
						<div className="flex flex-col gap-[16px]">
							<div className="h-[1px] bg-[#F3F4F6]" />
							<p className="font-lato text-[12px] font-semibold uppercase tracking-[0.6px] text-[#6C747D]">
								Credentials
							</p>
							{credentialFields.map((field) => {
								const inputType = field.type === 'secret' ? 'password' : 'text';
								return (
									<div key={field.name}>
										<label className="font-lato text-[12px] font-semibold text-[#A3ABB1]">
											{field.label}{field.required && <span className="ml-[2px] text-[#EF4444]">*</span>}
										</label>
										<input
											type={inputType}
											value={credentials[field.name] || ''}
											onChange={(e) => {
												setCredentials((prev) => ({ ...prev, [field.name]: e.target.value }));
												if (fetchState.status === 'auth_error') setFetchState({ status: 'idle', models: [], error: null });
											}}
											placeholder={field.help_text || `Enter ${field.label.toLowerCase()}`}
											className={`mt-[4px] w-full rounded-[6px] border px-[16px] py-[14px] font-lato text-[14px] placeholder:text-[#9A9A9A] focus:outline-0 ${fetchState.status === 'auth_error' && field.type === 'secret' ? 'border-[#FCA5A5] bg-[#FFF8F8]' : 'border-[#DDE2E5]'}`}
										/>
									</div>
								);
							})}
						</div>
					)}

					{/* Auth error banner — only shown on step 1 when credentials are invalid */}
					{fetchState.status === 'auth_error' && (
						<div className="flex items-start gap-[10px] rounded-[8px] border border-[#FECACA] bg-[#FEF2F2] px-[14px] py-[12px]">
							<svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="mt-[1px] shrink-0">
								<circle cx="8" cy="8" r="7" stroke="#EF4444" strokeWidth="1.3" fill="none"/>
								<path d="M8 4.5V8.5M8 10.5H8.01" stroke="#EF4444" strokeWidth="1.4" strokeLinecap="round"/>
							</svg>
							<div>
								<p className="font-lato text-[13px] font-semibold text-[#991B1B]">Invalid credentials</p>
								<p className="mt-[2px] font-lato text-[12px] leading-[18px] text-[#DC2626]">{fetchState.error}</p>
								<p className="mt-[4px] font-lato text-[11px] text-[#6B7280]">Please check your API key and try again.</p>
							</div>
						</div>
					)}

					<div className="mt-[24px]">
						<button
							type="button"
							onClick={handleStep1Continue}
							disabled={!step1Valid || fetchState.status === 'loading'}
							className="flex w-full items-center justify-center gap-[8px] rounded-[8px] bg-[#5048ED] py-[12px] font-lato text-[14px] font-medium text-white transition-colors hover:bg-[#4338CA] disabled:cursor-not-allowed disabled:opacity-40"
						>
							{fetchState.status === 'loading' ? (
								<>
									<span className="inline-block h-[14px] w-[14px] animate-spin rounded-full border-[2px] border-white border-t-transparent" />
									Validating credentials…
								</>
							) : (
								<>
									Continue — Fetch available models
									<svg width="14" height="14" viewBox="0 0 14 14" fill="none">
										<path d="M3 7H11M8 4L11 7L8 10" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
									</svg>
								</>
							)}
						</button>
					</div>
				</div>
			)}

			{/* ── Step 2: Choose Model ── */}
			{step === 2 && (
				<div className="flex flex-col gap-[16px]">
					<div className="flex items-center gap-[8px]">
						<button
							type="button"
							onClick={handleStep1Back}
							className="flex items-center gap-[4px] font-lato text-[12px] text-[#6B7280] hover:text-[#111827]"
						>
							<svg width="12" height="12" viewBox="0 0 12 12" fill="none">
								<path d="M9 6H3M5 3L3 6L5 9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
							</svg>
							Back
						</button>
						<span className="font-lato text-[12px] text-[#D1D5DB]">·</span>
						<span className="font-lato text-[12px] text-[#6B7280]">
							{selectedProvider?.display_name}
						</span>
					</div>

					{/* Loading skeletons */}
					{fetchState.status === 'loading' && (
						<div className="flex flex-col gap-[8px]">
							<p className="font-lato text-[12px] text-[#9CA3AF]">Fetching models from the API…</p>
							{[1, 2, 3].map((i) => <ModelSkeletonCard key={i} />)}
						</div>
					)}

					{/* Error banner — still shows static fallback below if available */}
					{fetchState.status === 'error' && (
						<div className="flex items-start gap-[8px] rounded-[8px] border border-[#FCA5A5] bg-[#FEF2F2] px-[12px] py-[10px]">
							<svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="mt-[1px] shrink-0">
								<circle cx="7" cy="7" r="6" stroke="#EF4444" strokeWidth="1.2" fill="none"/>
								<path d="M7 4V7.5M7 9.5H7.01" stroke="#EF4444" strokeWidth="1.2" strokeLinecap="round"/>
							</svg>
							<div>
								<p className="font-lato text-[12px] font-semibold text-[#DC2626]">Could not fetch live models</p>
								<p className="mt-[2px] font-lato text-[11px] leading-[16px] text-[#DC2626]">{fetchState.error}</p>
								{displayModels.length > 0 && (
									<p className="mt-[4px] font-lato text-[11px] text-[#6B7280]">Showing known models — you can still continue.</p>
								)}
							</div>
						</div>
					)}

					{/* Search + model cards */}
					{fetchState.status !== 'loading' && displayModels.length > 0 && (
						<>
							<div className="flex items-center justify-between">
								{fetchState.status === 'success' && (
									<div className="flex items-center gap-[6px]">
										<svg width="12" height="12" viewBox="0 0 12 12" fill="none">
											<circle cx="6" cy="6" r="5" fill="#10B981"/>
											<path d="M3.5 6L5 7.5L8.5 4" stroke="white" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
										</svg>
										<p className="font-lato text-[12px] text-[#10B981]">
											{displayModels.length} model{displayModels.length !== 1 ? 's' : ''} fetched live
										</p>
									</div>
								)}
								{fetchState.status !== 'success' && <span />}
								<p className="font-lato text-[11px] text-[#9CA3AF]">
									{filteredModels.length}/{displayModels.length} shown
								</p>
							</div>

							{/* Search input */}
							<div className="relative">
								<svg
									width="14" height="14" viewBox="0 0 14 14" fill="none"
									className="absolute left-[10px] top-1/2 -translate-y-1/2 text-[#9CA3AF]"
								>
									<circle cx="6" cy="6" r="4.5" stroke="currentColor" strokeWidth="1.2"/>
									<path d="M9.5 9.5L12 12" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
								</svg>
								<input
									type="text"
									value={modelSearch}
									onChange={(e) => setModelSearch(e.target.value)}
									placeholder="Search models…"
									className="w-full rounded-[6px] border border-[#DDE2E5] py-[8px] pl-[30px] pr-[10px] font-lato text-[13px] placeholder:text-[#9CA3AF] focus:outline-0 focus:border-[#5048ED]"
								/>
								{modelSearch && (
									<button
										type="button"
										onClick={() => setModelSearch('')}
										className="absolute right-[8px] top-1/2 -translate-y-1/2 text-[#9CA3AF] hover:text-[#6B7280]"
									>
										<svg width="12" height="12" viewBox="0 0 12 12" fill="none">
											<path d="M3 3L9 9M9 3L3 9" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
										</svg>
									</button>
								)}
							</div>

							<div className="flex flex-col gap-[8px]">
								{filteredModels.length > 0 ? filteredModels.map((m) => (
									<ModelCard
										key={m.id}
										model={m}
										selected={selectedModel === m.id}
										onClick={() => setSelectedModel(m.id)}
									/>
								)) : (
									<div className="rounded-[8px] border border-dashed border-[#E5E7EB] px-[16px] py-[24px] text-center">
										<p className="font-lato text-[13px] text-[#9CA3AF]">No models match "{modelSearch}"</p>
										<button
											type="button"
											onClick={() => setModelSearch('')}
											className="mt-[6px] font-lato text-[12px] text-[#5048ED] hover:underline"
										>
											Clear search
										</button>
									</div>
								)}
							</div>
						</>
					)}

					{fetchState.status !== 'loading' && displayModels.length === 0 && (
						<div className="rounded-[8px] border border-dashed border-[#E5E7EB] px-[16px] py-[32px] text-center">
							<p className="font-lato text-[13px] text-[#9CA3AF]">No models returned by the provider</p>
						</div>
					)}

					<div className="mt-[24px]">
						<button
							type="button"
							onClick={handleStep2Continue}
							disabled={!step2Valid}
							className="flex w-full items-center justify-center gap-[8px] rounded-[8px] bg-[#5048ED] py-[12px] font-lato text-[14px] font-medium text-white transition-colors hover:bg-[#4338CA] disabled:cursor-not-allowed disabled:opacity-40"
						>
							Continue — Configure provider
							<svg width="14" height="14" viewBox="0 0 14 14" fill="none">
								<path d="M3 7H11M8 4L11 7L8 10" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
							</svg>
						</button>
					</div>
				</div>
			)}

			{/* ── Step 3: Name + Limits ── */}
			{step === 3 && (
				<div className="flex flex-col gap-[20px]">
					<div className="flex items-center gap-[8px]">
						<button
							type="button"
							onClick={() => setStep(2)}
							className="flex items-center gap-[4px] font-lato text-[12px] text-[#6B7280] hover:text-[#111827]"
						>
							<svg width="12" height="12" viewBox="0 0 12 12" fill="none">
								<path d="M9 6H3M5 3L3 6L5 9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
							</svg>
							Back
						</button>
					</div>

					{/* Summary chip */}
					{(() => {
						const Logo = PROVIDER_LOGOS[selectedSlug];
						const meta = PROVIDER_META[selectedSlug] || {};
						return (
							<div className="flex items-center gap-[12px] rounded-[10px] border bg-[#F9FAFB] px-[14px] py-[10px]"
								style={{ borderColor: meta.border || '#E5E7EB' }}>
								<div className="flex h-[36px] w-[36px] shrink-0 items-center justify-center rounded-[8px] border bg-white p-[6px]"
									style={{ borderColor: meta.border || '#E5E7EB' }}>
									{Logo ? <Logo size={22} /> : <span className="text-[13px] font-bold" style={{ color: meta.accent }}>{selectedSlug[0]?.toUpperCase()}</span>}
								</div>
								<div>
									<p className="font-lato text-[13px] font-semibold text-[#111827]">{selectedProvider?.display_name}</p>
									<p className="font-mono text-[11px] text-[#9CA3AF]">{selectedModel}</p>
								</div>
							</div>
						);
					})()}

					<div className="flex flex-col gap-[16px]">
						<div>
							<label className="font-lato text-[12px] font-semibold text-[#A3ABB1]">
								Configuration Name <span className="text-[#EF4444]">*</span>
							</label>
							<input
								type="text"
								value={name}
								onChange={(e) => setName(e.target.value)}
								placeholder="e.g. claude-primary, gpt4-fallback"
								className="mt-[4px] w-full rounded-[6px] border border-[#DDE2E5] px-[16px] py-[14px] font-lato text-[14px] placeholder:text-[#9A9A9A] focus:outline-0"
							/>
						</div>
						<div>
							<label className="font-lato text-[12px] font-semibold text-[#A3ABB1]">Description</label>
							<input
								type="text"
								value={description}
								onChange={(e) => setDescription(e.target.value)}
								placeholder="e.g. Primary provider for production"
								className="mt-[4px] w-full rounded-[6px] border border-[#DDE2E5] px-[16px] py-[14px] font-lato text-[14px] placeholder:text-[#9A9A9A] focus:outline-0"
							/>
						</div>

						{/* Optional integer config fields (max_retries, timeout) */}
						{optionalFields.length > 0 && (
							<>
								<div className="h-[1px] bg-[#F3F4F6]" />
								{optionalFields.map((field) => (
									<div key={field.name}>
										<label className="font-lato text-[12px] font-semibold text-[#A3ABB1]">{field.label}</label>
										<input
											type="number"
											value={credentials[field.name] || field.default || ''}
											onChange={(e) => setCredentials((prev) => ({ ...prev, [field.name]: e.target.value }))}
											placeholder={field.help_text || ''}
											className="mt-[4px] w-full rounded-[6px] border border-[#DDE2E5] px-[16px] py-[14px] font-lato text-[14px] placeholder:text-[#9A9A9A] focus:outline-0"
										/>
									</div>
								))}
							</>
						)}

						<div className="h-[1px] bg-[#F3F4F6]" />
						<p className="font-lato text-[12px] font-semibold uppercase tracking-[0.6px] text-[#6C747D]">
							Limits <span className="normal-case text-[#9CA3AF] tracking-normal font-normal">(optional)</span>
						</p>
						<div className="grid grid-cols-2 gap-[12px]">
							<div>
								<label className="font-lato text-[12px] font-semibold text-[#A3ABB1]">Rate limit (req/min)</label>
								<input
									type="number"
									value={rateLimitRpm}
									onChange={(e) => setRateLimitRpm(e.target.value)}
									placeholder="Unlimited"
									className="mt-[4px] w-full rounded-[6px] border border-[#DDE2E5] px-[16px] py-[14px] font-lato text-[14px] placeholder:text-[#9A9A9A] focus:outline-0"
								/>
							</div>
							<div>
								<label className="font-lato text-[12px] font-semibold text-[#A3ABB1]">Monthly budget (USD)</label>
								<input
									type="number"
									value={monthlyBudget}
									onChange={(e) => setMonthlyBudget(e.target.value)}
									placeholder="Unlimited"
									className="mt-[4px] w-full rounded-[6px] border border-[#DDE2E5] px-[16px] py-[14px] font-lato text-[14px] placeholder:text-[#9A9A9A] focus:outline-0"
								/>
							</div>
						</div>
					</div>

					<div className="mt-[24px]">
						<button
							type="button"
							onClick={handleSubmit}
							disabled={!step3Valid || isSubmitting}
							className="flex w-full items-center justify-center gap-[8px] rounded-[8px] bg-[#5048ED] py-[12px] font-lato text-[14px] font-medium text-white transition-colors hover:bg-[#4338CA] disabled:cursor-not-allowed disabled:opacity-40"
						>
							{isSubmitting ? (
								<>
									<span className="inline-block h-[14px] w-[14px] animate-spin rounded-full border-[2px] border-white border-t-transparent" />
									Adding provider…
								</>
							) : 'Add Provider'}
						</button>
					</div>
				</div>
			)}
		</div>
	);
}

function EditProviderForm({ provider, availableProviders, onSave, onClose, appId, triggerApi }) {
	const meta = PROVIDER_META[provider.provider_slug] || { bg: '#F9FAFB', border: '#E5E7EB', accent: '#6B7280' };
	const Logo = PROVIDER_LOGOS[provider.provider_slug];
	const providerMeta = availableProviders.find((p) => p.slug === provider.provider_slug);
	const configFields = providerMeta?.config_fields || [];
	const credentialFields = configFields.filter(
		(f) => !(f.type === 'select' && f.options_from === 'supported_models') && f.type !== 'integer'
	);

	const [name, setName] = useState(provider.name || '');
	const [description, setDescription] = useState(provider.description || '');
	const [rateLimitRpm, setRateLimitRpm] = useState(provider.rate_limit_rpm || '');
	const [monthlyBudget, setMonthlyBudget] = useState(provider.monthly_budget_usd || '');
	const [fallbackModel, setFallbackModel] = useState(provider.default_model || '');
	const [modelSearch, setModelSearch] = useState('');
	const [modelPickerOpen, setModelPickerOpen] = useState(false);
	const [models, setModels] = useState(provider.enabled_models || []);
	// Secret fields start empty — user must re-enter to update, blank = keep existing
	const [credentials, setCredentials] = useState(() => {
		const init = {};
		credentialFields.forEach((f) => { init[f.name] = ''; });
		return init;
	});
	const [isSubmitting, setIsSubmitting] = useState(false);

	// Fetch live models if available (non-blocking, augments the enabled_models list)
	useEffect(() => {
		const maskedConfig = provider.masked_config || {};
		const config = {};
		credentialFields.forEach((f) => {
			if (maskedConfig[f.name] != null) config[f.name] = maskedConfig[f.name];
		});
		if (!Object.keys(config).length) return;
		triggerApi({
			url: `/api/v1/apps/${appId}/ai/providers/fetch-models/`,
			type: 'POST',
			loader: false,
			showErrorModal: false,
			payload: { provider_slug: provider.provider_slug, config },
		}).then(({ response, success }) => {
			if (success && response?.models?.length > 0) setModels(response.models.map((m) => ({ model_id: m.id, display_name: m.name || m.id, is_enabled: true })));
		});
	}, []);

	const filteredModels = modelSearch.trim()
		? models.filter((m) => m.model_id.toLowerCase().includes(modelSearch.toLowerCase()) || (m.display_name || '').toLowerCase().includes(modelSearch.toLowerCase()))
		: models;

	const handleSave = async () => {
		setIsSubmitting(true);
		const config = {};
		credentialFields.forEach((f) => {
			const val = credentials[f.name];
			// Only include if the user actually typed something
			if (val !== undefined && val !== '') {
				config[f.name] = val;
			}
		});
		await onSave({ name, description, config: Object.keys(config).length ? config : undefined, default_model: fallbackModel, rate_limit_rpm: rateLimitRpm ? parseInt(rateLimitRpm, 10) : null, monthly_budget_usd: monthlyBudget || null });
		setIsSubmitting(false);
	};

	return (
		<div className="flex flex-col gap-[20px] px-[24px] py-[24px]">
			{/* Provider identity chip */}
			<div className="flex items-center gap-[12px] rounded-[10px] border bg-[#F9FAFB] px-[14px] py-[10px]"
				style={{ borderColor: meta.border }}>
				<div className="flex h-[36px] w-[36px] shrink-0 items-center justify-center rounded-[8px] border bg-white p-[6px]"
					style={{ borderColor: meta.border }}>
					{Logo ? <Logo size={22} /> : <span className="text-[13px] font-bold" style={{ color: meta.accent }}>{provider.provider_slug[0]?.toUpperCase()}</span>}
				</div>
				<div>
					<p className="font-lato text-[13px] font-semibold text-[#111827]">{providerMeta?.display_name || provider.provider_slug}</p>
					<p className="font-mono text-[11px] text-[#9CA3AF]">{provider.default_model}</p>
				</div>
			</div>

			{/* Name & description */}
			<div>
				<label className="font-lato text-[12px] font-semibold text-[#A3ABB1]">
					Configuration Name <span className="text-[#EF4444]">*</span>
				</label>
				<input type="text" value={name} onChange={(e) => setName(e.target.value)}
					className="mt-[4px] w-full rounded-[6px] border border-[#DDE2E5] px-[16px] py-[12px] font-lato text-[14px] placeholder:text-[#9A9A9A] focus:outline-0 focus:border-[#5048ED]" />
			</div>
			<div>
				<label className="font-lato text-[12px] font-semibold text-[#A3ABB1]">Description</label>
				<input type="text" value={description} onChange={(e) => setDescription(e.target.value)}
					placeholder="Optional description"
					className="mt-[4px] w-full rounded-[6px] border border-[#DDE2E5] px-[16px] py-[12px] font-lato text-[14px] placeholder:text-[#9A9A9A] focus:outline-0 focus:border-[#5048ED]" />
			</div>

			{/* Credentials */}
			{credentialFields.length > 0 && (
				<>
					<div className="h-[1px] bg-[#F3F4F6]" />
					<p className="font-lato text-[12px] font-semibold uppercase tracking-[0.6px] text-[#6C747D]">Credentials</p>
					<p className="font-lato text-[12px] text-[#9CA3AF]">
						Leave blank to keep existing credentials. Only fill in what you want to update.
					</p>
					{credentialFields.map((field) => (
						<div key={field.name}>
							<label className="font-lato text-[12px] font-semibold text-[#A3ABB1]">{field.label}</label>
							<input
								type={field.type === 'secret' ? 'password' : 'text'}
								value={credentials[field.name] || ''}
								onChange={(e) => setCredentials((prev) => ({ ...prev, [field.name]: e.target.value }))}
								placeholder="Leave blank to keep existing"
								className="mt-[4px] w-full rounded-[6px] border border-[#DDE2E5] px-[16px] py-[12px] font-lato text-[14px] placeholder:text-[#9A9A9A] focus:outline-0 focus:border-[#5048ED]"
							/>
						</div>
					))}
				</>
			)}

			{/* Fallback Model */}
			{models.length > 0 && (
				<>
					<div className="h-[1px] bg-[#F3F4F6]" />
					<div>
						<div className="mb-[8px] flex items-center justify-between">
							<div>
								<label className="font-lato text-[12px] font-semibold uppercase tracking-[0.6px] text-[#6C747D]">Fallback Model</label>
								<p className="mt-[1px] font-lato text-[11px] text-[#9CA3AF]">
									Used when no model is specified in direct <code className="rounded bg-[#F3F4F6] px-[3px] text-[10px]">provider.complete()</code> calls.
								</p>
							</div>
							<button
								type="button"
								onClick={() => { setModelPickerOpen(!modelPickerOpen); setModelSearch(''); }}
								className="font-lato text-[12px] font-medium text-[#5048ED] hover:underline"
							>
								{modelPickerOpen ? 'Done' : 'Change'}
							</button>
						</div>

						{/* Current selection chip — always visible */}
						<div className={`flex items-center gap-[10px] rounded-[8px] border px-[12px] py-[10px] ${modelPickerOpen ? 'border-[#5048ED] bg-[#F5F3FF]' : 'border-[#E5E7EB] bg-[#F9FAFB]'}`}>
							<div className={`flex h-[28px] w-[28px] shrink-0 items-center justify-center rounded-[6px] ${modelPickerOpen ? 'bg-[#EEF2FF]' : 'bg-[#E5E7EB]'}`}>
								<svg width="13" height="13" viewBox="0 0 14 14" fill="none">
									<rect x="1" y="3" width="12" height="8" rx="2" stroke={modelPickerOpen ? '#5048ED' : '#6B7280'} strokeWidth="1.3"/>
									<path d="M4 7H10M4 9H8" stroke={modelPickerOpen ? '#5048ED' : '#6B7280'} strokeWidth="1.1" strokeLinecap="round"/>
								</svg>
							</div>
							<div className="min-w-0 flex-1">
								<p className="font-mono text-[12px] font-medium text-[#111827] truncate">{fallbackModel || '—'}</p>
								<p className="font-lato text-[11px] text-[#9CA3AF]">Currently selected</p>
							</div>
							{modelPickerOpen && (
								<svg width="14" height="14" viewBox="0 0 14 14" fill="none">
									<circle cx="7" cy="7" r="6" fill="#5048ED"/>
									<path d="M4 7L6 9L10 5" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
								</svg>
							)}
						</div>

						{/* Picker — collapsed by default */}
						{modelPickerOpen && (
							<div className="mt-[8px] rounded-[8px] border border-[#E5E7EB] bg-white">
								<div className="border-b border-[#F3F4F6] p-[8px]">
									<div className="relative">
										<svg className="absolute left-[8px] top-1/2 -translate-y-1/2 text-[#9CA3AF]" width="13" height="13" viewBox="0 0 14 14" fill="none">
											<circle cx="6" cy="6" r="4.5" stroke="currentColor" strokeWidth="1.2"/>
											<path d="M9.5 9.5L12 12" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
										</svg>
										<input
											autoFocus
											type="text"
											value={modelSearch}
											onChange={(e) => setModelSearch(e.target.value)}
											placeholder="Search models…"
											className="w-full rounded-[6px] border border-[#E5E7EB] py-[7px] pl-[26px] pr-[8px] font-lato text-[12px] placeholder:text-[#9CA3AF] focus:border-[#5048ED] focus:outline-0"
										/>
									</div>
								</div>
								<div className="flex max-h-[180px] flex-col overflow-y-auto">
									{[...filteredModels].sort((a, b) => (b.model_id === fallbackModel ? 1 : 0) - (a.model_id === fallbackModel ? 1 : 0)).map((m) => (
										<button
											key={m.model_id}
											type="button"
											onClick={() => { setFallbackModel(m.model_id); setModelSearch(''); setModelPickerOpen(false); }}
											className={`flex items-center justify-between border-b border-[#F9FAFB] px-[12px] py-[9px] text-left transition-colors last:border-b-0 hover:bg-[#F9FAFB] ${
												fallbackModel === m.model_id ? 'bg-[#F5F3FF]' : ''
											}`}
										>
											<span className="font-mono text-[12px] text-[#111827]">{m.model_id}</span>
											{fallbackModel === m.model_id && (
												<svg width="14" height="14" viewBox="0 0 14 14" fill="none">
													<circle cx="7" cy="7" r="6" fill="#5048ED"/>
													<path d="M4 7L6 9L10 5" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
												</svg>
											)}
										</button>
									))}
								</div>
							</div>
						)}
					</div>
				</>
			)}

			{/* Limits */}
			<div className="h-[1px] bg-[#F3F4F6]" />
			<p className="font-lato text-[12px] font-semibold uppercase tracking-[0.6px] text-[#6C747D]">
				Limits <span className="normal-case text-[#9CA3AF] tracking-normal font-normal">(optional)</span>
			</p>
			<div className="grid grid-cols-2 gap-[12px]">
				<div>
					<label className="font-lato text-[12px] font-semibold text-[#A3ABB1]">Rate limit (req/min)</label>
					<input type="number" value={rateLimitRpm} onChange={(e) => setRateLimitRpm(e.target.value)} placeholder="Unlimited"
						className="mt-[4px] w-full rounded-[6px] border border-[#DDE2E5] px-[16px] py-[12px] font-lato text-[14px] placeholder:text-[#9A9A9A] focus:outline-0 focus:border-[#5048ED]" />
				</div>
				<div>
					<label className="font-lato text-[12px] font-semibold text-[#A3ABB1]">Monthly budget (USD)</label>
					<input type="number" value={monthlyBudget} onChange={(e) => setMonthlyBudget(e.target.value)} placeholder="Unlimited"
						className="mt-[4px] w-full rounded-[6px] border border-[#DDE2E5] px-[16px] py-[12px] font-lato text-[14px] placeholder:text-[#9A9A9A] focus:outline-0 focus:border-[#5048ED]" />
				</div>
			</div>

			{/* Actions */}
			<div className="flex justify-end gap-[12px] pt-[4px]">
				<button type="button" onClick={onClose}
					className="rounded-[8px] border border-[#DDE2E5] px-[20px] py-[10px] font-lato text-[14px] font-medium text-[#111827] transition-colors hover:bg-[#F9FAFB]">
					Cancel
				</button>
				<button type="button" onClick={handleSave} disabled={!name.trim() || isSubmitting}
					className="flex items-center gap-[8px] rounded-[8px] bg-[#5048ED] px-[20px] py-[10px] font-lato text-[14px] font-medium text-white transition-colors hover:bg-[#4338CA] disabled:pointer-events-none disabled:opacity-50">
					{isSubmitting ? (
						<><span className="inline-block h-[13px] w-[13px] animate-spin rounded-full border-[2px] border-white border-t-transparent" /> Saving…</>
					) : 'Save Changes'}
				</button>
			</div>
		</div>
	);
}

/* ─── Dependency block dialog — shown when backend returns 409 PROVIDER_IN_USE ─── */
function DependencyBlockModal({ show, onClose, entityName, agentCount, agents }) {
	if (!show) return null;
	return (
		<div className="fixed inset-0 z-50 flex items-center justify-center">
			<div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
			<div className="relative w-full max-w-[440px] rounded-[16px] bg-white p-[28px] shadow-2xl">
				{/* Amber warning icon */}
				<div className="mb-[16px] flex h-[44px] w-[44px] items-center justify-center rounded-full bg-[#FFFBEB]">
					<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
						<path d="M10 6V10M10 14H10.01M19 10C19 14.9706 14.9706 19 10 19C5.02944 19 1 14.9706 1 10C1 5.02944 5.02944 1 10 1C14.9706 1 19 5.02944 19 10Z" stroke="#F59E0B" strokeWidth="1.8" strokeLinecap="round"/>
					</svg>
				</div>
				<h3 className="mb-[8px] font-source-sans-pro text-[18px] font-semibold text-[#111827]">
					Cannot Deactivate Provider
				</h3>
				<p className="mb-[6px] font-lato text-[14px] leading-[22px] text-[#6B7280]">
					<span className="font-semibold text-[#111827]">&ldquo;{entityName}&rdquo;</span> is actively used by{' '}
					<span className="font-semibold text-[#D97706]">{agentCount} agent{agentCount !== 1 ? 's' : ''}</span>.
					Reassign or disable the following agents before deactivating this provider:
				</p>
				<ul className="mb-[24px] mt-[12px] max-h-[180px] overflow-y-auto rounded-[8px] border border-[#E5E7EB] bg-[#F9FAFB] p-[12px] space-y-[8px]">
					{agents.map((a) => (
						<li key={a.id} className="flex items-center gap-[10px] font-lato text-[13px] text-[#111827]">
							<span className="inline-block h-[6px] w-[6px] flex-shrink-0 rounded-full bg-[#10B981]" />
							{a.name}
						</li>
					))}
				</ul>
				<div className="flex justify-end">
					<button
						onClick={onClose}
						className="rounded-[8px] border border-[#DDE2E5] px-[20px] py-[10px] font-lato text-[14px] font-medium text-[#111827] hover:bg-[#F9FAFB]"
					>
						Got it
					</button>
				</div>
			</div>
		</div>
	);
}

function ProviderRow({ provider, onEdit, onToggleStatus, onTestConnection, onDelete, testingId }) {
	const [expanded, setExpanded] = useState(false);
	const meta = PROVIDER_META[provider.provider_slug] || { bg: '#F9FAFB', border: '#E5E7EB', accent: '#6B7280' };
	const Logo = PROVIDER_LOGOS[provider.provider_slug];
	const maskedConfig = provider.masked_config || {};
	const isTesting = testingId === provider.id;

	const isInactive = provider.status !== 'active';

	return (
		<div className={`rounded-[10px] border bg-white transition-shadow ${isInactive ? 'border-[#E5E7EB] opacity-70 grayscale-[30%]' : 'border-[#E5E7EB] shadow-sm hover:shadow-md'}`}>
			<div className="flex items-center px-[20px] py-[14px]">
				<button
					onClick={() => setExpanded(!expanded)}
					className="mr-[14px] text-[#9CA3AF] transition-colors hover:text-[#111827]"
				>
					<svg
						width="12" height="12" viewBox="0 0 12 12" fill="none"
						className={`transition-transform duration-200 ${expanded ? 'rotate-90' : ''}`}
					>
						<path d="M4.5 2L8.5 6L4.5 10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
					</svg>
				</button>

				{/* Provider logo pill */}
				<div className="mr-[14px] flex h-[40px] w-[40px] shrink-0 items-center justify-center rounded-[10px] border p-[7px]"
					style={{ backgroundColor: meta.bg, borderColor: meta.border }}>
					{Logo
						? <Logo size={24} />
						: <span className="text-[14px] font-bold" style={{ color: meta.accent }}>{provider.name[0]?.toUpperCase()}</span>
					}
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
						<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Monthly Spend</span>
						<p className="font-lato text-[14px] text-[#111827]">
							${parseFloat(provider.current_month_spend_usd || 0).toFixed(2)}
						</p>
					</div>

					<div>
						<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Invocations</span>
						<p className="font-lato text-[14px] text-[#111827]">{provider.total_invocations || 0}</p>
					</div>

					<button
						onClick={() => onEdit(provider)}
						className="flex items-center gap-[6px] rounded-[6px] bg-[#5048ED] px-[14px] py-[7px] font-lato text-[13px] font-medium text-white transition-colors hover:bg-[#4338CA]"
					>
						<svg width="13" height="13" viewBox="0 0 13 13" fill="none">
							<path d="M9 1.5L11.5 4L4.5 11H2V8.5L9 1.5Z" stroke="white" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
						</svg>
						Configure
					</button>
				</div>
			</div>

			{expanded && (
				<div className="border-t border-[#E5E7EB]">
					{/* Stats row */}
					<div className="grid grid-cols-5 gap-0 border-b border-[#F3F4F6]">
						{[
							{ label: 'API Key', value: maskedConfig.api_key || maskedConfig.aws_access_key_id || '****', mono: true },
							{ label: 'Fallback Model', value: provider.default_model || '—', mono: true, hint: 'Used when no model is specified in direct API calls' },
							{ label: 'Monthly Budget', value: provider.monthly_budget_usd ? `$${parseFloat(provider.monthly_budget_usd).toFixed(2)}` : 'Unlimited' },
							{ label: 'Total Cost', value: `$${parseFloat(provider.total_cost_usd || 0).toFixed(4)}` },
							{ label: 'Total Tokens', value: ((provider.total_input_tokens || 0) + (provider.total_output_tokens || 0)).toLocaleString() },
						].map((stat, i) => (
							<div key={i} className={`px-[20px] py-[14px] ${i < 4 ? 'border-r border-[#F3F4F6]' : ''}`}>
								<div className="flex items-center gap-[4px]">
									<p className="font-lato text-[10px] font-bold uppercase tracking-[0.6px] text-[#9CA3AF]">{stat.label}</p>
									{stat.hint && (
										<span className="group relative cursor-help text-[#C4C9CE]">
											<svg width="11" height="11" viewBox="0 0 11 11" fill="none">
												<circle cx="5.5" cy="5.5" r="4.5" stroke="currentColor" strokeWidth="1"/>
												<path d="M5.5 5V7.5M5.5 3.5H5.51" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
											</svg>
											<span className="pointer-events-none absolute bottom-[calc(100%+6px)] left-1/2 z-50 w-[200px] -translate-x-1/2 rounded-[6px] bg-[#1F2937] px-[10px] py-[6px] font-lato text-[11px] leading-[16px] text-white opacity-0 shadow-lg transition-opacity group-hover:opacity-100">
												{stat.hint}
												<span className="absolute left-1/2 top-full -translate-x-1/2 border-4 border-transparent border-t-[#1F2937]" />
											</span>
										</span>
									)}
								</div>
								<p className={`mt-[2px] truncate text-[13px] text-[#111827] ${stat.mono ? 'font-mono' : 'font-lato'}`}>{stat.value}</p>
							</div>
						))}
					</div>

					{/* Action buttons */}
					<div className="flex items-center gap-[8px] px-[20px] py-[12px]">
						<button
							onClick={() => onTestConnection(provider)}
							disabled={isTesting}
							className="flex items-center gap-[6px] rounded-[6px] border border-[#DDE2E5] px-[12px] py-[6px] font-lato text-[13px] text-[#374151] transition-colors hover:bg-[#F9FAFB] disabled:opacity-50"
						>
							{isTesting ? (
								<span className="inline-block h-[11px] w-[11px] animate-spin rounded-full border-[1.5px] border-[#6B7280] border-t-transparent" />
							) : (
								<svg width="12" height="12" viewBox="0 0 12 12" fill="none">
									<path d="M3 6L5 9L10 3" stroke="#6B7280" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
								</svg>
							)}
							{isTesting ? 'Testing…' : 'Test Connection'}
						</button>

						{provider.status === 'active' ? (
							<button
								onClick={() => onToggleStatus(provider)}
								className="flex items-center gap-[6px] rounded-[6px] border border-[#FDE68A] bg-[#FFFBEB] px-[12px] py-[6px] font-lato text-[13px] font-medium text-[#92400E] transition-colors hover:border-[#F59E0B] hover:bg-[#FEF3C7]"
							>
								<svg width="12" height="12" viewBox="0 0 12 12" fill="none">
									<circle cx="6" cy="6" r="4.5" stroke="#D97706" strokeWidth="1.4"/>
									<path d="M2.8 2.8L9.2 9.2" stroke="#D97706" strokeWidth="1.4" strokeLinecap="round"/>
								</svg>
								Disable
							</button>
						) : (
							<button
								onClick={() => onToggleStatus(provider)}
								className="flex items-center gap-[6px] rounded-[6px] border border-[#A7F3D0] bg-[#ECFDF5] px-[12px] py-[6px] font-lato text-[13px] font-medium text-[#065F46] transition-colors hover:border-[#6EE7B7] hover:bg-[#D1FAE5]"
							>
								<svg width="12" height="12" viewBox="0 0 12 12" fill="none">
									<circle cx="6" cy="6" r="4.5" stroke="#059669" strokeWidth="1.4"/>
									<path d="M3.5 6L5.5 8L8.5 4" stroke="#059669" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
								</svg>
								Enable
							</button>
						)}

						<button
							onClick={() => onDelete(provider)}
							className="ml-auto flex items-center gap-[6px] rounded-[6px] border border-[#FECACA] bg-[#FEF2F2] px-[12px] py-[6px] font-lato text-[13px] font-medium text-[#991B1B] transition-colors hover:border-[#FCA5A5] hover:bg-[#FEE2E2]"
						>
							<svg width="12" height="12" viewBox="0 0 12 12" fill="none">
								<path d="M2 3H10M4 3V2H8V3M5 5V9M7 5V9M3 3L3.5 10H8.5L9 3" stroke="#DC2626" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
							</svg>
							Delete
						</button>
					</div>
				</div>
			)}
		</div>
	);
}

export default function Providers({ onReady }) {
	const { appId } = useParams();
	const triggerApi = useApi();

	const [providers, setProviders] = useState([]);
	const [availableProviders, setAvailableProviders] = useState([]);
	const [initialLoading, setInitialLoading] = useState(true);
	const [addModalOpen, setAddModalOpen] = useState(false);
	const [editModalOpen, setEditModalOpen] = useState(false);
	const [editingProvider, setEditingProvider] = useState(null);
	const [confirmModal, setConfirmModal] = useState({ show: false, type: null, provider: null });
	const [depModal, setDepModal] = useState({ show: false, entityName: '', agentCount: 0, agents: [] });
	const [testingId, setTestingId] = useState(null);
	const [actionLoading, setActionLoading] = useState(false);
	const readyCalledRef = useRef(false);

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
		setInitialLoading(true);
		Promise.all([fetchProviders(), fetchAvailableProviders()]).finally(() => {
			setInitialLoading(false);
			if (!readyCalledRef.current && onReady) {
				readyCalledRef.current = true;
				onReady();
			}
		});
	}, [appId]);

	// Add provider — called by wizard on step 3 submit
	const handleAddProvider = async (payload) => {
		const { success, response } = await triggerApi({
			url: `/api/v1/apps/${appId}/ai/providers/`,
			type: 'POST',
			loader: false,
			payload,
			showErrorModal: false,
		});

		if (success) {
			setAddModalOpen(false);
			notify('success', 'Provider Added', `${payload.name} has been added successfully.`);
			fetchProviders();
		} else {
			notify('error', 'Failed to Add Provider', response?.message || 'An error occurred.');
		}
	};

	// Edit provider
	const handleEditProvider = async (payload) => {
		if (!editingProvider) return;
		const { success, response } = await triggerApi({
			url: `/api/v1/apps/${appId}/ai/providers/${editingProvider.id}/`,
			type: 'PUT',
			loader: false,
			payload,
			showErrorModal: false,
		});
		if (success) {
			setEditModalOpen(false);
			setEditingProvider(null);
			notify('success', 'Provider Updated', `${payload.name} has been updated successfully.`);
			fetchProviders();
		} else {
			notify('error', 'Update Failed', response?.message || 'An error occurred.');
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

		const { success, response } = await triggerApi({
			url: `/api/v1/apps/${appId}/ai/providers/${provider.id}/toggle/`,
			type: 'POST',
			loader: false,
			payload: { is_enabled: newEnabled },
		});

		setActionLoading(false);
		setConfirmModal({ show: false, type: null, provider: null });

		if (!success && response?.error_code === 'PROVIDER_IN_USE') {
			setDepModal({
				show: true,
				entityName: provider.name,
				agentCount: response.agents?.length ?? 0,
				agents: response.agents ?? [],
			});
			return;
		}

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

		const { success, response } = await triggerApi({
			url: `/api/v1/apps/${appId}/ai/providers/${provider.id}/`,
			type: 'DELETE',
			loader: false,
		});

		setActionLoading(false);
		setConfirmModal({ show: false, type: null, provider: null });

		if (!success && response?.error_code === 'PROVIDER_IN_USE') {
			setDepModal({
				show: true,
				entityName: provider.name,
				agentCount: response.agents?.length ?? 0,
				agents: response.agents ?? [],
			});
			return;
		}

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
				{!initialLoading && providers.length === 0 && (
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

			{/* Add Provider — centered wizard dialog */}
			<StandardModal
				label="Add Provider"
				size="lg"
				show={addModalOpen}
				closeModal={() => setAddModalOpen(false)}
				ModalBody={
					<div className="px-[24px] py-[24px]">
						<AddProviderWizard
							onSubmit={handleAddProvider}
							availableProviders={availableProviders}
							appId={appId}
							triggerApi={triggerApi}
						/>
					</div>
				}
			/>

			{/* Edit Provider Modal */}
			<StandardModal
				label={`Configure — ${editingProvider?.name || ''}`}
				size="lg"
				show={editModalOpen}
				closeModal={() => { setEditModalOpen(false); setEditingProvider(null); }}
				ModalBody={
					editingProvider && (
						<EditProviderForm
							key={editingProvider.id}
							provider={editingProvider}
							availableProviders={availableProviders}
							onSave={handleEditProvider}
							onClose={() => { setEditModalOpen(false); setEditingProvider(null); }}
							appId={appId}
							triggerApi={triggerApi}
						/>
					)
				}
			/>

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

			{/* Dependency block — shown when provider is in use by active agents */}
			<DependencyBlockModal
				show={depModal.show}
				onClose={() => setDepModal({ show: false, entityName: '', agentCount: 0, agents: [] })}
				entityName={depModal.entityName}
				agentCount={depModal.agentCount}
				agents={depModal.agents}
			/>
		</div>
	);
}
