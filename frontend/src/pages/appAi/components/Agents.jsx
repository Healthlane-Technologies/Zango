import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { Formik } from 'formik';
import * as Yup from 'yup';
import toast from 'react-hot-toast';
import useApi from '../../../hooks/useApi';
import InputField from '../../../components/Form/InputField.jsx';
import Toast from '../../../components/Notifications/Toast';

// ── Provider logo SVGs ───────────────────────────────────────────────────────

function AnthropicLogo({ size = 18 }) {
	return (
		<svg width={size} height={size} viewBox="0 0 46 32" fill="none" xmlns="http://www.w3.org/2000/svg">
			<path d="M32.73 0h-6.945L38.74 32h6.945L32.73 0Z" fill="#181818"/>
			<path d="M13.055 0 0.315 32h7.109l2.656-6.8h13.6l2.656 6.8h7.11L18.705 0h-5.65Zm-.78 19.367 4.44-11.371 4.44 11.371h-8.88Z" fill="#181818"/>
		</svg>
	);
}

function OpenAILogo({ size = 18 }) {
	return (
		<svg width={size} height={size} viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
			<path d="M29.71 13.09A8.09 8.09 0 0 0 20.78 4a8.1 8.1 0 0 0-13.7 3A8.1 8.1 0 0 0 2.29 18.9 8.1 8.1 0 0 0 11.22 28a8.09 8.09 0 0 0 13.69-3A8.1 8.1 0 0 0 29.71 13.09Zm-12.4 17.3a6 6 0 0 1-3.84-1.39l.19-.11 6.37-3.68a1 1 0 0 0 .53-.92v-8.98l2.69 1.56a.09.09 0 0 1 .05.07v7.44a6 6 0 0 1-6 6.01Zm-12.89-5.5a6 6 0 0 1-.72-4 5.89 5.89 0 0 0 1 .17l6.37 3.68a1 1 0 0 0 1.06 0l7.78-4.49v3.12a.1.1 0 0 1-.04.08L13.48 27a6 6 0 0 1-8.06-2.11ZM3.29 10.52a6 6 0 0 1 3.13-2.64v7.58a1 1 0 0 0 .51.9l7.75 4.47-2.7 1.56a.1.1 0 0 1-.09 0L5.41 18.4a6 6 0 0 1-2.12-7.88Zm22.13 5.15-7.78-4.52 2.7-1.55a.1.1 0 0 1 .09 0l6.48 3.74a6 6 0 0 1-.93 10.82v-7.58a1.06 1.06 0 0 0-.56-.91Zm2.68-4.06a5.9 5.9 0 0 0-1-.17l-6.37-3.68a1 1 0 0 0-1.06 0L11.9 12.25V9.13a.09.09 0 0 1 .04-.08L18.43 5a6 6 0 0 1 9 6.61ZM10.55 17.1l-2.69-1.55a.09.09 0 0 1-.05-.07V8.03a6 6 0 0 1 9.84-4.6l-.19.11-6.37 3.68a1 1 0 0 0-.53.91l-.01 8.97Zm1.46-3.15 3.46-2 3.46 2v4l-3.46 2-3.46-2v-4Z" fill="#181818"/>
		</svg>
	);
}

