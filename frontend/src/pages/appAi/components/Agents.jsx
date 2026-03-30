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
	anthropic: { color: '#6B5CE7', initial: 'A', label: 'Anthropic' },
	openai: { color: '#10B981', initial: 'O', label: 'OpenAI' },
	azure_openai: { color: '#346BD4', initial: 'Az', label: 'Azure OpenAI' },
	bedrock: { color: '#F59E0B', initial: 'B', label: 'AWS Bedrock' },
};

function notify(type, title, description) {
	toast.custom(
		(t) => <Toast type={type} toastRef={t} title={title} description={description} />,
		{ duration: 5000, position: 'bottom-left' }
	);
}

function ProviderBadge({ slug, name }) {
	const info = PROVIDER_COLORS[slug] || { color: '#6B7280', initial: '?', label: name || slug };
	return (
		<span className="flex items-center gap-[6px]">
			<span className="flex h-[20px] w-[20px] items-center justify-center rounded-full text-[10px] font-semibold text-white" style={{ backgroundColor: info.color }}>
				{info.initial}
			</span>
			<span className="font-lato text-[13px] text-[#111827]">{name || info.label}</span>
		</span>
	);
}

function StatusBadge({ status }) {
	const isActive = status === 'active';
	return (
		<span className="flex items-center gap-[4px]">
			<span className={`inline-block h-[6px] w-[6px] rounded-full ${isActive ? 'bg-[#10B981]' : 'bg-[#6B7280]'}`} />
			<span className={`font-lato text-[12px] font-medium ${isActive ? 'text-[#10B981]' : 'text-[#6B7280]'}`}>
				{isActive ? 'Active' : 'Disabled'}
			</span>
		</span>
	);
}

function Tag({ children, color = 'blue' }) {
	const colors = { blue: 'bg-[#EFF6FF] text-[#346BD4]', green: 'bg-[#ECFDF5] text-[#059669]', amber: 'bg-[#FFFBEB] text-[#D97706]', purple: 'bg-[#F5F3FF] text-[#7C3AED]' };
	return <span className={`rounded-[4px] px-[8px] py-[2px] font-lato text-[12px] font-medium ${colors[color]}`}>{children}</span>;
}

function MetricCard({ label, value, color }) {
	return (
		<div className="rounded-[8px] border border-[#E5E7EB] bg-[#F9FAFB] px-[16px] py-[12px]">
			<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">{label}</span>
			<p className={`mt-[4px] font-lato text-[20px] font-semibold ${color || 'text-[#111827]'}`}>{value}</p>
		</div>
	);
}

function ConfirmationModal({ show, onClose, onConfirm, title, message, confirmLabel, confirmColor, loading }) {
	if (!show) return null;
	const colorClasses = { red: 'bg-[#EF4444] hover:bg-[#DC2626]', green: 'bg-[#10B981] hover:bg-[#059669]', blue: 'bg-[#346BD4] hover:bg-[#2556B0]' };
	return (
		<Modal label={title} show={show} closeModal={onClose} ModalBody={
			<div className="flex flex-col gap-[24px]">
				<p className="font-lato text-[14px] leading-[22px] text-[#6B7280]">{message}</p>
				<div className="flex justify-end gap-[12px]">
					<button onClick={onClose} disabled={loading} className="rounded-[8px] border border-[#DDE2E5] px-[20px] py-[10px] font-lato text-[14px] font-medium text-[#111827] hover:bg-[#F9FAFB] disabled:opacity-50">Cancel</button>
					<button onClick={onConfirm} disabled={loading} className={`rounded-[8px] px-[20px] py-[10px] font-lato text-[14px] font-medium text-white disabled:opacity-50 ${colorClasses[confirmColor] || colorClasses.blue}`}>
						{loading ? 'Processing...' : confirmLabel}
					</button>
				</div>
			</div>
		} />
	);
}

/* ─── Inline Prompt Creator (mini form within agent builder) ─── */
function InlinePromptCreator({ type, appId, triggerApi, onCreated, onCancel }) {
	const [name, setName] = useState('');
	const [content, setContent] = useState('');
	const [saving, setSaving] = useState(false);

	const handleSave = async () => {
		if (!name || !content) return;
		setSaving(true);
		const { success } = await triggerApi({
			url: `/api/v1/apps/${appId}/ai/prompts/`,
			type: 'POST',
			loader: false,
			payload: { name, description: '', type, content, change_description: 'Initial version' },
		});
		setSaving(false);
		if (success) {
			notify('success', 'Prompt Created', `${name} created with v1.`);
			onCreated(name);
		}
	};

	return (
		<div className="mt-[8px] rounded-[8px] border border-[#346BD4] bg-[#F8FAFF] p-[16px]">
			<div className="mb-[8px] flex items-center justify-between">
				<span className="font-lato text-[12px] font-semibold uppercase tracking-[0.6px] text-[#346BD4]">
					Create New {type === 'system' ? 'System' : 'User'} Prompt
				</span>
				<button onClick={onCancel} className="font-lato text-[12px] text-[#6B7280] hover:text-[#111827]">Cancel</button>
			</div>
			<input
				value={name}
				onChange={(e) => setName(e.target.value)}
				placeholder="prompt-name (lowercase, hyphens)"
				className="mb-[8px] w-full rounded-[6px] border border-[#DDE2E5] px-[12px] py-[8px] font-lato text-[13px] outline-none focus:border-[#346BD4]"
			/>
			<textarea
				value={content}
				onChange={(e) => setContent(e.target.value)}
				placeholder={`Enter ${type} prompt content...\nUse {{variable_name}} for template variables`}
				rows={4}
				className="mb-[8px] w-full rounded-[6px] border border-[#DDE2E5] px-[12px] py-[8px] font-mono text-[12px] outline-none focus:border-[#346BD4]"
			/>
			<button
				onClick={handleSave}
				disabled={!name || !content || saving}
				className="rounded-[6px] bg-[#346BD4] px-[14px] py-[6px] font-lato text-[12px] font-medium text-white hover:bg-[#2556B0] disabled:opacity-50"
			>
				{saving ? 'Creating...' : 'Create Prompt'}
			</button>
		</div>
	);
}

