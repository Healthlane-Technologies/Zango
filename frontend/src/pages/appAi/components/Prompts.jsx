import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { Formik } from 'formik';
import * as Yup from 'yup';
import toast from 'react-hot-toast';
import useApi from '../../../hooks/useApi';
import Modal from '../../../components/Modal';
import InputField from '../../../components/Form/InputField.jsx';
import Toast from '../../../components/Notifications/Toast';

function notify(type, title, description) {
	toast.custom(
		(t) => (
			<Toast type={type} toastRef={t} title={title} description={description} />
		),
		{ duration: 5000, position: 'bottom-left' }
	);
}

function StatusBadge({ status }) {
	const styles = {
		active: 'bg-[#ECFDF5] text-[#10B981]',
		draft: 'bg-[#FEF3C7] text-[#D97706]',
		inactive: 'bg-[#F3F4F6] text-[#6B7280]',
	};
	return (
		<span
			className={`inline-flex items-center gap-[4px] rounded-[4px] px-[8px] py-[2px] font-lato text-[12px] font-medium ${styles[status] || styles.inactive}`}
		>
			{status === 'active' && (
				<span className="inline-block h-[6px] w-[6px] rounded-full bg-[#10B981]" />
			)}
			{status.charAt(0).toUpperCase() + status.slice(1)}
		</span>
	);
}

function TypeBadge({ type }) {
	const isSystem = type === 'system';
	return (
		<span
			className={`rounded-[4px] px-[10px] py-[3px] font-lato text-[12px] font-medium ${
				isSystem
					? 'bg-[#EFF6FF] text-[#346BD4]'
					: 'bg-[#F3E8FF] text-[#7C3AED]'
			}`}
		>
			{isSystem ? 'System' : 'User'}
		</span>
	);
}

function HighlightedContent({ content }) {
	if (!content) return null;
	const parts = content.split(/(\{\{\w+\}\})/g);
	return (
		<pre className="whitespace-pre-wrap break-words font-mono text-[13px] leading-[22px] text-[#D1D5DB]">
			{parts.map((part, i) =>
				/^\{\{\w+\}\}$/.test(part) ? (
					<span key={i} className="text-[#F59E0B]">
						{part}
					</span>
				) : (
					<span key={i} className="text-[#E5E7EB]">
						{part}
					</span>
				)
			)}
		</pre>
	);
}