function AzureLogo({ size = 18 }) {
	return (
		<svg width={size} height={size} viewBox="0 0 96 96" xmlns="http://www.w3.org/2000/svg">
			<defs>
				<linearGradient id="ag-az1" x1="0.957" y1="39.859" x2="0.458" y2="40.44" gradientUnits="userSpaceOnUse">
					<stop offset="0" stopColor="#114a8b"/>
					<stop offset="1" stopColor="#0669bc"/>
				</linearGradient>
				<linearGradient id="ag-az2" x1="0.654" y1="39.92" x2="0.946" y2="40.198" gradientUnits="userSpaceOnUse">
					<stop offset="0" stopOpacity=".3"/>
					<stop offset=".071" stopOpacity=".2"/>
					<stop offset=".321" stopOpacity=".1"/>
					<stop offset=".623" stopOpacity=".05"/>
					<stop offset="1" stopOpacity="0"/>
				</linearGradient>
				<linearGradient id="ag-az3" x1="0.372" y1="39.128" x2="0.796" y2="40.473" gradientUnits="userSpaceOnUse">
					<stop offset="0" stopColor="#3ccbf4"/>
					<stop offset="1" stopColor="#2892df"/>
				</linearGradient>
			</defs>
			<path d="M33.338 6.544h26.038l-27.03 80.087a4.152 4.152 0 0 1-3.933 2.824H8.149a4.145 4.145 0 0 1-3.928-5.47L29.405 9.368a4.152 4.152 0 0 1 3.933-2.824z" fill="url(#ag-az1)"/>
			<path d="M71.175 60.261h-41.29L53.44 6.544H29.395A4.15 4.15 0 0 0 25.47 9.37L.222 83.985a4.145 4.145 0 0 0 3.928 5.47h20.343a4.15 4.15 0 0 0 3.896-2.693z" fill="#0078d4"/>
			<path d="M33.338 6.544a4.12 4.12 0 0 0-3.924 2.848L.247 83.951a4.14 4.14 0 0 0 3.902 5.504h20.484a4.45 4.45 0 0 0 3.415-2.82l4.918-14.507 17.582 16.335a4.24 4.24 0 0 0 2.65.992H74.59L62.194 60.1l-17.055.005L59.47 6.544z" fill="url(#ag-az2)"/>
			<path d="M66.595 9.368A4.145 4.145 0 0 0 62.67 6.54H33.648a4.145 4.145 0 0 1 3.925 2.828l25.184 74.616a4.145 4.145 0 0 1-3.925 5.472h29.02a4.145 4.145 0 0 0 3.924-5.472z" fill="url(#ag-az3)"/>
		</svg>
	);
}

function BedrockLogo({ size = 18 }) {
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
	anthropic:    { bg: '#F5F2FF', accent: '#6B5CE7', label: 'Anthropic' },
	openai:       { bg: '#F0FDF9', accent: '#059669', label: 'OpenAI' },
	azure_openai: { bg: '#EFF6FF', accent: '#2563EB', label: 'Azure OpenAI' },
	bedrock:      { bg: '#FFFBEB', accent: '#D97706', label: 'AWS Bedrock' },
};

function notify(type, title, description) {
	toast.custom(
		(t) => <Toast type={type} toastRef={t} title={title} description={description} />,
		{ duration: 5000, position: 'bottom-left' }
	);
}