/* ─── Prompt Selector with Preview ─── */
function PromptSelector({ label, hint, type, value, onChange, prompts, appId, triggerApi, onPromptCreated }) {
	const [showPreview, setShowPreview] = useState(false);
	const [showCreator, setShowCreator] = useState(false);
	const filtered = prompts.filter((p) => p.type === type);
	const selected = filtered.find((p) => p.name === value);

	return (
		<div>
			<div className="mb-[4px] flex items-center justify-between">
				<label className="font-lato text-[13px] font-semibold text-[#374151]">{label}</label>
				{value && (
					<button onClick={() => setShowPreview(!showPreview)} className="font-lato text-[11px] font-medium text-[#346BD4] hover:underline">
						{showPreview ? 'Hide Preview' : 'Preview'}
					</button>
				)}
			</div>
			<p className="mb-[6px] font-lato text-[12px] text-[#9CA3AF]">{hint}</p>
			<div className="flex items-center gap-[8px]">
				<select
					value={value}
					onChange={(e) => { onChange(e.target.value); setShowPreview(false); }}
					className="flex-1 rounded-[6px] border border-[#DDE2E5] px-[12px] py-[10px] font-lato text-[13px] text-[#111827] outline-none focus:border-[#5048ED]"
				>
					<option value="">None (optional)</option>
					{filtered.map((p) => (
						<option key={p.id} value={p.name}>{p.name}{p.active_version_number ? ` (v${p.active_version_number})` : ''}</option>
					))}
				</select>
				<button
					onClick={() => setShowCreator(!showCreator)}
					className="flex-shrink-0 rounded-[6px] border border-dashed border-[#346BD4] px-[10px] py-[9px] font-lato text-[12px] font-medium text-[#346BD4] hover:bg-[#EFF6FF]"
					title="Create a new prompt"
				>
					+ New
				</button>
			</div>

			{showPreview && selected?.active_version?.content && (
				<div className="mt-[8px] rounded-[6px] bg-[#1F2937] p-[12px] max-h-[160px] overflow-y-auto">
					<pre className="whitespace-pre-wrap break-words font-mono text-[12px] leading-[20px] text-[#D1D5DB]">
						{selected.active_version.content.split(/(\{\{\w+\}\})/g).map((part, i) =>
							/^\{\{\w+\}\}$/.test(part) ? <span key={i} className="text-[#F59E0B]">{part}</span> : <span key={i}>{part}</span>
						)}
					</pre>
				</div>
			)}

			{showCreator && (
				<InlinePromptCreator
					type={type}
					appId={appId}
					triggerApi={triggerApi}
					onCreated={(name) => {
						setShowCreator(false);
						onPromptCreated();
						onChange(name);
					}}
					onCancel={() => setShowCreator(false)}
				/>
			)}

			{filtered.length === 0 && !showCreator && (
				<p className="mt-[4px] font-lato text-[11px] text-[#D97706]">
					No {type} prompts found. Click "+ New" to create one, or go to the Prompts tab.
				</p>
			)}
		</div>
	);
}

/* ─── Tool Multi-Select with Chips ─── */
function ToolSelector({ selectedTools, onChange, availableTools }) {
	const [dropdownOpen, setDropdownOpen] = useState(false);
	const [search, setSearch] = useState('');

	const filtered = availableTools.filter(
		(t) => t.is_active && !selectedTools.includes(t.name) && (
			t.name.toLowerCase().includes(search.toLowerCase()) ||
			t.description.toLowerCase().includes(search.toLowerCase())
		)
	);

	const addTool = (name) => {
		onChange([...selectedTools, name]);
		setSearch('');
	};

	const removeTool = (name) => {
		onChange(selectedTools.filter((t) => t !== name));
	};

	const safetyColors = {
		read_only: 'bg-[#ECFDF5] text-[#059669]',
		write: 'bg-[#FEF3C7] text-[#D97706]',
		external: 'bg-[#FEF2F2] text-[#DC2626]',
	};
	const safetyLabels = { read_only: 'READ', write: 'WRITE', external: 'EXT' };

	return (
		<div className="relative">
			{/* Selected chips */}
			<div className="mb-[6px] flex flex-wrap gap-[6px]">
				{selectedTools.map((name) => {
					const toolInfo = availableTools.find((t) => t.name === name);
					return (
						<span key={name} className="flex items-center gap-[4px] rounded-[6px] bg-[#EFF6FF] px-[10px] py-[4px]">
							<span className="font-mono font-lato text-[12px] text-[#346BD4]">{name}</span>
							{toolInfo && (
								<span className={`ml-[2px] rounded-[3px] px-[4px] py-[0px] text-[9px] font-bold ${safetyColors[toolInfo.safety] || 'bg-[#F3F4F6] text-[#6B7280]'}`}>
									{safetyLabels[toolInfo.safety] || '?'}
								</span>
							)}
							<button
								type="button"
								onClick={() => removeTool(name)}
								className="ml-[2px] text-[#9CA3AF] hover:text-[#EF4444]"
							>
								<svg width="10" height="10" viewBox="0 0 10 10"><path d="M2 2L8 8M8 2L2 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>
							</button>
						</span>
					);
				})}
			</div>

			{/* Search + dropdown */}
			<div className="relative">
				<input
					value={search}
					onChange={(e) => { setSearch(e.target.value); setDropdownOpen(true); }}
					onFocus={() => setDropdownOpen(true)}
					placeholder={selectedTools.length > 0 ? 'Add another tool...' : 'Search and select tools...'}
					className="w-full rounded-[6px] border border-[#DDE2E5] px-[12px] py-[10px] font-lato text-[13px] outline-none focus:border-[#5048ED]"
				/>
				{dropdownOpen && filtered.length > 0 && (
					<div className="absolute z-20 mt-[4px] w-full max-h-[240px] overflow-y-auto rounded-[8px] border border-[#E5E7EB] bg-white shadow-lg">
						{filtered.map((tool) => (
							<button
								key={tool.name}
								type="button"
								onClick={() => { addTool(tool.name); setDropdownOpen(false); }}
								className="flex w-full items-start gap-[10px] px-[12px] py-[10px] text-left hover:bg-[#F9FAFB] border-b border-[#F3F4F6] last:border-b-0"
							>
								<div className="flex-1 min-w-0">
									<div className="flex items-center gap-[6px]">
										<span className="font-mono font-lato text-[13px] font-medium text-[#111827]">{tool.name}</span>
										<span className={`rounded-[3px] px-[5px] py-[1px] text-[9px] font-bold ${safetyColors[tool.safety] || 'bg-[#F3F4F6] text-[#6B7280]'}`}>
											{safetyLabels[tool.safety] || '?'}
										</span>
										{tool.requires_confirmation && (
											<span className="text-[10px] text-[#D97706]">requires confirmation</span>
										)}
									</div>
									<p className="mt-[2px] font-lato text-[11px] text-[#6B7280] truncate">{tool.description}</p>
								</div>
								<span className="flex-shrink-0 font-lato text-[11px] text-[#9CA3AF]">{tool.section}</span>
							</button>
						))}
					</div>
				)}
				{dropdownOpen && filtered.length === 0 && search && (
					<div className="absolute z-20 mt-[4px] w-full rounded-[8px] border border-[#E5E7EB] bg-white px-[12px] py-[10px] shadow-lg">
						<p className="font-lato text-[12px] text-[#9CA3AF]">No matching tools found. Sync tools first from the Tools tab.</p>
					</div>
				)}
			</div>

			{/* Click-away */}
			{dropdownOpen && (
				<div className="fixed inset-0 z-10" onClick={() => setDropdownOpen(false)} />
			)}
		</div>
	);
}