function ConfirmationModal({ show, onClose, onConfirm, title, message, confirmLabel, confirmColor, loading }) {
	if (!show) return null;
	const colorClasses = {
		red: 'bg-[#EF4444] hover:bg-[#DC2626]',
		green: 'bg-[#10B981] hover:bg-[#059669]',
		blue: 'bg-[#346BD4] hover:bg-[#2556B0]',
		amber: 'bg-[#F59E0B] hover:bg-[#D97706]',
	};
	return (
		<Modal
			label={title}
			show={show}
			closeModal={onClose}
			ModalBody={
				<div className="flex flex-col gap-[24px]">
					<p className="font-lato text-[14px] leading-[22px] text-[#6B7280]">{message}</p>
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

function VersionHistory({ versions, activeVersionId, onPromote, promotingId }) {
	return (
		<div className="flex flex-col gap-[12px]">
			<h4 className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
				Version History
			</h4>
			<div className="flex flex-col gap-[8px]">
				{versions.map((v) => {
					const isActive = v.status === 'active';
					const isPromoting = promotingId === v.id;
					return (
						<div
							key={v.id}
							className={`flex items-start gap-[12px] rounded-[8px] border px-[16px] py-[12px] ${
								isActive ? 'border-[#10B981] bg-[#F0FDF4]' : 'border-[#E5E7EB] bg-white'
							}`}
						>
							<div
								className={`mt-[4px] h-[10px] w-[10px] rounded-full flex-shrink-0 ${
									isActive ? 'bg-[#10B981]' : 'bg-[#D1D5DB]'
								}`}
							/>
							<div className="flex-1 min-w-0">
								<div className="flex items-center gap-[8px]">
									<span className="font-lato text-[14px] font-semibold text-[#111827]">
										v{v.version_number}
									</span>
									<StatusBadge status={v.status} />
								</div>
								<p className="mt-[2px] font-lato text-[13px] text-[#374151] truncate">
									{v.change_description || 'No description'}
								</p>
								<p className="mt-[2px] font-lato text-[12px] text-[#9CA3AF]">
									{new Date(v.created_at).toLocaleDateString('en-US', {
										month: 'short',
										day: 'numeric',
										year: 'numeric',
									})}
									{v.created_by ? ` \u00b7 by ${v.created_by}` : ''}
								</p>
							</div>
							{!isActive && (
								<button
									onClick={() => onPromote(v)}
									disabled={isPromoting}
									className="flex-shrink-0 rounded-[6px] border border-[#346BD4] px-[12px] py-[4px] font-lato text-[12px] font-medium text-[#346BD4] transition-colors hover:bg-[#EFF6FF] disabled:opacity-50"
								>
									{isPromoting ? 'Promoting...' : 'Promote'}
								</button>
							)}
						</div>
					);
				})}
			</div>
		</div>
	);
}

function PromptRow({ prompt, onEdit, onNewVersion, onPromote, onDelete, onCompare, promotingId }) {
	const [expanded, setExpanded] = useState(false);
	const [compareV1, setCompareV1] = useState('');
	const [compareV2, setCompareV2] = useState('');
	const [compareResult, setCompareResult] = useState(null);
	const [comparing, setComparing] = useState(false);
	const { appId } = useParams();
	const triggerApi = useApi();

	const activeVersion = prompt.active_version;
	const versions = prompt.versions || [];

	const handleCompare = async () => {
		if (!compareV1 || !compareV2 || compareV1 === compareV2) return;
		setComparing(true);
		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/ai/prompts/${prompt.id}/compare/?v1=${compareV1}&v2=${compareV2}`,
			type: 'GET',
			loader: false,
			showErrorModal: false,
		});
		setComparing(false);
		if (success) {
			setCompareResult(response);
		} else {
			notify('error', 'Compare Failed', response?.message || 'Could not compare versions');
		}
	};

	return (
		<div className="rounded-[8px] border border-[#E5E7EB] bg-white">
			{/* Collapsed Row */}
			<div className="flex items-center px-[24px] py-[16px]">
				<button
					onClick={() => setExpanded(!expanded)}
					className="mr-[16px] text-[#6B7280] transition-colors hover:text-[#111827]"
				>
					<svg
						width="12" height="12" viewBox="0 0 12 12"
						className={`transition-transform ${expanded ? 'rotate-90' : ''}`}
					>
						<path d="M4.5 2L8.5 6L4.5 10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
					</svg>
				</button>

				<div className="mr-[16px] flex h-[32px] w-[32px] items-center justify-center rounded-[6px] bg-[#FEF3C7]">
					<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
						<path d="M3 3H13V11H8L5 14V11H3V3Z" stroke="#D97706" strokeWidth="1.2" fill="none" strokeLinejoin="round"/>
					</svg>
				</div>

				<div className="min-w-[200px] mr-[24px]">
					<span className="font-source-sans-pro text-[15px] font-semibold text-[#111827]">
						{prompt.name}
					</span>
				</div>

				<div className="ml-auto flex items-center gap-[32px]">
					<div className="text-center">
						<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
							Type
						</span>
						<div className="mt-[2px]">
							<TypeBadge type={prompt.type} />
						</div>
					</div>

					<div className="text-center">
						<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
							Active Version
						</span>
						<p className="mt-[2px] font-lato text-[14px] font-semibold text-[#111827]">
							{prompt.active_version_number ? `v${prompt.active_version_number}` : '-'}
						</p>
					</div>

					<div className="text-center">
						<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
							Total Versions
						</span>
						<p className="mt-[2px] font-lato text-[14px] text-[#111827]">
							{prompt.total_versions || 0}
						</p>
					</div>

					<div className="text-center">
						<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
							Last Modified
						</span>
						<p className="mt-[2px] font-lato text-[13px] text-[#111827]">
							{prompt.modified_at
								? new Date(prompt.modified_at).toLocaleDateString('en-US', {
										month: 'short',
										day: 'numeric',
										year: 'numeric',
								  })
								: '-'}
						</p>
					</div>
				</div>
			</div>

			{/* Expanded Detail */}
			{expanded && (
				<div className="border-t border-[#E5E7EB] px-[24px] py-[20px]">
					<div className="flex gap-[32px]">
						{/* Left: Active Version Content */}
						<div className="flex-1 min-w-0">
							<h4 className="mb-[12px] font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
								Active Version {activeVersion ? `(V${activeVersion.version_number})` : ''}
							</h4>

							{activeVersion ? (
								<>
									<div className="rounded-[8px] bg-[#1F2937] p-[20px] mb-[16px] max-h-[400px] overflow-y-auto">
										<HighlightedContent content={activeVersion.content} />
									</div>

									{activeVersion.variables && activeVersion.variables.length > 0 && (
										<div className="mb-[16px]">
											<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
												Variables
											</span>
											<div className="mt-[6px] flex flex-wrap gap-[6px]">
												{activeVersion.variables.map((v) => (
													<span
														key={v}
														className="rounded-[4px] bg-[#FEF3C7] px-[10px] py-[3px] font-mono text-[12px] text-[#92400E]"
													>
														{`{{${v}}}`}
													</span>
												))}
											</div>
										</div>
									)}
								</>
							) : (
								<p className="font-lato text-[14px] text-[#9CA3AF]">
									No active version set.
								</p>
							)}

							{/* Actions */}
							<div className="flex items-center gap-[12px] mt-[16px]">
								<button
									onClick={() => onNewVersion(prompt)}
									className="flex items-center gap-[6px] rounded-[6px] bg-[#5048ED] px-[14px] py-[7px] font-lato text-[13px] font-medium text-white transition-colors hover:bg-[#4338CA]"
								>
									+ New Version
								</button>
								<button
									onClick={() => onEdit(prompt)}
									className="flex items-center gap-[6px] rounded-[6px] border border-[#DDE2E5] px-[12px] py-[6px] font-lato text-[13px] text-[#111827] transition-colors hover:bg-[#F9FAFB]"
								>
									Edit Prompt
								</button>
								<button
									onClick={() => onDelete(prompt)}
									className="flex items-center gap-[6px] rounded-[6px] border border-[#EF4444] px-[12px] py-[6px] font-lato text-[13px] text-[#EF4444] transition-colors hover:bg-[#FEF2F2]"
								>
									Delete
								</button>
							</div>

							{/* Compare */}
							{versions.length >= 2 && (
								<div className="mt-[20px] flex items-center gap-[8px]">
									<span className="font-lato text-[12px] font-semibold uppercase tracking-[0.6px] text-[#6C747D]">
										Compare
									</span>
									<select
										value={compareV1}
										onChange={(e) => { setCompareV1(e.target.value); setCompareResult(null); }}
										className="rounded-[6px] border border-[#DDE2E5] px-[8px] py-[4px] font-lato text-[13px] text-[#111827]"
									>
										<option value="">v...</option>
										{versions.map((v) => (
											<option key={v.id} value={v.version_number}>v{v.version_number}</option>
										))}
									</select>
									<span className="font-lato text-[12px] text-[#9CA3AF]">vs</span>
									<select
										value={compareV2}
										onChange={(e) => { setCompareV2(e.target.value); setCompareResult(null); }}
										className="rounded-[6px] border border-[#DDE2E5] px-[8px] py-[4px] font-lato text-[13px] text-[#111827]"
									>
										<option value="">v...</option>
										{versions.map((v) => (
											<option key={v.id} value={v.version_number}>v{v.version_number}</option>
										))}
									</select>
									<button
										onClick={handleCompare}
										disabled={!compareV1 || !compareV2 || compareV1 === compareV2 || comparing}
										className="flex items-center gap-[4px] rounded-[6px] border border-[#346BD4] px-[12px] py-[4px] font-lato text-[12px] font-medium text-[#346BD4] transition-colors hover:bg-[#EFF6FF] disabled:opacity-40"
									>
										{comparing ? 'Loading...' : 'View Diff'}
									</button>
								</div>
							)}

							{/* Compare Result */}
							{compareResult && (
								<div className="mt-[12px] grid grid-cols-2 gap-[12px]">
									<div>
										<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
											V{compareResult.version_1.version_number}
										</span>
										<div className="mt-[4px] rounded-[6px] bg-[#1F2937] p-[12px] max-h-[200px] overflow-y-auto">
											<HighlightedContent content={compareResult.version_1.content} />
										</div>
									</div>
									<div>
										<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
											V{compareResult.version_2.version_number}
										</span>
										<div className="mt-[4px] rounded-[6px] bg-[#1F2937] p-[12px] max-h-[200px] overflow-y-auto">
											<HighlightedContent content={compareResult.version_2.content} />
										</div>
									</div>
								</div>
							)}
						</div>

						{/* Right: Version History */}
						<div className="w-[340px] flex-shrink-0">
							<VersionHistory
								versions={versions}
								activeVersionId={activeVersion?.id}
								onPromote={onPromote}
								promotingId={promotingId}
							/>
						</div>
					</div>
				</div>
			)}
		</div>
	);
}

export default function Prompts() {
	const { appId } = useParams();
	const triggerApi = useApi();

	const [prompts, setPrompts] = useState([]);
	const [stats, setStats] = useState({});
	const [createModalOpen, setCreateModalOpen] = useState(false);
	const [editModalOpen, setEditModalOpen] = useState(false);
	const [editingPrompt, setEditingPrompt] = useState(null);
	const [newVersionModalOpen, setNewVersionModalOpen] = useState(false);
	const [versionPrompt, setVersionPrompt] = useState(null);
	const [confirmModal, setConfirmModal] = useState({ show: false });
	const [promotingId, setPromotingId] = useState(null);
	const [actionLoading, setActionLoading] = useState(false);

	// Fetch prompts list then load detail for each (to get versions)
	const fetchPrompts = useCallback(async () => {
		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/ai/prompts/`,
			type: 'GET',
			loader: false,
		});
		if (success && response) {
			const records = response.prompts?.records || response.prompts || [];
			if (response.stats) setStats(response.stats);

			// Now fetch detail for each prompt to get active_version + versions
			const detailed = await Promise.all(
				(Array.isArray(records) ? records : []).map(async (p) => {
					const { response: detailResp, success: detailOk } = await triggerApi({
						url: `/api/v1/apps/${appId}/ai/prompts/${p.id}/`,
						type: 'GET',
						loader: false,
					});
					if (detailOk && detailResp?.prompt) {
						return { ...p, ...detailResp.prompt };
					}
					return p;
				})
			);
			setPrompts(detailed);
		}
	}, [appId, triggerApi]);

	useEffect(() => {
		fetchPrompts();
	}, [appId]);

	// Create prompt
	const handleCreatePrompt = async (values, { resetForm, setSubmitting }) => {
		const { success } = await triggerApi({
			url: `/api/v1/apps/${appId}/ai/prompts/`,
			type: 'POST',
			loader: true,
			payload: {
				name: values.name,
				description: values.description,
				type: values.type,
				content: values.content,
				change_description: values.change_description || 'Initial version',
			},
		});
		setSubmitting(false);
		if (success) {
			setCreateModalOpen(false);
			resetForm();
			notify('success', 'Prompt Created', `${values.name} created with v1.`);
			fetchPrompts();
		}
	};

	// Edit prompt metadata
	const handleEditPrompt = async (values, { resetForm, setSubmitting }) => {
		if (!editingPrompt) return;
		const { success } = await triggerApi({
			url: `/api/v1/apps/${appId}/ai/prompts/${editingPrompt.id}/`,
			type: 'PUT',
			loader: true,
			payload: {
				name: values.name,
				description: values.description,
				type: values.type,
			},
		});
		setSubmitting(false);
		if (success) {
			setEditModalOpen(false);
			setEditingPrompt(null);
			resetForm();
			notify('success', 'Prompt Updated', `${values.name} updated.`);
			fetchPrompts();
		}
	};

	// Create new version
	const handleCreateVersion = async (values, { resetForm, setSubmitting }) => {
		if (!versionPrompt) return;
		const { success } = await triggerApi({
			url: `/api/v1/apps/${appId}/ai/prompts/${versionPrompt.id}/versions/`,
			type: 'POST',
			loader: true,
			payload: {
				content: values.content,
				change_description: values.change_description,
			},
		});
		setSubmitting(false);
		if (success) {
			setNewVersionModalOpen(false);
			setVersionPrompt(null);
			resetForm();
			notify('success', 'Version Created', 'New draft version created.');
			fetchPrompts();
		}
	};

	// Promote version
	const handlePromote = async (version) => {
		const prompt = prompts.find((p) => p.versions?.some((v) => v.id === version.id));
		if (!prompt) return;
		setPromotingId(version.id);
		const { success } = await triggerApi({
			url: `/api/v1/apps/${appId}/ai/prompts/${prompt.id}/versions/${version.id}/promote/`,
			type: 'POST',
			loader: false,
		});
		setPromotingId(null);
		if (success) {
			notify('success', 'Version Promoted', `v${version.version_number} is now active.`);
			fetchPrompts();
		}
	};

	// Delete prompt
	const handleDelete = (prompt) => {
		setConfirmModal({
			show: true,
			prompt,
			title: 'Delete Prompt',
			message: `Are you sure you want to delete "${prompt.name}"? ${
				prompt.total_versions > 0
					? 'This prompt has version history and will be deactivated.'
					: 'This action cannot be undone.'
			}`,
			confirmLabel: 'Delete',
			confirmColor: 'red',
		});
	};

	const confirmDelete = async () => {
		const prompt = confirmModal.prompt;
		setActionLoading(true);
		const { success } = await triggerApi({
			url: `/api/v1/apps/${appId}/ai/prompts/${prompt.id}/`,
			type: 'DELETE',
			loader: false,
		});
		setActionLoading(false);
		setConfirmModal({ show: false });
		if (success) {
			notify('success', 'Prompt Deleted', `${prompt.name} removed.`);
			fetchPrompts();
		}
	};

	const openEdit = (prompt) => {
		setEditingPrompt(prompt);
		setEditModalOpen(true);
	};

	const openNewVersion = (prompt) => {
		setVersionPrompt(prompt);
		setNewVersionModalOpen(true);
	};

	const createValidation = Yup.object({
		name: Yup.string()
			.matches(/^[a-z0-9-]+$/, 'Lowercase letters, numbers, and hyphens only')
			.required('Name is required'),
		type: Yup.string().oneOf(['system', 'user']).required('Type is required'),
		content: Yup.string().required('Prompt content is required'),
	});

	const editValidation = Yup.object({
		name: Yup.string().required('Name is required'),
		type: Yup.string().oneOf(['system', 'user']).required('Type is required'),
	});

	const versionValidation = Yup.object({
		content: Yup.string().required('Content is required'),
	});

	const editInitialValues = editingPrompt
		? { name: editingPrompt.name, description: editingPrompt.description || '', type: editingPrompt.type }
		: { name: '', description: '', type: 'system' };

	const versionInitialValues = {
		content: versionPrompt?.active_version?.content || '',
		change_description: '',
	};

	return (
		<div className="flex flex-col gap-[24px]">
			{/* Summary Card */}
			<div className="rounded-[16px] border border-[#E5E7EB] bg-white p-[24px]">
				<div className="mb-[16px] flex items-center justify-between">
					<div>
						<h2 className="font-source-sans-pro text-[18px] font-semibold text-[#111827]">
							Prompt Registry
						</h2>
						<p className="font-lato text-[14px] text-[#6B7280]">
							Versioned prompt templates with variable slots — code references by name, panel controls which version is live
						</p>
					</div>
					<button
						onClick={() => setCreateModalOpen(true)}
						className="flex items-center gap-[6px] rounded-[8px] bg-[#5048ED] px-[16px] py-[8px] font-lato text-[14px] font-medium text-white transition-colors hover:bg-[#4338CA]"
					>
						+ Create Prompt
					</button>
				</div>
				<div className="flex items-center gap-[16px]">
					<div className="flex items-center gap-[8px]">
						<span className="font-lato text-[14px] text-[#6B7280]">Total Prompts</span>
						<span className="font-lato text-[14px] font-semibold text-[#111827]">
							{stats.total_prompts ?? prompts.length}
						</span>
					</div>
					<div className="h-[16px] w-[1px] bg-[#E5E7EB]" />
					<div className="flex items-center gap-[8px]">
						<span className="font-lato text-[14px] text-[#6B7280]">Active Versions</span>
						<span className="font-lato text-[14px] font-semibold text-[#10B981]">
							{stats.active_versions ?? 0}
						</span>
					</div>
					<div className="h-[16px] w-[1px] bg-[#E5E7EB]" />
					<div className="flex items-center gap-[8px]">
						<span className="font-lato text-[14px] text-[#6B7280]">Total Versions</span>
						<span className="font-lato text-[14px] font-semibold text-[#111827]">
							{stats.total_versions ?? 0}
						</span>
					</div>
				</div>
			</div>

			{/* Table Header */}
			{prompts.length > 0 && (
				<div className="flex items-center px-[24px] py-[8px]">
					<span className="ml-[60px] min-w-[200px] font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
						Prompt Name
					</span>
					<div className="ml-auto flex items-center gap-[32px]">
						<span className="w-[80px] text-center font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Type</span>
						<span className="w-[100px] text-center font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Active Version</span>
						<span className="w-[100px] text-center font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Total Versions</span>
						<span className="w-[100px] text-center font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Last Modified</span>
					</div>
				</div>
			)}

			{/* Prompt List */}
			<div className="flex flex-col gap-[12px]">
				{prompts.length === 0 && (
					<div className="rounded-[8px] border border-dashed border-[#D1D5DB] bg-white px-[24px] py-[48px] text-center">
						<p className="font-lato text-[14px] text-[#9CA3AF]">
							No prompts created yet. Click "Create Prompt" to get started.
						</p>
					</div>
				)}
				{prompts.map((prompt) => (
					<PromptRow
						key={prompt.id}
						prompt={prompt}
						onEdit={openEdit}
						onNewVersion={openNewVersion}
						onPromote={handlePromote}
						onDelete={handleDelete}
						promotingId={promotingId}
					/>
				))}
			</div>

			{/* Create Prompt Modal */}
			<Formik
				initialValues={{ name: '', description: '', type: 'system', content: '', change_description: '' }}
				validationSchema={createValidation}
				onSubmit={handleCreatePrompt}
				enableReinitialize
			>
				{(formik) => (
					<Modal
						label="Create Prompt"
						show={createModalOpen}
						closeModal={() => { setCreateModalOpen(false); formik.resetForm(); }}
						ModalBody={
							<form onSubmit={formik.handleSubmit} className="flex grow flex-col gap-[20px] overflow-y-auto">
								<InputField label="Prompt Name" name="name" id="name" placeholder="e.g. assessment-question-system" />
								<InputField label="Description" name="description" id="description" placeholder="What this prompt does" />
								<div>
									<label className="font-lato text-[12px] font-semibold uppercase tracking-[0.6px] text-[#6C747D]">
										Type
									</label>
									<select
										name="type"
										value={formik.values.type}
										onChange={formik.handleChange}
										onBlur={formik.handleBlur}
										className="mt-[4px] w-full rounded-[8px] border border-[#DDE2E5] px-[12px] py-[10px] font-lato text-[14px] text-[#111827] outline-none focus:border-[#5048ED] focus:ring-1 focus:ring-[#5048ED]"
									>
										<option value="system">System</option>
										<option value="user">User</option>
									</select>
								</div>
								<div>
									<label className="font-lato text-[12px] font-semibold uppercase tracking-[0.6px] text-[#6C747D]">
										Prompt Content
									</label>
									<textarea
										name="content"
										value={formik.values.content}
										onChange={formik.handleChange}
										onBlur={formik.handleBlur}
										rows={8}
										placeholder={'Use {{variable_name}} for template variables'}
										className="mt-[4px] w-full rounded-[8px] border border-[#DDE2E5] px-[12px] py-[10px] font-mono text-[13px] text-[#111827] outline-none focus:border-[#5048ED] focus:ring-1 focus:ring-[#5048ED]"
									/>
									{formik.touched.content && formik.errors.content && (
										<p className="mt-[4px] font-lato text-[12px] text-[#EF4444]">{formik.errors.content}</p>
									)}
								</div>
								<InputField label="Version Note" name="change_description" id="change_description" placeholder="e.g. Initial version" />
								<div className="flex justify-end gap-[12px] pt-[8px]">
									<button
										type="submit"
										disabled={formik.isSubmitting || !formik.isValid}
										className="rounded-[8px] bg-[#5048ED] px-[24px] py-[10px] font-lato text-[14px] font-medium text-white transition-colors hover:bg-[#4338CA] disabled:pointer-events-none disabled:opacity-50"
									>
										{formik.isSubmitting ? 'Creating...' : 'Create Prompt'}
									</button>
								</div>
							</form>
						}
					/>
				)}
			</Formik>

			{/* Edit Prompt Modal */}
			<Formik
				initialValues={editInitialValues}
				validationSchema={editValidation}
				onSubmit={handleEditPrompt}
				enableReinitialize
			>
				{(formik) => (
					<Modal
						label={`Edit Prompt — ${editingPrompt?.name || ''}`}
						show={editModalOpen}
						closeModal={() => { setEditModalOpen(false); setEditingPrompt(null); formik.resetForm(); }}
						ModalBody={
							<form onSubmit={formik.handleSubmit} className="flex grow flex-col gap-[20px] overflow-y-auto">
								<InputField label="Prompt Name" name="name" id="name" />
								<InputField label="Description" name="description" id="description" />
								<div>
									<label className="font-lato text-[12px] font-semibold uppercase tracking-[0.6px] text-[#6C747D]">Type</label>
									<select
										name="type"
										value={formik.values.type}
										onChange={formik.handleChange}
										className="mt-[4px] w-full rounded-[8px] border border-[#DDE2E5] px-[12px] py-[10px] font-lato text-[14px] text-[#111827] outline-none focus:border-[#5048ED]"
									>
										<option value="system">System</option>
										<option value="user">User</option>
									</select>
								</div>
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
						}
					/>
				)}
			</Formik>

			{/* New Version Modal */}
			<Formik
				initialValues={versionInitialValues}
				validationSchema={versionValidation}
				onSubmit={handleCreateVersion}
				enableReinitialize
			>
				{(formik) => (
					<Modal
						label={`New Version — ${versionPrompt?.name || ''}`}
						show={newVersionModalOpen}
						closeModal={() => { setNewVersionModalOpen(false); setVersionPrompt(null); formik.resetForm(); }}
						ModalBody={
							<form onSubmit={formik.handleSubmit} className="flex grow flex-col gap-[20px] overflow-y-auto">
								<div>
									<label className="font-lato text-[12px] font-semibold uppercase tracking-[0.6px] text-[#6C747D]">
										Prompt Content
									</label>
									<textarea
										name="content"
										value={formik.values.content}
										onChange={formik.handleChange}
										onBlur={formik.handleBlur}
										rows={10}
										placeholder={'Use {{variable_name}} for template variables'}
										className="mt-[4px] w-full rounded-[8px] border border-[#DDE2E5] px-[12px] py-[10px] font-mono text-[13px] text-[#111827] outline-none focus:border-[#5048ED] focus:ring-1 focus:ring-[#5048ED]"
									/>
									{formik.touched.content && formik.errors.content && (
										<p className="mt-[4px] font-lato text-[12px] text-[#EF4444]">{formik.errors.content}</p>
									)}
								</div>
								<InputField label="What changed?" name="change_description" id="change_description" placeholder="e.g. Added pharmacovigilance topic weighting" />
								<p className="font-lato text-[12px] text-[#9CA3AF]">
									New versions are created as drafts. Use "Promote" to make a version active.
								</p>
								<div className="flex justify-end gap-[12px] pt-[8px]">
									<button
										type="submit"
										disabled={formik.isSubmitting || !formik.isValid}
										className="rounded-[8px] bg-[#5048ED] px-[24px] py-[10px] font-lato text-[14px] font-medium text-white transition-colors hover:bg-[#4338CA] disabled:pointer-events-none disabled:opacity-50"
									>
										{formik.isSubmitting ? 'Creating...' : 'Create Version'}
									</button>
								</div>
							</form>
						}
					/>
				)}
			</Formik>

			{/* Confirmation Modal */}
			<ConfirmationModal
				show={confirmModal.show}
				onClose={() => setConfirmModal({ show: false })}
				onConfirm={confirmDelete}
				title={confirmModal.title}
				message={confirmModal.message}
				confirmLabel={confirmModal.confirmLabel}
				confirmColor={confirmModal.confirmColor}
				loading={actionLoading}
			/>
		</div>
	);
}