function ProviderBadge({ slug, name }) {
	const meta = PROVIDER_META[slug] || { bg: '#F3F4F6', accent: '#6B7280', label: name || slug };
	const Logo = PROVIDER_LOGOS[slug];
	return (
		<span className="flex items-center gap-[6px]">
			<span className="flex h-[22px] w-[22px] items-center justify-center rounded-[4px]" style={{ backgroundColor: meta.bg }}>
				{Logo
					? <Logo size={14} />
					: <span className="font-lato text-[10px] font-bold" style={{ color: meta.accent }}>{(slug || '?')[0].toUpperCase()}</span>
				}
			</span>
			<span className="font-lato text-[13px] text-[#111827]">{name || meta.label}</span>
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
					<button type="button" onClick={() => setShowPreview(!showPreview)} className="font-lato text-[11px] font-medium text-[#346BD4] hover:underline">
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
					type="button"
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

/* ─── Searchable Select ─── */
function SearchableSelect({ value, onChange, options, placeholder, disabled, renderTriggerContent, renderOptionContent }) {
	const [open, setOpen] = useState(false);
	const [search, setSearch] = useState('');
	const selected = options.find((o) => o.value === value);

	const filtered = search.trim()
		? options.filter((o) => o.label.toLowerCase().includes(search.toLowerCase()) || o.sublabel?.toLowerCase().includes(search.toLowerCase()))
		: [...options].sort((a, b) => (b.value === value ? 1 : 0) - (a.value === value ? 1 : 0));

	return (
		<div className="relative">
			<button
				type="button"
				disabled={disabled}
				onClick={() => { setOpen(!open); setSearch(''); }}
				className={`flex w-full items-center justify-between rounded-[6px] border px-[12px] py-[10px] font-lato text-[13px] outline-none transition-colors ${
					disabled ? 'border-[#DDE2E5] bg-[#F9FAFB] text-[#9CA3AF]' : open ? 'border-[#5048ED]' : 'border-[#DDE2E5] hover:border-[#9CA3AF]'
				}`}
			>
				{selected ? (
					renderTriggerContent ? (
						<span className="flex-1 min-w-0">{renderTriggerContent(selected)}</span>
					) : (
						<span className="flex-1 truncate text-left text-[#111827]">
							{selected.label}
							{selected.sublabel && <span className="ml-[6px] font-mono text-[11px] text-[#9CA3AF]">{selected.sublabel}</span>}
						</span>
					)
				) : (
					<span className="flex-1 text-left text-[#9CA3AF]">{disabled ? 'Select a provider first' : placeholder}</span>
				)}
				<svg width="12" height="12" viewBox="0 0 12 12" fill="none" className={`ml-[6px] shrink-0 text-[#9CA3AF] transition-transform ${open ? 'rotate-180' : ''}`}>
					<path d="M2 4L6 8L10 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
				</svg>
			</button>

			{open && !disabled && (
				<>
					<div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
					<div className="absolute z-20 mt-[4px] w-full rounded-[8px] border border-[#E5E7EB] bg-white shadow-lg">
						<div className="border-b border-[#F3F4F6] p-[8px]">
							<div className="relative">
								<svg className="absolute left-[8px] top-1/2 -translate-y-1/2 text-[#9CA3AF]" width="13" height="13" viewBox="0 0 14 14" fill="none">
									<circle cx="6" cy="6" r="4.5" stroke="currentColor" strokeWidth="1.2"/>
									<path d="M9.5 9.5L12 12" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
								</svg>
								<input
									autoFocus
									type="text"
									value={search}
									onChange={(e) => setSearch(e.target.value)}
									placeholder="Search…"
									className="w-full rounded-[4px] border border-[#E5E7EB] py-[6px] pl-[26px] pr-[8px] font-lato text-[12px] outline-none focus:border-[#5048ED]"
								/>
							</div>
						</div>
						<div className="max-h-[220px] overflow-y-auto">
							{filtered.length === 0 ? (
								<p className="px-[12px] py-[10px] font-lato text-[12px] text-[#9CA3AF]">No matches</p>
							) : filtered.map((o) => (
								<button
									key={o.value}
									type="button"
									onClick={() => { onChange(o.value); setOpen(false); setSearch(''); }}
									className={`flex w-full items-center justify-between px-[12px] py-[9px] text-left transition-colors hover:bg-[#F9FAFB] ${value === o.value ? 'bg-[#F5F3FF]' : ''}`}
								>
									{renderOptionContent ? (
										<span className="min-w-0 flex-1">{renderOptionContent(o)}</span>
									) : (
										<div className="min-w-0 flex-1">
											<p className="truncate font-lato text-[13px] text-[#111827]">{o.label}</p>
											{o.sublabel && <p className="font-mono text-[11px] text-[#9CA3AF]">{o.sublabel}</p>}
										</div>
									)}
									{value === o.value && (
										<svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="ml-[8px] shrink-0">
											<circle cx="7" cy="7" r="6" fill="#5048ED"/>
											<path d="M4 7L6 9L10 5" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
										</svg>
									)}
								</button>
							))}
						</div>
					</div>
				</>
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
			<div className="m-auto flex h-[95vh] w-full max-w-[1100px] flex-col rounded-[16px] bg-white shadow-2xl">
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
						output_json_schema_str: Yup.string().when('output_schema', {
							is: 'JSON',
							then: (schema) => schema.required('JSON Schema is required when output is set to JSON').test('valid-json', 'Invalid JSON', (val) => { try { JSON.parse(val); return true; } catch { return false; } }),
							otherwise: (schema) => schema.optional(),
						}),
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
																<SearchableSelect
													value={String(formik.values.provider_id || '')}
													onChange={(val) => {
														formik.setFieldValue('provider_id', val);
														const prov = providers.find((p) => String(p.id) === val);
														formik.setFieldValue('model', prov?.default_model || '');
													}}
													placeholder="Select a provider…"
													options={providers.filter((p) => p.is_enabled).map((p) => ({ value: String(p.id), label: p.name, sublabel: p.provider_slug }))}
													renderTriggerContent={(o) => <ProviderBadge slug={o.sublabel} name={o.label} />}
													renderOptionContent={(o) => (
														<div className="flex items-center gap-[8px]">
															<ProviderBadge slug={o.sublabel} name={o.label} />
														</div>
													)}
												/>
												{formik.touched.provider_id && formik.errors.provider_id && (
													<p className="mt-[4px] font-lato text-[12px] text-[#EF4444]">{formik.errors.provider_id}</p>
												)}
											</div>

											<div>
												<label className="mb-[4px] block font-lato text-[13px] font-semibold text-[#374151]">Model</label>
												{(() => {
													const modelOptions = [
														...models.map((m) => ({ value: m.model_id, label: m.display_name || m.model_id, sublabel: m.display_name && m.display_name !== m.model_id ? m.model_id : undefined })),
														...(models.length === 0 && selectedProvider?.default_model ? [{ value: selectedProvider.default_model, label: selectedProvider.default_model }] : []),
													];
													return (
														<SearchableSelect
															value={formik.values.model}
															onChange={(val) => formik.setFieldValue('model', val)}
															placeholder="Select a model…"
															disabled={!formik.values.provider_id}
															options={modelOptions}
														/>
													);
												})()}
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
															JSON Schema <span className="font-normal text-[#EF4444]">*</span>
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

									{/* Section 5: Memory */}
									<div className="mb-[24px]">
										<h3 className="mb-[4px] font-source-sans-pro text-[16px] font-semibold text-[#111827]">Memory</h3>
										<p className="mb-[16px] font-lato text-[13px] text-[#9CA3AF]">
											Enable session-scoped conversation history for multi-turn interactions
										</p>
										<div className="flex flex-col gap-[16px]">
											<div className="flex items-center justify-between rounded-[8px] border border-[#E5E7EB] p-[16px]">
												<div>
													<p className="font-lato text-[13px] font-semibold text-[#374151]">Enable Memory</p>
													<p className="font-lato text-[12px] text-[#9CA3AF]">
														Persist conversation history across <code className="rounded bg-[#F3F4F6] px-[3px] py-[0.5px] text-[11px]">agent.run()</code> calls using a <code className="rounded bg-[#F3F4F6] px-[3px] py-[0.5px] text-[11px]">session_id</code>
													</p>
												</div>
												<button
													type="button"
													onClick={() => formik.setFieldValue('memory_enabled', !formik.values.memory_enabled)}
													className={`relative ml-[16px] h-[22px] w-[40px] flex-shrink-0 rounded-full transition-colors ${formik.values.memory_enabled ? 'bg-[#10B981]' : 'bg-[#D1D5DB]'}`}
												>
													<span className={`absolute top-[2px] h-[18px] w-[18px] rounded-full bg-white shadow transition-all ${formik.values.memory_enabled ? 'left-[20px]' : 'left-[2px]'}`} />
												</button>
											</div>
											{formik.values.memory_enabled && (
												<div>
													<label className="mb-[4px] block font-lato text-[13px] font-semibold text-[#374151]">Max Messages in History</label>
													<p className="mb-[6px] font-lato text-[12px] text-[#9CA3AF]">
														Maximum number of past user/assistant exchanges to include per call (1–200)
													</p>
													<input
														name="memory_max_messages"
														type="number"
														min="1"
														max="200"
														value={formik.values.memory_max_messages}
														onChange={formik.handleChange}
														onBlur={formik.handleBlur}
														className="w-[120px] rounded-[6px] border border-[#DDE2E5] px-[12px] py-[10px] font-lato text-[13px] outline-none focus:border-[#5048ED]"
													/>
												</div>
											)}
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
{formik.values.memory_enabled
? `from zango.ai import get_agent

agent = get_agent("${formik.values.name}")

# First turn — session auto-created
r = agent.run(input="Hello!")
session_id = r.session_id

# Continue the conversation
r = agent.run(
    input="...",
    session_id=session_id,
)`
: formik.values.user_prompt_name
? `from zango.ai import get_agent

agent = get_agent("${formik.values.name}")
response = agent.run(
    variables={"{...}"}
)`
: `from zango.ai import get_agent

agent = get_agent("${formik.values.name}")
response = agent.run(
    input="Your message here"
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

/* ─── JSON Schema Collapsible ─── */
function JsonSchemaCollapsible({ schema }) {
	const [open, setOpen] = useState(false);
	const formatted = JSON.stringify(schema, null, 2);
	return (
		<div className="mt-[6px]">
			<button
				type="button"
				onClick={() => setOpen(!open)}
				className="flex items-center gap-[4px] font-lato text-[11px] font-medium text-[#346BD4] hover:underline"
			>
				<svg
					width="10" height="10" viewBox="0 0 10 10" fill="none"
					className={`transition-transform ${open ? 'rotate-90' : ''}`}
				>
					<path d="M3 2L7 5L3 8" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
				</svg>
				{open ? 'Hide Schema' : 'View Schema'}
			</button>
			{open && (
				<div className="mt-[6px] max-h-[200px] overflow-y-auto rounded-[6px] bg-[#1F2937] p-[10px]">
					<pre className="whitespace-pre-wrap break-words font-mono text-[11px] leading-[18px] text-[#D1D5DB]">
						{formatted}
					</pre>
				</div>
			)}
		</div>
	);
}

/* ─── Agent Row (list item) ─── */
function AgentRow({ agent, onEdit, onToggleStatus, onDuplicate, onTestAgent, testingId, appId, triggerApi }) {
	const [expanded, setExpanded] = useState(false);
	const [showSessions, setShowSessions] = useState(false);
	const [sessions, setSessions] = useState([]);
	const [sessionsLoading, setSessionsLoading] = useState(false);
	const [copied, setCopied] = useState(false);
	const metrics = agent.metrics || {};
	const isTesting = testingId === agent.id;

	const fetchSessions = async () => {
		setSessionsLoading(true);
		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/ai/agents/${agent.id}/sessions/`,
			type: 'GET',
			loader: false,
		});
		setSessionsLoading(false);
		if (success && response) {
			setSessions(response.sessions?.records || response.sessions || []);
		}
	};

	const handleShowSessions = () => {
		if (!showSessions) fetchSessions();
		setShowSessions(!showSessions);
	};

	const handleClearSession = async (sessionId) => {
		const { success } = await triggerApi({
			url: `/api/v1/apps/${appId}/ai/agents/${agent.id}/sessions/${encodeURIComponent(sessionId)}/`,
			type: 'DELETE',
			loader: false,
		});
		if (success) {
			notify('success', 'Session Cleared', `Session "${sessionId}" cleared.`);
			fetchSessions();
		}
	};

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
								<div className="flex items-start">
									<span className="w-[120px] shrink-0 font-lato text-[13px] text-[#6B7280]">Output</span>
									<div>
										<Tag color="green">{agent.output_schema}</Tag>
										{agent.output_schema === 'JSON' && agent.output_json_schema && (
											<JsonSchemaCollapsible schema={agent.output_json_schema} />
										)}
									</div>
								</div>
								{agent.guardrails?.length > 0 && (
									<div className="flex items-start"><span className="w-[120px] shrink-0 pt-[2px] font-lato text-[13px] text-[#6B7280]">Guardrails</span><div className="flex flex-wrap gap-[6px]">{agent.guardrails.map((g) => <Tag key={g} color="purple">{g}</Tag>)}</div></div>
								)}
								{agent.tools?.length > 0 && (
									<div className="flex items-start"><span className="w-[120px] shrink-0 pt-[2px] font-lato text-[13px] text-[#6B7280]">Tools</span><div className="flex flex-wrap gap-[6px]">{agent.tools.map((t) => <Tag key={t} color="blue">{t}</Tag>)}</div></div>
								)}
								<div className="flex">
									<span className="w-[120px] shrink-0 font-lato text-[13px] text-[#6B7280]">Memory</span>
									<span className={`font-lato text-[13px] ${agent.memory_enabled ? 'text-[#10B981]' : 'text-[#6B7280]'}`}>
										{agent.memory_enabled ? `Enabled (${agent.memory_max_messages} msg window)` : 'Disabled'}
									</span>
								</div>
							</div>
						</div>
						<div className="w-[400px] shrink-0 flex flex-col gap-[12px]">
							{/* Metrics */}
							<div>
								<p className="mb-[8px] font-lato text-[11px] font-bold uppercase tracking-[0.8px] text-[#6C747D]">Usage & Metrics</p>
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

							{/* Code snippet */}
							<div className="rounded-[8px] bg-[#1F2937] p-[14px]">
								<div className="mb-[10px] flex items-center justify-between">
									<span className="font-lato text-[10px] font-bold uppercase tracking-[0.6px] text-[#9CA3AF]">Use in Code</span>
									<button
										onClick={() => {
											const snippet = agent.memory_enabled
												? `from zango.ai import get_agent\n\nagent = get_agent("${agent.name}")\n\n# First turn — session auto-created\nr = agent.run(input="Hello!")\nsession_id = r.session_id\n\n# Continue the conversation\nr = agent.run(\n    input="...",\n    session_id=session_id,\n)`
												: agent.user_prompt_name
												? `from zango.ai import get_agent\n\nagent = get_agent("${agent.name}")\nresponse = agent.run(\n    variables={...}\n)`
												: `from zango.ai import get_agent\n\nagent = get_agent("${agent.name}")\nresponse = agent.run(\n    input="Your message here"\n)`;
											navigator.clipboard.writeText(snippet);
											setCopied(true);
											setTimeout(() => setCopied(false), 2000);
										}}
										className="flex items-center gap-[4px] font-lato text-[11px] text-[#6B7280] hover:text-[#D1D5DB] transition-colors"
									>
										{copied ? (
											<>
												<svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 6L5 9L10 3" stroke="#10B981" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
												<span className="text-[#10B981]">Copied</span>
											</>
										) : (
											<>
												<svg width="12" height="12" viewBox="0 0 12 12" fill="none"><rect x="4" y="1" width="7" height="8" rx="1" stroke="currentColor" strokeWidth="1.2"/><path d="M1 4v7h7" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/></svg>
												<span>Copy</span>
											</>
										)}
									</button>
								</div>
								<pre className="font-mono text-[11px] leading-[19px] text-[#D1D5DB] whitespace-pre-wrap">
{agent.memory_enabled
? `from zango.ai import get_agent

agent = get_agent("${agent.name}")

# First turn — session auto-created
r = agent.run(input="Hello!")
session_id = r.session_id

# Continue the conversation
r = agent.run(
    input="...",
    session_id=session_id,
)`
: agent.user_prompt_name
? `from zango.ai import get_agent

agent = get_agent("${agent.name}")
response = agent.run(
    variables={...}
)`
: `from zango.ai import get_agent

agent = get_agent("${agent.name}")
response = agent.run(
    input="Your message here"
)`}
								</pre>
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
						{agent.memory_enabled && (
							<button onClick={handleShowSessions} className={`rounded-[6px] border px-[12px] py-[6px] font-lato text-[13px] ${showSessions ? 'border-[#5048ED] bg-[#EEF2FF] text-[#5048ED]' : 'border-[#DDE2E5] text-[#111827] hover:bg-[#F9FAFB]'}`}>
								Sessions {agent.session_count > 0 ? `(${agent.session_count})` : ''}
							</button>
						)}
					</div>

					{/* Sessions Panel */}
					{showSessions && agent.memory_enabled && (
						<div className="mt-[16px] rounded-[8px] border border-[#E5E7EB] bg-[#F9FAFB] p-[16px]">
							<div className="mb-[12px] flex items-center justify-between">
								<h4 className="font-lato text-[13px] font-semibold text-[#111827]">Memory Sessions</h4>
								<button onClick={fetchSessions} className="font-lato text-[12px] text-[#346BD4] hover:underline">
									Refresh
								</button>
							</div>
							{sessionsLoading ? (
								<p className="font-lato text-[13px] text-[#6B7280]">Loading sessions...</p>
							) : sessions.length === 0 ? (
								<p className="font-lato text-[13px] text-[#9CA3AF]">No sessions yet. Sessions are created automatically when agent.run() is called with a session_id.</p>
							) : (
								<table className="w-full border-collapse">
									<thead>
										<tr className="border-b border-[#E5E7EB]">
											<th className="pb-[8px] text-left font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Session ID</th>
											<th className="pb-[8px] text-left font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">User Ref</th>
											<th className="pb-[8px] text-right font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Messages</th>
											<th className="pb-[8px] text-right font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Last Active</th>
											<th className="pb-[8px] text-right font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Status</th>
											<th className="pb-[8px]" />
										</tr>
									</thead>
									<tbody>
										{sessions.map((s) => (
											<tr key={s.id} className="border-b border-[#F3F4F6]">
												<td className="py-[8px] font-mono font-lato text-[12px] text-[#111827]">{s.session_id}</td>
												<td className="py-[8px] font-lato text-[12px] text-[#6B7280]">{s.user_ref || '-'}</td>
												<td className="py-[8px] text-right font-lato text-[12px] text-[#374151]">{s.message_count}</td>
												<td className="py-[8px] text-right font-lato text-[12px] text-[#6B7280]">{new Date(s.last_active_at).toLocaleString()}</td>
												<td className="py-[8px] text-right">
													<span className={`inline-flex items-center gap-[4px] font-lato text-[11px] font-medium ${s.is_active ? 'text-[#10B981]' : 'text-[#6B7280]'}`}>
														<span className={`h-[5px] w-[5px] rounded-full ${s.is_active ? 'bg-[#10B981]' : 'bg-[#9CA3AF]'}`} />
														{s.is_active ? 'Active' : 'Cleared'}
													</span>
												</td>
												<td className="py-[8px] text-right">
													{s.is_active && (
														<button
															onClick={() => handleClearSession(s.session_id)}
															className="font-lato text-[12px] text-[#EF4444] hover:underline"
														>
															Clear
														</button>
													)}
												</td>
											</tr>
										))}
									</tbody>
								</table>
							)}
						</div>
					)}
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
	const [testingId, setTestingId] = useState(null);

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
		try {
			const guardrails = values.guardrails_str ? values.guardrails_str.split(',').map((g) => g.trim()).filter(Boolean) : [];
			const tools = values.selected_tools || [];

			let output_json_schema = undefined;
			if (values.output_schema === 'JSON' && values.output_json_schema_str) {
				output_json_schema = JSON.parse(values.output_json_schema_str);
			}

			const payload = {
				name: values.name, description: values.description,
				provider_id: parseInt(values.provider_id, 10), model: values.model,
				system_prompt_name: values.system_prompt_name || '',
				user_prompt_name: values.user_prompt_name || '',
				temperature: parseFloat(values.temperature), max_tokens: parseInt(values.max_tokens, 10),
				timeout_seconds: parseInt(values.timeout_seconds, 10), output_schema: values.output_schema,
				guardrails, tools,
				memory_enabled: values.memory_enabled,
				memory_max_messages: parseInt(values.memory_max_messages, 10) || 20,
			};
			if (output_json_schema !== undefined) {
				payload.output_json_schema = output_json_schema;
			}

			const isEdit = !!values._isEdit;
			const url = isEdit ? `/api/v1/apps/${appId}/ai/agents/${editingAgent.id}/` : `/api/v1/apps/${appId}/ai/agents/`;
			const { success, response } = await triggerApi({ url, type: isEdit ? 'PUT' : 'POST', loader: false, payload });
			if (success) {
				setBuilderOpen(false); setEditingAgent(null); resetForm();
				notify('success', isEdit ? 'Agent Updated' : 'Agent Created', `${values.name} ${isEdit ? 'updated' : 'created'} successfully.`);
				fetchAgents();
			} else {
				const msg = response?.message || 'Something went wrong. Please try again.';
				notify('error', isEdit ? 'Failed to Update Agent' : 'Failed to Create Agent', msg);
			}
		} finally {
			setSubmitting(false);
		}
	};

	const openCreate = () => { setEditingAgent(null); setBuilderOpen(true); };
	const openEdit = (agent) => { setEditingAgent(agent); setBuilderOpen(true); };

	const handleToggleStatus = async (agent) => {
		const newEnabled = agent.status !== 'active';
		const { success } = await triggerApi({ url: `/api/v1/apps/${appId}/ai/agents/${agent.id}/toggle/`, type: 'POST', loader: false, payload: { is_enabled: newEnabled } });
		if (success) { notify('success', newEnabled ? 'Agent Enabled' : 'Agent Disabled', `${agent.name} updated.`); fetchAgents(); }
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
				selected_tools: editingAgent.tools || [],
				memory_enabled: editingAgent.memory_enabled ?? false,
				memory_max_messages: editingAgent.memory_max_messages ?? 20,
				_isEdit: true,
		  }
		: {
				name: '', description: '', provider_id: '', model: '',
				system_prompt_name: '', user_prompt_name: '',
				temperature: 0.7, max_tokens: 4096, timeout_seconds: 30,
				output_schema: 'JSON', output_json_schema_str: '', guardrails_str: '', selected_tools: [],
				memory_enabled: false, memory_max_messages: 20,
				_isEdit: false,
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
					<AgentRow key={agent.id} agent={agent} onEdit={openEdit} onToggleStatus={handleToggleStatus} onDuplicate={handleDuplicate} onTestAgent={handleTestAgent} testingId={testingId} appId={appId} triggerApi={triggerApi} />
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

		</div>
	);
}