/* ─── Full-Page Agent Builder ─── */
function AgentBuilder({ show, onClose, onSave, initialValues, providers, prompts, availableTools, appId, triggerApi, onPromptCreated }) {
	if (!show) return null;

	const isEdit = !!initialValues._isEdit;

	return (
		<div className="fixed inset-0 z-50 flex bg-black/50">
			<div className="m-auto flex h-[90vh] w-full max-w-[1100px] flex-col rounded-[16px] bg-white shadow-2xl">
				{/* Header */}
				<div className="flex items-center justify-between border-b border-[#E5E7EB] px-[32px] py-[20px]">
					<div className="flex items-center gap-[12px]">
						<button onClick={onClose} className="rounded-[6px] p-[6px] text-[#6B7280] transition-colors hover:bg-[#F3F4F6] hover:text-[#111827]">
							<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
								<path d="M12 4L6 10L12 16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
							</svg>
						</button>
						<h2 className="font-source-sans-pro text-[20px] font-semibold text-[#111827]">
							{isEdit ? 'Edit Agent' : 'Create Agent'}
						</h2>
					</div>
					<button onClick={onClose} className="rounded-[6px] p-[6px] text-[#6B7280] hover:bg-[#F3F4F6] hover:text-[#111827]">
						<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
							<path d="M5 5L15 15M15 5L5 15" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
						</svg>
					</button>
				</div>

				{/* Body */}
				<Formik
					initialValues={initialValues}
					validationSchema={Yup.object({
						name: Yup.string().matches(/^[a-z0-9-]+$/, 'Lowercase letters, numbers, and hyphens only').required('Required'),
						description: Yup.string(),
						provider_id: Yup.mixed().required('Select a provider'),
						model: Yup.string().required('Select a model'),
						temperature: Yup.number().min(0).max(2).required('Required'),
						max_tokens: Yup.number().min(1).max(128000).required('Required'),
						timeout_seconds: Yup.number().min(1).required('Required'),
						output_schema: Yup.string().required('Required'),
					})}
					onSubmit={onSave}
					enableReinitialize
				>
					{(formik) => {
						const selectedProvider = providers.find((p) => String(p.id) === String(formik.values.provider_id));
						const models = selectedProvider?.enabled_models?.filter((m) => m.is_enabled) || [];

						return (
							<form onSubmit={formik.handleSubmit} className="flex flex-1 overflow-hidden">
								{/* Left Column — Main fields */}
								<div className="flex-1 overflow-y-auto px-[32px] py-[24px]">

									{/* Section 1: Identity */}
									<div className="mb-[32px]">
										<h3 className="mb-[4px] font-source-sans-pro text-[16px] font-semibold text-[#111827]">Identity</h3>
										<p className="mb-[16px] font-lato text-[13px] text-[#9CA3AF]">
											Give your agent a unique name and describe its purpose
										</p>
										<div className="flex flex-col gap-[16px]">
											<div>
												<label className="mb-[4px] block font-lato text-[13px] font-semibold text-[#374151]">Agent Name</label>
												<p className="mb-[6px] font-lato text-[12px] text-[#9CA3AF]">Lowercase letters, numbers, and hyphens. Used in code as <code className="rounded bg-[#F3F4F6] px-[4px] py-[1px] text-[11px]">get_agent("name")</code></p>
												<input
													name="name"
													value={formik.values.name}
													onChange={formik.handleChange}
													onBlur={formik.handleBlur}
													placeholder="e.g. assessment-question-generator"
													className="w-full rounded-[6px] border border-[#DDE2E5] px-[12px] py-[10px] font-lato text-[14px] outline-none focus:border-[#5048ED] focus:ring-1 focus:ring-[#5048ED]"
												/>
												{formik.touched.name && formik.errors.name && (
													<p className="mt-[4px] font-lato text-[12px] text-[#EF4444]">{formik.errors.name}</p>
												)}
											</div>
											<div>
												<label className="mb-[4px] block font-lato text-[13px] font-semibold text-[#374151]">Description</label>
												<textarea
													name="description"
													value={formik.values.description}
													onChange={formik.handleChange}
													onBlur={formik.handleBlur}
													placeholder="Describe what this agent does and when it should be used"
													rows={3}
													className="w-full rounded-[6px] border border-[#DDE2E5] px-[12px] py-[10px] font-lato text-[13px] outline-none focus:border-[#5048ED] focus:ring-1 focus:ring-[#5048ED]"
												/>
												{formik.touched.description && formik.errors.description && (
													<p className="mt-[4px] font-lato text-[12px] text-[#EF4444]">{formik.errors.description}</p>
												)}
											</div>
										</div>
									</div>

									{/* Section 2: LLM Configuration */}
									<div className="mb-[32px]">
										<h3 className="mb-[4px] font-source-sans-pro text-[16px] font-semibold text-[#111827]">LLM Configuration</h3>
										<p className="mb-[16px] font-lato text-[13px] text-[#9CA3AF]">
											Choose which provider and model this agent uses
										</p>
										<div className="flex flex-col gap-[16px]">
											<div>
												<div className="mb-[4px] flex items-center justify-between">
													<label className="font-lato text-[13px] font-semibold text-[#374151]">Provider</label>
													{providers.filter((p) => p.is_enabled).length === 0 && (
														<span className="font-lato text-[11px] text-[#D97706]">
															No providers configured. Go to the Providers tab first.
														</span>
													)}
												</div>
												<select
													name="provider_id"
													value={formik.values.provider_id}
													onChange={(e) => { formik.setFieldValue('provider_id', e.target.value); formik.setFieldValue('model', ''); }}
													onBlur={formik.handleBlur}
													className="w-full rounded-[6px] border border-[#DDE2E5] px-[12px] py-[10px] font-lato text-[13px] outline-none focus:border-[#5048ED]"
												>
													<option value="">Select a provider...</option>
													{providers.filter((p) => p.is_enabled).map((p) => (
														<option key={p.id} value={p.id}>{p.name} ({p.provider_slug})</option>
													))}
												</select>
												{formik.touched.provider_id && formik.errors.provider_id && (
													<p className="mt-[4px] font-lato text-[12px] text-[#EF4444]">{formik.errors.provider_id}</p>
												)}
											</div>

											<div>
												<label className="mb-[4px] block font-lato text-[13px] font-semibold text-[#374151]">Model</label>
												<select
													name="model"
													value={formik.values.model}
													onChange={formik.handleChange}
													onBlur={formik.handleBlur}
													disabled={!formik.values.provider_id}
													className="w-full rounded-[6px] border border-[#DDE2E5] px-[12px] py-[10px] font-lato text-[13px] outline-none focus:border-[#5048ED] disabled:bg-[#F9FAFB] disabled:text-[#9CA3AF]"
												>
													<option value="">{formik.values.provider_id ? 'Select a model...' : 'Select a provider first'}</option>
													{models.map((m) => (
														<option key={m.model_id} value={m.model_id}>{m.display_name} ({m.model_id})</option>
													))}
													{models.length === 0 && selectedProvider?.default_model && (
														<option value={selectedProvider.default_model}>{selectedProvider.default_model}</option>
													)}
												</select>
												{formik.touched.model && formik.errors.model && (
													<p className="mt-[4px] font-lato text-[12px] text-[#EF4444]">{formik.errors.model}</p>
												)}
											</div>

											<div className="grid grid-cols-3 gap-[12px]">
												<div>
													<label className="mb-[4px] block font-lato text-[13px] font-semibold text-[#374151]">Temperature</label>
													<p className="mb-[4px] font-lato text-[11px] text-[#9CA3AF]">0 = deterministic, 2 = creative</p>
													<input name="temperature" type="number" step="0.1" min="0" max="2" value={formik.values.temperature} onChange={formik.handleChange} onBlur={formik.handleBlur}
														className="w-full rounded-[6px] border border-[#DDE2E5] px-[12px] py-[10px] font-lato text-[13px] outline-none focus:border-[#5048ED]" />
												</div>
												<div>
													<label className="mb-[4px] block font-lato text-[13px] font-semibold text-[#374151]">Max Tokens</label>
													<p className="mb-[4px] font-lato text-[11px] text-[#9CA3AF]">Max response length</p>
													<input name="max_tokens" type="number" min="1" max="128000" value={formik.values.max_tokens} onChange={formik.handleChange} onBlur={formik.handleBlur}
														className="w-full rounded-[6px] border border-[#DDE2E5] px-[12px] py-[10px] font-lato text-[13px] outline-none focus:border-[#5048ED]" />
												</div>
												<div>
													<label className="mb-[4px] block font-lato text-[13px] font-semibold text-[#374151]">Timeout (sec)</label>
													<p className="mb-[4px] font-lato text-[11px] text-[#9CA3AF]">Request timeout</p>
													<input name="timeout_seconds" type="number" min="1" value={formik.values.timeout_seconds} onChange={formik.handleChange} onBlur={formik.handleBlur}
														className="w-full rounded-[6px] border border-[#DDE2E5] px-[12px] py-[10px] font-lato text-[13px] outline-none focus:border-[#5048ED]" />
												</div>
											</div>
										</div>
									</div>

									{/* Section 3: Prompts */}
									<div className="mb-[32px]">
										<h3 className="mb-[4px] font-source-sans-pro text-[16px] font-semibold text-[#111827]">Prompts</h3>
										<p className="mb-[16px] font-lato text-[13px] text-[#9CA3AF]">
											Link versioned prompt templates. You can preview content or create new prompts inline.
										</p>
										<div className="flex flex-col gap-[20px]">
											<PromptSelector
												label="System Prompt"
												hint="Sets the agent's behavior and persona. Applied as the system message in every call."
												type="system"
												value={formik.values.system_prompt_name}
												onChange={(val) => formik.setFieldValue('system_prompt_name', val)}
												prompts={prompts}
												appId={appId}
												triggerApi={triggerApi}
												onPromptCreated={onPromptCreated}
											/>
											<PromptSelector
												label="User Prompt"
												hint="Template for user messages. Variables like {{name}} are filled at runtime via agent.run(variables={...})."
												type="user"
												value={formik.values.user_prompt_name}
												onChange={(val) => formik.setFieldValue('user_prompt_name', val)}
												prompts={prompts}
												appId={appId}
												triggerApi={triggerApi}
												onPromptCreated={onPromptCreated}
											/>
										</div>
									</div>

									{/* Section 4: Output & Tools */}
									<div className="mb-[24px]">
										<h3 className="mb-[4px] font-source-sans-pro text-[16px] font-semibold text-[#111827]">Output & Tools</h3>
										<p className="mb-[16px] font-lato text-[13px] text-[#9CA3AF]">
											Configure the expected output format and optional capabilities
										</p>
										<div className="flex flex-col gap-[16px]">
											<div>
												<label className="mb-[4px] block font-lato text-[13px] font-semibold text-[#374151]">Output Schema</label>
												<p className="mb-[6px] font-lato text-[12px] text-[#9CA3AF]">How the agent's response should be structured</p>
												<div className="flex gap-[8px]">
													{['JSON', 'Text', 'Markdown'].map((schema) => (
														<button
															key={schema}
															type="button"
															onClick={() => formik.setFieldValue('output_schema', schema)}
															className={`rounded-[6px] border px-[20px] py-[8px] font-lato text-[13px] font-medium transition-colors ${
																formik.values.output_schema === schema
																	? 'border-[#5048ED] bg-[#EEF2FF] text-[#5048ED]'
																	: 'border-[#DDE2E5] text-[#6B7280] hover:border-[#9CA3AF]'
															}`}
														>
															{schema}
														</button>
													))}
												</div>
												{formik.values.output_schema === 'JSON' && (
													<div className="mt-[8px]">
														<label className="mb-[4px] block font-lato text-[13px] font-semibold text-[#374151]">
															JSON Schema <span className="font-normal text-[#9CA3AF]">(optional)</span>
														</label>
														<p className="mb-[6px] font-lato text-[12px] text-[#9CA3AF]">
															Define a JSON Schema to enforce structured output. The LLM will be constrained to return JSON matching this schema.
														</p>
														<textarea
															name="output_json_schema_str"
															value={formik.values.output_json_schema_str || ''}
															onChange={formik.handleChange}
															onBlur={(e) => {
																formik.handleBlur(e);
																if (e.target.value) {
																	try {
																		JSON.parse(e.target.value);
																		formik.setFieldError('output_json_schema_str', undefined);
																	} catch {
																		formik.setFieldError('output_json_schema_str', 'Invalid JSON');
																	}
																}
															}}
															placeholder={'{\n  "type": "array",\n  "items": {\n    "type": "object",\n    "properties": {\n      "question": { "type": "string" },\n      "answer": { "type": "string" }\n    },\n    "required": ["question", "answer"]\n  }\n}'}
															rows={8}
															className={`w-full rounded-[6px] border px-[12px] py-[10px] font-mono text-[12px] outline-none focus:border-[#5048ED] ${
																formik.errors.output_json_schema_str
																	? 'border-red-400 bg-red-50'
																	: 'border-[#DDE2E5]'
															}`}
														/>
														{formik.errors.output_json_schema_str && (
															<p className="mt-[4px] font-lato text-[12px] text-red-500">{formik.errors.output_json_schema_str}</p>
														)}
													</div>
												)}
											</div>

											<div>
												<label className="mb-[4px] block font-lato text-[13px] font-semibold text-[#374151]">Guardrails</label>
												<p className="mb-[6px] font-lato text-[12px] text-[#9CA3AF]">Comma-separated list of guardrail names (e.g. pii-redaction, token-budget-check)</p>
												<input name="guardrails_str" value={formik.values.guardrails_str} onChange={formik.handleChange}
													placeholder="e.g. pii-redaction, content-safety"
													className="w-full rounded-[6px] border border-[#DDE2E5] px-[12px] py-[10px] font-lato text-[13px] outline-none focus:border-[#5048ED]" />
											</div>

											<div>
												<label className="mb-[4px] block font-lato text-[13px] font-semibold text-[#374151]">Tools</label>
												<p className="mb-[6px] font-lato text-[12px] text-[#9CA3AF]">
													Select functions this agent can call. Tools are registered via <code className="rounded bg-[#F3F4F6] px-[3px] py-[0.5px] text-[11px]">@tool</code> in code and synced from the Tools tab.
												</p>
												<ToolSelector
													selectedTools={formik.values.selected_tools}
													onChange={(tools) => formik.setFieldValue('selected_tools', tools)}
													availableTools={availableTools}
												/>
												{availableTools.length === 0 && (
													<p className="mt-[4px] font-lato text-[11px] text-[#D97706]">
														No tools available. Register tools with @tool decorator and sync from the Tools tab.
													</p>
												)}
											</div>
										</div>
									</div>
								</div>

								{/* Right Column — Summary & Actions */}
								<div className="w-[320px] flex-shrink-0 border-l border-[#E5E7EB] bg-[#F9FAFB] px-[24px] py-[24px] flex flex-col overflow-y-auto">
									<h3 className="mb-[20px] font-source-sans-pro text-[16px] font-semibold text-[#111827]">Summary</h3>

									<div className="flex flex-col gap-[16px] flex-1">
										<div className="rounded-[8px] border border-[#E5E7EB] bg-white p-[16px]">
											<div className="flex items-center gap-[8px] mb-[12px]">
												<div className="flex h-[28px] w-[28px] items-center justify-center rounded-[6px] bg-[#EEF2FF]">
													<span className="font-lato text-[14px] font-bold text-[#5048ED]">1</span>
												</div>
												<span className="font-lato text-[13px] font-semibold text-[#111827]">Choose LLM & Define Role</span>
											</div>
											<p className="font-lato text-[12px] text-[#6B7280]">Select your provider and model, then describe the agent's purpose</p>
											{formik.values.provider_id && formik.values.model && (
												<div className="mt-[8px] flex items-center gap-[6px]">
													<svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M3 7L6 10L11 4" stroke="#10B981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
													<span className="font-lato text-[12px] text-[#10B981]">{formik.values.model}</span>
												</div>
											)}
										</div>

										<div className="rounded-[8px] border border-[#E5E7EB] bg-white p-[16px]">
											<div className="flex items-center gap-[8px] mb-[12px]">
												<div className="flex h-[28px] w-[28px] items-center justify-center rounded-[6px] bg-[#EEF2FF]">
													<span className="font-lato text-[14px] font-bold text-[#5048ED]">2</span>
												</div>
												<span className="font-lato text-[13px] font-semibold text-[#111827]">Configure Prompts</span>
											</div>
											<p className="font-lato text-[12px] text-[#6B7280]">Link versioned prompt templates that define agent behavior</p>
											{(formik.values.system_prompt_name || formik.values.user_prompt_name) && (
												<div className="mt-[8px] flex flex-col gap-[4px]">
													{formik.values.system_prompt_name && (
														<div className="flex items-center gap-[4px]">
															<svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 6L5 9L10 3" stroke="#10B981" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
															<span className="font-lato text-[11px] text-[#10B981]">System: {formik.values.system_prompt_name}</span>
														</div>
													)}
													{formik.values.user_prompt_name && (
														<div className="flex items-center gap-[4px]">
															<svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 6L5 9L10 3" stroke="#10B981" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
															<span className="font-lato text-[11px] text-[#10B981]">User: {formik.values.user_prompt_name}</span>
														</div>
													)}
												</div>
											)}
										</div>

										<div className="rounded-[8px] border border-[#E5E7EB] bg-white p-[16px]">
											<div className="flex items-center gap-[8px] mb-[12px]">
												<div className="flex h-[28px] w-[28px] items-center justify-center rounded-[6px] bg-[#EEF2FF]">
													<span className="font-lato text-[14px] font-bold text-[#5048ED]">3</span>
												</div>
												<span className="font-lato text-[13px] font-semibold text-[#111827]">Output & Tools</span>
											</div>
											<p className="font-lato text-[12px] text-[#6B7280]">Set output format and attach optional tools & guardrails</p>
											<div className="mt-[8px] flex flex-wrap items-center gap-[4px]">
												<Tag color="green">{formik.values.output_schema || 'Text'}</Tag>
												{(formik.values.selected_tools || []).length > 0 && (
													<span className="ml-[4px] font-lato text-[11px] text-[#346BD4]">
														+ {formik.values.selected_tools.length} tool{formik.values.selected_tools.length > 1 ? 's' : ''}
													</span>
												)}
											</div>
										</div>
									</div>

									{/* Code Preview */}
									{formik.values.name && (
										<div className="mt-[16px] rounded-[8px] bg-[#1F2937] p-[12px]">
											<span className="font-lato text-[10px] font-bold uppercase tracking-[0.6px] text-[#6B7280]">Usage in Code</span>
											<pre className="mt-[6px] font-mono text-[11px] leading-[18px] text-[#D1D5DB]">
{`from zango.ai import get_agent

agent = get_agent("${formik.values.name}")
response = agent.run(
    variables={"{...}"}
)`}
											</pre>
										</div>
									)}

									<button
										type="submit"
										disabled={formik.isSubmitting || !formik.isValid}
										className="mt-[16px] w-full rounded-[8px] bg-[#5048ED] py-[12px] font-lato text-[14px] font-semibold text-white transition-colors hover:bg-[#4338CA] disabled:opacity-50"
									>
										{formik.isSubmitting ? 'Saving...' : isEdit ? 'Save Changes' : 'Create Agent'}
									</button>
								</div>
							</form>
						);
					}}
				</Formik>
			</div>
		</div>
	);
}

/* ─── Agent Row (list item) ─── */
function AgentRow({ agent, onEdit, onToggleStatus, onDuplicate, onTestAgent, testingId }) {
	const [expanded, setExpanded] = useState(false);
	const metrics = agent.metrics || {};
	const isTesting = testingId === agent.id;

	return (
		<div className="rounded-[8px] border border-[#E5E7EB] bg-white">
			<div className="flex items-center px-[24px] py-[14px]">
				<button onClick={() => setExpanded(!expanded)} className="mr-[12px] text-[#6B7280] transition-colors hover:text-[#111827]">
					<svg width="12" height="12" viewBox="0 0 12 12" className={`transition-transform ${expanded ? 'rotate-90' : ''}`}>
						<path d="M4.5 2L8.5 6L4.5 10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
					</svg>
				</button>
				<div className="mr-[12px] flex h-[32px] w-[32px] items-center justify-center rounded-[6px] bg-[#F3F4F6]">
					<svg width="18" height="18" viewBox="0 0 18 18" fill="none">
						<rect x="4" y="3" width="10" height="8" rx="2" stroke="#6B7280" strokeWidth="1.2"/>
						<circle cx="7" cy="7" r="1" fill="#6B7280"/><circle cx="11" cy="7" r="1" fill="#6B7280"/>
						<path d="M6 11V14M12 11V14" stroke="#6B7280" strokeWidth="1.2" strokeLinecap="round"/>
					</svg>
				</div>
				<div className="mr-[20px] min-w-[180px]">
					<span className="font-source-sans-pro text-[14px] font-semibold text-[#111827]">{agent.name}</span>
				</div>
				<div className="mr-[20px] min-w-[100px]"><ProviderBadge slug={agent.provider_slug} name={agent.provider_name} /></div>
				<div className="mr-[20px] min-w-[150px]"><span className="font-lato text-[13px] text-[#374151]">{agent.model}</span></div>
				<div className="mr-[20px] min-w-[70px]"><StatusBadge status={agent.status} /></div>
				<div className="mr-[20px] min-w-[40px] text-right"><span className="font-lato text-[14px] font-semibold text-[#111827]">{(metrics.invocations24h || 0).toLocaleString()}</span></div>
				<div className="mr-[20px] min-w-[70px] text-right"><span className="font-lato text-[13px] text-[#374151]">${(metrics.totalCost || 0).toFixed(3)}</span></div>
				<div className="mr-[16px] min-w-[80px] text-right"><span className="font-lato text-[13px] text-[#374151]">${(metrics.avgCost || 0).toFixed(3)}</span></div>
				<button
					onClick={(e) => { e.stopPropagation(); onToggleStatus(agent); }}
					className={`relative ml-auto h-[22px] w-[40px] rounded-full transition-colors ${agent.status === 'active' ? 'bg-[#10B981]' : 'bg-[#D1D5DB]'}`}
				>
					<span className={`absolute top-[2px] h-[18px] w-[18px] rounded-full bg-white shadow transition-transform ${agent.status === 'active' ? 'left-[20px]' : 'left-[2px]'}`} />
				</button>
			</div>

			{expanded && (
				<div className="border-t border-[#E5E7EB] px-[24px] py-[20px]">
					<div className="flex gap-[40px]">
						<div className="flex-1">
							<h4 className="mb-[16px] font-lato text-[11px] font-bold uppercase tracking-[0.8px] text-[#6C747D]">Configuration</h4>
							<div className="flex flex-col gap-[12px]">
								<div className="flex"><span className="w-[120px] shrink-0 font-lato text-[13px] text-[#6B7280]">Description</span><span className="font-lato text-[13px] text-[#111827]">{agent.description || '-'}</span></div>
								<div className="flex items-center"><span className="w-[120px] shrink-0 font-lato text-[13px] text-[#6B7280]">Provider</span><ProviderBadge slug={agent.provider_slug} name={agent.provider_name} /></div>
								<div className="flex"><span className="w-[120px] shrink-0 font-lato text-[13px] text-[#6B7280]">Model</span><span className="font-mono font-lato text-[13px] text-[#111827]">{agent.model}</span></div>
								<div className="flex"><span className="w-[120px] shrink-0 font-lato text-[13px] text-[#6B7280]">Temperature</span><span className="font-lato text-[13px] text-[#111827]">{agent.temperature}</span></div>
								<div className="flex"><span className="w-[120px] shrink-0 font-lato text-[13px] text-[#6B7280]">Max Tokens</span><span className="font-lato text-[13px] text-[#111827]">{(agent.max_tokens || 0).toLocaleString()}</span></div>
								<div className="flex"><span className="w-[120px] shrink-0 font-lato text-[13px] text-[#6B7280]">Timeout</span><span className="font-lato text-[13px] text-[#111827]">{agent.timeout_seconds}s</span></div>
								<div className="flex"><span className="w-[120px] shrink-0 font-lato text-[13px] text-[#6B7280]">System Prompt</span><span className="font-lato text-[13px] font-medium text-[#346BD4]">{agent.system_prompt_name || '-'}</span></div>
								<div className="flex"><span className="w-[120px] shrink-0 font-lato text-[13px] text-[#6B7280]">User Prompt</span><span className="font-lato text-[13px] font-medium text-[#346BD4]">{agent.user_prompt_name || '-'}</span></div>
								<div className="flex items-center"><span className="w-[120px] shrink-0 font-lato text-[13px] text-[#6B7280]">Output</span><Tag color="green">{agent.output_schema}</Tag></div>
								{agent.guardrails?.length > 0 && (
									<div className="flex items-start"><span className="w-[120px] shrink-0 pt-[2px] font-lato text-[13px] text-[#6B7280]">Guardrails</span><div className="flex flex-wrap gap-[6px]">{agent.guardrails.map((g) => <Tag key={g} color="purple">{g}</Tag>)}</div></div>
								)}
								{agent.tools?.length > 0 && (
									<div className="flex items-start"><span className="w-[120px] shrink-0 pt-[2px] font-lato text-[13px] text-[#6B7280]">Tools</span><div className="flex flex-wrap gap-[6px]">{agent.tools.map((t) => <Tag key={t} color="blue">{t}</Tag>)}</div></div>
								)}
							</div>
						</div>
						<div className="w-[400px] shrink-0">
							<h4 className="mb-[16px] font-lato text-[11px] font-bold uppercase tracking-[0.8px] text-[#6C747D]">Usage & Metrics</h4>
							<div className="mb-[8px] grid grid-cols-3 gap-[8px]">
								<MetricCard label="Total Invocations" value={(metrics.totalInvocations || 0).toLocaleString()} />
								<MetricCard label="Success Rate" value={metrics.successRate > 0 ? `${metrics.successRate}%` : '-'} color={metrics.successRate >= 99 ? 'text-[#10B981]' : metrics.successRate >= 95 ? 'text-[#F59E0B]' : 'text-[#111827]'} />
								<MetricCard label="Avg Latency" value={metrics.avgLatency || '-'} color="text-[#346BD4]" />
							</div>
							<div className="grid grid-cols-3 gap-[8px]">
								<MetricCard label="Total Cost" value={metrics.totalCost > 0 ? `$${metrics.totalCost.toFixed(2)}` : '-'} />
								<MetricCard label="Avg In Tokens" value={metrics.avgInputTokens > 0 ? metrics.avgInputTokens.toLocaleString() : '-'} />
								<MetricCard label="Avg Out Tokens" value={metrics.avgOutputTokens > 0 ? metrics.avgOutputTokens.toLocaleString() : '-'} />
							</div>
						</div>
					</div>
					<div className="mt-[20px] flex items-center gap-[12px]">
						<button onClick={() => onTestAgent(agent)} disabled={isTesting} className="flex items-center gap-[6px] rounded-[6px] bg-[#346BD4] px-[14px] py-[7px] font-lato text-[13px] font-medium text-white hover:bg-[#2556B0] disabled:opacity-50">
							{isTesting ? <span className="inline-block h-[10px] w-[10px] animate-spin rounded-full border-[2px] border-white border-t-transparent" /> : <svg width="10" height="12" viewBox="0 0 10 12" fill="none"><path d="M1 1L9 6L1 11V1Z" fill="white"/></svg>}
							{isTesting ? 'Testing...' : 'Test Agent'}
						</button>
						<button onClick={() => onEdit(agent)} className="rounded-[6px] border border-[#DDE2E5] px-[12px] py-[6px] font-lato text-[13px] text-[#111827] hover:bg-[#F9FAFB]">Edit</button>
						<button onClick={() => onDuplicate(agent)} className="rounded-[6px] border border-[#DDE2E5] px-[12px] py-[6px] font-lato text-[13px] text-[#111827] hover:bg-[#F9FAFB]">Duplicate</button>
						<button onClick={() => onToggleStatus(agent)} className={`rounded-[6px] border px-[12px] py-[6px] font-lato text-[13px] ${agent.status === 'active' ? 'border-[#EF4444] text-[#EF4444] hover:bg-[#FEF2F2]' : 'border-[#10B981] text-[#10B981] hover:bg-[#ECFDF5]'}`}>
							{agent.status === 'active' ? 'Disable' : 'Enable'}
						</button>
					</div>
				</div>
			)}
		</div>
	);
}

/* ─── Main Agents Component ─── */
export default function Agents() {
	const { appId } = useParams();
	const triggerApi = useApi();

	const [agents, setAgents] = useState([]);
	const [stats, setStats] = useState({});
	const [providers, setProviders] = useState([]);
	const [prompts, setPrompts] = useState([]);
	const [availableTools, setAvailableTools] = useState([]);
	const [builderOpen, setBuilderOpen] = useState(false);
	const [editingAgent, setEditingAgent] = useState(null);
	const [confirmModal, setConfirmModal] = useState({ show: false });
	const [testingId, setTestingId] = useState(null);
	const [actionLoading, setActionLoading] = useState(false);

	const fetchAgents = useCallback(async () => {
		const { response, success } = await triggerApi({ url: `/api/v1/apps/${appId}/ai/agents/`, type: 'GET', loader: false });
		if (success && response) {
			setAgents(Array.isArray(response.agents?.records || response.agents) ? (response.agents?.records || response.agents) : []);
			if (response.stats) setStats(response.stats);
		}
	}, [appId, triggerApi]);

	const fetchProviders = useCallback(async () => {
		const { response, success } = await triggerApi({ url: `/api/v1/apps/${appId}/ai/providers/`, type: 'GET', loader: false });
		if (success && response) setProviders(Array.isArray(response.providers?.records || response.providers) ? (response.providers?.records || response.providers) : []);
	}, [appId, triggerApi]);

	const fetchPrompts = useCallback(async () => {
		const { response, success } = await triggerApi({ url: `/api/v1/apps/${appId}/ai/prompts/`, type: 'GET', loader: false });
		if (success && response) {
			const records = response.prompts?.records || response.prompts || [];
			// Fetch detail for each to get active_version content for preview
			const detailed = await Promise.all(
				(Array.isArray(records) ? records : []).map(async (p) => {
					const { response: d, success: ok } = await triggerApi({ url: `/api/v1/apps/${appId}/ai/prompts/${p.id}/`, type: 'GET', loader: false });
					return ok && d?.prompt ? { ...p, ...d.prompt } : p;
				})
			);
			setPrompts(detailed);
		}
	}, [appId, triggerApi]);

	const fetchTools = useCallback(async () => {
		const { response, success } = await triggerApi({ url: `/api/v1/apps/${appId}/ai/tools/`, type: 'GET', loader: false });
		if (success && response) setAvailableTools(response.tools?.records || response.tools || []);
	}, [appId, triggerApi]);

	useEffect(() => { fetchAgents(); fetchProviders(); fetchPrompts(); fetchTools(); }, [appId]);

	const handleSave = async (values, { resetForm, setSubmitting }) => {
		const guardrails = values.guardrails_str ? values.guardrails_str.split(',').map((g) => g.trim()).filter(Boolean) : [];
		const tools = values.selected_tools || [];
		const payload = {
			name: values.name, description: values.description,
			provider_id: parseInt(values.provider_id, 10), model: values.model,
			system_prompt_name: values.system_prompt_name || '',
			user_prompt_name: values.user_prompt_name || '',
			temperature: parseFloat(values.temperature), max_tokens: parseInt(values.max_tokens, 10),
			timeout_seconds: parseInt(values.timeout_seconds, 10), output_schema: values.output_schema,
			output_json_schema: values.output_json_schema_str ? JSON.parse(values.output_json_schema_str) : null,
			guardrails, tools,
		};

		const isEdit = !!values._isEdit;
		const url = isEdit ? `/api/v1/apps/${appId}/ai/agents/${editingAgent.id}/` : `/api/v1/apps/${appId}/ai/agents/`;
		const { success } = await triggerApi({ url, type: isEdit ? 'PUT' : 'POST', loader: true, payload });
		setSubmitting(false);
		if (success) {
			setBuilderOpen(false); setEditingAgent(null); resetForm();
			notify('success', isEdit ? 'Agent Updated' : 'Agent Created', `${values.name} ${isEdit ? 'updated' : 'created'} successfully.`);
			fetchAgents();
		}
	};

	const openCreate = () => { setEditingAgent(null); setBuilderOpen(true); };
	const openEdit = (agent) => { setEditingAgent(agent); setBuilderOpen(true); };

	const handleToggleStatus = (agent) => {
		const isDisabling = agent.status === 'active';
		setConfirmModal({
			show: true, agent,
			title: isDisabling ? 'Disable Agent' : 'Enable Agent',
			message: isDisabling ? `Disable "${agent.name}"? It will stop responding to invocations.` : `Enable "${agent.name}"?`,
			confirmLabel: isDisabling ? 'Disable' : 'Enable',
			confirmColor: isDisabling ? 'red' : 'green',
		});
	};

	const confirmToggle = async () => {
		const agent = confirmModal.agent;
		setActionLoading(true);
		const { success } = await triggerApi({ url: `/api/v1/apps/${appId}/ai/agents/${agent.id}/toggle/`, type: 'POST', loader: false, payload: { is_enabled: agent.status !== 'active' } });
		setActionLoading(false); setConfirmModal({ show: false });
		if (success) { notify('success', agent.status === 'active' ? 'Agent Disabled' : 'Agent Enabled', `${agent.name} updated.`); fetchAgents(); }
	};

	const handleDuplicate = async (agent) => {
		const { success } = await triggerApi({ url: `/api/v1/apps/${appId}/ai/agents/${agent.id}/duplicate/`, type: 'POST', loader: true });
		if (success) { notify('success', 'Agent Duplicated', `"${agent.name}" duplicated.`); fetchAgents(); }
	};

	const handleTestAgent = async (agent) => {
		if (testingId) return;
		setTestingId(agent.id);
		const { response, success } = await triggerApi({ url: `/api/v1/apps/${appId}/ai/agents/${agent.id}/test/`, type: 'POST', loader: false, showErrorModal: false });
		setTestingId(null);
		if (success) { const r = response.result || {}; notify('success', 'Test Passed', `${r.latency_ms}ms, ${(r.input_tokens || 0) + (r.output_tokens || 0)} tokens`); }
		else notify('error', 'Test Failed', response?.message || 'Test failed.');
	};

	const activeCount = agents.filter((a) => a.status === 'active').length;
	const disabledCount = agents.filter((a) => a.status === 'disabled').length;

	const builderInitialValues = editingAgent
		? {
				name: editingAgent.name, description: editingAgent.description || '',
				provider_id: editingAgent.provider ? String(editingAgent.provider) : '',
				model: editingAgent.model, system_prompt_name: editingAgent.system_prompt_name || '',
				user_prompt_name: editingAgent.user_prompt_name || '',
				temperature: editingAgent.temperature, max_tokens: editingAgent.max_tokens,
				timeout_seconds: editingAgent.timeout_seconds, output_schema: editingAgent.output_schema,
				guardrails_str: (editingAgent.guardrails || []).join(', '),
				output_json_schema_str: editingAgent.output_json_schema ? JSON.stringify(editingAgent.output_json_schema, null, 2) : '',
				selected_tools: editingAgent.tools || [], _isEdit: true,
		  }
		: {
				name: '', description: '', provider_id: '', model: '',
				system_prompt_name: '', user_prompt_name: '',
				temperature: 0.7, max_tokens: 4096, timeout_seconds: 30,
				output_schema: 'JSON', output_json_schema_str: '', guardrails_str: '', selected_tools: [], _isEdit: false,
		  };

	return (
		<div className="flex flex-col gap-[24px]">
			<div className="rounded-[16px] border border-[#E5E7EB] bg-white p-[24px]">
				<div className="mb-[16px] flex items-center justify-between">
					<div>
						<h2 className="font-source-sans-pro text-[18px] font-semibold text-[#111827]">AI Agents</h2>
						<p className="font-lato text-[14px] text-[#6B7280]">Invocable AI objects that application code uses to interact with LLMs</p>
					</div>
					<button onClick={openCreate} className="flex items-center gap-[6px] rounded-[8px] bg-[#5048ED] px-[16px] py-[8px] font-lato text-[14px] font-medium text-white hover:bg-[#4338CA]">+ Create Agent</button>
				</div>
				<div className="flex items-center gap-[16px]">
					<div className="flex items-center gap-[8px]"><span className="font-lato text-[14px] text-[#6B7280]">Total</span><span className="font-lato text-[14px] font-semibold text-[#111827]">{stats.total_agents ?? agents.length}</span></div>
					<div className="h-[16px] w-[1px] bg-[#E5E7EB]" />
					<div className="flex items-center gap-[8px]"><span className="font-lato text-[14px] text-[#6B7280]">Active</span><span className="font-lato text-[14px] font-semibold text-[#10B981]">{stats.active_agents ?? activeCount}</span></div>
					<div className="h-[16px] w-[1px] bg-[#E5E7EB]" />
					<div className="flex items-center gap-[8px]"><span className="font-lato text-[14px] text-[#6B7280]">Disabled</span><span className="font-lato text-[14px] font-semibold text-[#6B7280]">{disabledCount}</span></div>
				</div>
			</div>

			{agents.length > 0 && (
				<div className="flex items-center px-[72px] font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
					<span className="mr-[20px] min-w-[180px]">Agent</span>
					<span className="mr-[20px] min-w-[100px]">Provider</span>
					<span className="mr-[20px] min-w-[150px]">Model</span>
					<span className="mr-[20px] min-w-[70px]">Status</span>
					<span className="mr-[20px] min-w-[40px] text-right">24h</span>
					<span className="mr-[20px] min-w-[70px] text-right">Total Cost</span>
					<span className="mr-[16px] min-w-[80px] text-right">Avg Run Cost</span>
				</div>
			)}

			<div className="flex flex-col gap-[8px]">
				{agents.length === 0 && (
					<div className="rounded-[8px] border border-dashed border-[#D1D5DB] bg-white px-[24px] py-[48px] text-center">
						<p className="font-lato text-[14px] text-[#9CA3AF]">No agents yet. Click "Create Agent" to get started.</p>
					</div>
				)}
				{agents.map((agent) => (
					<AgentRow key={agent.id} agent={agent} onEdit={openEdit} onToggleStatus={handleToggleStatus} onDuplicate={handleDuplicate} onTestAgent={handleTestAgent} testingId={testingId} />
				))}
			</div>

			<AgentBuilder
				show={builderOpen}
				onClose={() => { setBuilderOpen(false); setEditingAgent(null); }}
				onSave={handleSave}
				initialValues={builderInitialValues}
				providers={providers}
				prompts={prompts}
				availableTools={availableTools}
				appId={appId}
				triggerApi={triggerApi}
				onPromptCreated={fetchPrompts}
			/>

			<ConfirmationModal
				show={confirmModal.show}
				onClose={() => setConfirmModal({ show: false })}
				onConfirm={confirmToggle}
				title={confirmModal.title}
				message={confirmModal.message}
				confirmLabel={confirmModal.confirmLabel}
				confirmColor={confirmModal.confirmColor}
				loading={actionLoading}
			/>
		</div>
	);
}
