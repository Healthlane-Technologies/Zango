import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { Formik } from 'formik';
import * as Yup from 'yup';
import toast from 'react-hot-toast';
import useApi from '../../../hooks/useApi';
import Modal from '../../../components/Modal';
import InputField from '../../../components/Form/InputField.jsx';
import Toast from '../../../components/Notifications/Toast';

/* ─────────────────────────── helpers ─────────────────────────── */

function notify(type, title, description) {
	toast.custom(
		(t) => <Toast type={type} toastRef={t} title={title} description={description} />,
		{ duration: 5000, position: 'bottom-left' }
	);
}

function extractVariables(content = '') {
	const matches = content.match(/\{\{(\w+)\}\}/g) || [];
	return [...new Set(matches.map((m) => m.slice(2, -2)))];
}

/**
 * Word-level diff using LCS. Falls back to line-level for very long texts.
 * Returns [{type: 'equal'|'removed'|'added', value: string}]
 */
function diffWords(a = '', b = '') {
	const useLine = a.length > 3000 || b.length > 3000;
	const ta = useLine ? a.split('\n').flatMap((l, i, arr) => i < arr.length - 1 ? [l, '\n'] : [l]) : a.split(/(\s+)/);
	const tb = useLine ? b.split('\n').flatMap((l, i, arr) => i < arr.length - 1 ? [l, '\n'] : [l]) : b.split(/(\s+)/);
	const m = ta.length, n = tb.length;
	const dp = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
	for (let i = 1; i <= m; i++)
		for (let j = 1; j <= n; j++)
			dp[i][j] = ta[i - 1] === tb[j - 1] ? dp[i - 1][j - 1] + 1 : Math.max(dp[i - 1][j], dp[i][j - 1]);
	const result = [];
	let i = m, j = n;
	while (i > 0 || j > 0) {
		if (i > 0 && j > 0 && ta[i - 1] === tb[j - 1]) {
			result.unshift({ type: 'equal', value: ta[i - 1] }); i--; j--;
		} else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
			result.unshift({ type: 'added', value: tb[j - 1] }); j--;
		} else {
			result.unshift({ type: 'removed', value: ta[i - 1] }); i--;
		}
	}
	return result;
}

function formatDate(dateStr) {
	if (!dateStr) return '—';
	return new Date(dateStr).toLocaleDateString('en-US', {
		month: 'short',
		day: 'numeric',
		year: 'numeric',
	});
}

/* ─────────────────────────── small UI atoms ─────────────────────────── */

function StatusBadge({ status }) {
	const map = {
		active: 'bg-[#ECFDF5] text-[#10B981]',
		draft: 'bg-[#FEF3C7] text-[#D97706]',
		inactive: 'bg-[#F3F4F6] text-[#6B7280]',
	};
	return (
		<span
			className={`inline-flex items-center gap-[4px] rounded-[4px] px-[8px] py-[2px] font-lato text-[12px] font-medium ${map[status] || map.inactive}`}
		>
			{status === 'active' && (
				<span className="inline-block h-[6px] w-[6px] rounded-full bg-[#10B981]" />
			)}
			{status.charAt(0).toUpperCase() + status.slice(1)}
		</span>
	);
}

function TypeBadge({ type }) {
	return (
		<span
			className={`rounded-[4px] px-[10px] py-[3px] font-lato text-[12px] font-medium ${
				type === 'system'
					? 'bg-[#EFF6FF] text-[#346BD4]'
					: 'bg-[#F3E8FF] text-[#7C3AED]'
			}`}
		>
			{type === 'system' ? 'System' : 'User'}
		</span>
	);
}

function VariableChip({ name }) {
	return (
		<span className="inline-flex items-center gap-[4px] rounded-[4px] bg-[#FFFBEB] px-[10px] py-[3px] font-mono text-[12px] text-[#92400E] border border-[#FDE68A]">
			<svg width="10" height="10" viewBox="0 0 10 10" fill="none">
				<path d="M3 2L1 5L3 8M7 2L9 5L7 8" stroke="#D97706" strokeWidth="1.2" strokeLinecap="round"/>
			</svg>
			{`{{${name}}}`}
		</span>
	);
}

/* ─── live-highlighted textarea content ─── */
function HighlightedContent({ content }) {
	if (!content) return <span className="text-[#6B7280] italic">No content</span>;
	const parts = content.split(/(\{\{\w+\}\})/g);
	return (
		<pre className="whitespace-pre-wrap break-words font-mono text-[13px] leading-[22px]">
			{parts.map((part, i) =>
				/^\{\{\w+\}\}$/.test(part) ? (
					<span key={i} className="text-[#F59E0B] bg-[#FFFBEB] bg-opacity-20 rounded-[2px] px-[1px]">
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

/* ─── Prompt content textarea with live variable preview ─── */
function PromptContentEditor({ value, onChange, onBlur, placeholder, rows = 10, error }) {
	const variables = extractVariables(value);

	return (
		<div className="flex flex-col gap-[8px]">
			<div className="relative">
				<textarea
					value={value}
					onChange={onChange}
					onBlur={onBlur}
					rows={rows}
					placeholder={placeholder || 'Use {{variable_name}} for template variables'}
					className={`w-full rounded-[8px] border px-[14px] py-[12px] font-mono text-[13px] leading-[22px] text-[#111827] outline-none transition-colors resize-y ${
						error
							? 'border-[#EF4444] focus:border-[#EF4444] focus:ring-1 focus:ring-[#EF4444]'
							: 'border-[#DDE2E5] focus:border-[#5048ED] focus:ring-1 focus:ring-[#5048ED]'
					}`}
				/>
			</div>
			{variables.length > 0 && (
				<div className="flex flex-wrap items-center gap-[6px]">
					<span className="font-lato text-[11px] font-semibold uppercase tracking-[0.5px] text-[#9CA3AF]">
						Detected:
					</span>
					{variables.map((v) => (
						<VariableChip key={v} name={v} />
					))}
				</div>
			)}
			{error && <p className="font-lato text-[12px] text-[#EF4444]">{error}</p>}
		</div>
	);
}

/* ─── Deactivate confirmation dialog ─── */
function DeactivateModal({ show, onClose, onConfirm, prompt, loading }) {
	if (!show || !prompt) return null;
	const hasVersions = (prompt.versions || []).length > 0 || prompt.total_versions > 0;
	const usedByAgents = prompt.used_by_agents || [];

	return (
		<div className="fixed inset-0 z-50 flex items-center justify-center">
			<div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={!loading ? onClose : undefined} />
			<div className="relative w-full max-w-[440px] rounded-[16px] bg-white p-[28px] shadow-2xl">
				{/* Icon */}
				<div className="mb-[16px] flex h-[44px] w-[44px] items-center justify-center rounded-full bg-[#FEF2F2]">
					<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
						<path d="M10 6V10M10 14H10.01M19 10C19 14.9706 14.9706 19 10 19C5.02944 19 1 14.9706 1 10C1 5.02944 5.02944 1 10 1C14.9706 1 19 5.02944 19 10Z" stroke="#EF4444" strokeWidth="1.8" strokeLinecap="round"/>
					</svg>
				</div>
				<h3 className="mb-[8px] font-source-sans-pro text-[18px] font-semibold text-[#111827]">
					{hasVersions ? 'Deactivate' : 'Delete'} Prompt
				</h3>
				<p className="mb-[16px] font-lato text-[14px] leading-[22px] text-[#6B7280]">
					{hasVersions
						? <>Deactivate <span className="font-semibold text-[#111827]">&ldquo;{prompt.name}&rdquo;</span>? It will be removed from the registry and agent dropdowns. Version history is preserved.</>
						: <>Permanently delete <span className="font-semibold text-[#111827]">&ldquo;{prompt.name}&rdquo;</span>? This prompt has no version history and cannot be recovered.</>
					}
				</p>
				<div className="flex justify-end gap-[10px]">
					<button
						onClick={onClose}
						disabled={loading}
						className="rounded-[8px] border border-[#DDE2E5] px-[20px] py-[10px] font-lato text-[14px] font-medium text-[#111827] hover:bg-[#F9FAFB] disabled:opacity-50"
					>
						Cancel
					</button>
					<button
						onClick={onConfirm}
						disabled={loading}
						className="flex items-center gap-[6px] rounded-[8px] bg-[#EF4444] px-[20px] py-[10px] font-lato text-[14px] font-medium text-white hover:bg-[#DC2626] disabled:opacity-50 transition-colors"
					>
						{loading ? (
							<><svg className="animate-spin" width="13" height="13" viewBox="0 0 13 13" fill="none"><path d="M6.5 1.5A5 5 0 1 0 11.5 6.5" stroke="white" strokeWidth="1.5" strokeLinecap="round"/></svg>Processing…</>
						) : (
							hasVersions ? 'Deactivate' : 'Delete'
						)}
					</button>
				</div>
			</div>
		</div>
	);
}

/* ─── Dependency block dialog — shown when backend returns 409 PROMPT_IN_USE ─── */
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
					Cannot Deactivate Prompt
				</h3>
				<p className="mb-[6px] font-lato text-[14px] leading-[22px] text-[#6B7280]">
					<span className="font-semibold text-[#111827]">&ldquo;{entityName}&rdquo;</span> is actively used by{' '}
					<span className="font-semibold text-[#D97706]">{agentCount} agent{agentCount !== 1 ? 's' : ''}</span>.
					Unlink or disable the following agents before deactivating:
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

/* ─────────────────────────── Version History Panel ─────────────────────────── */

function VersionTimeline({ versions, onPromote, promotingId, readOnly }) {
	return (
		<div className="flex flex-col">
			<h4 className="mb-[14px] font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
				Version History
			</h4>
			<div className="relative flex flex-col gap-0">
				{/* Vertical line */}
				<div className="absolute left-[9px] top-[10px] bottom-[10px] w-[1px] bg-[#E5E7EB]" />

				{versions.map((v, idx) => {
					const isActive = v.status === 'active';
					const isPromoting = promotingId === v.id;
					const isFirst = idx === 0;

					return (
						<div key={v.id} className="relative flex items-start gap-[14px] pb-[16px] last:pb-0">
							{/* Dot */}
							<div
								className={`relative z-10 mt-[2px] flex h-[20px] w-[20px] flex-shrink-0 items-center justify-center rounded-full border-[2px] ${
									isActive
										? 'border-[#10B981] bg-[#10B981]'
										: isFirst
										? 'border-[#5048ED] bg-white'
										: 'border-[#D1D5DB] bg-white'
								}`}
							>
								{isActive && (
									<svg width="10" height="8" viewBox="0 0 10 8" fill="none">
										<path d="M1 4L3.5 6.5L9 1" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
									</svg>
								)}
							</div>

							{/* Content */}
							<div className="flex-1 min-w-0">
								<div className="flex items-center gap-[8px] mb-[2px]">
									<span className="font-lato text-[14px] font-semibold text-[#111827]">
										v{v.version_number}
									</span>
									<StatusBadge status={v.status} />
									{isFirst && !isActive && (
										<span className="font-lato text-[10px] font-medium text-[#5048ED] bg-[#EEF2FF] rounded-[3px] px-[5px] py-[1px]">
											Latest
										</span>
									)}
								</div>
								{v.change_description && (
									<p className="font-lato text-[13px] text-[#374151] leading-[18px] mb-[2px]">
										{v.change_description}
									</p>
								)}
								<p className="font-lato text-[11px] text-[#9CA3AF]">
									{formatDate(v.created_at)}
									{v.created_by ? ` · ${v.created_by}` : ''}
								</p>
								{!isActive && !readOnly && (
									<button
										onClick={() => onPromote(v)}
										disabled={isPromoting}
										className="mt-[6px] flex items-center gap-[4px] rounded-[5px] border border-[#10B981] px-[10px] py-[3px] font-lato text-[12px] font-medium text-[#10B981] hover:bg-[#ECFDF5] disabled:opacity-50 transition-colors"
									>
										{isPromoting ? (
											<>
												<svg className="animate-spin" width="10" height="10" viewBox="0 0 10 10" fill="none">
													<path d="M5 1.5A3.5 3.5 0 1 0 8.5 5" stroke="#10B981" strokeWidth="1.5" strokeLinecap="round"/>
												</svg>
												Promoting…
											</>
										) : (
											<>
												<svg width="10" height="10" viewBox="0 0 10 10" fill="none">
													<path d="M5 8.5V1.5M2 4.5L5 1.5L8 4.5" stroke="#10B981" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
												</svg>
												Make Active
											</>
										)}
									</button>
								)}
							</div>
						</div>
					);
				})}
			</div>
		</div>
	);
}

/* ─────────────────────────── Diff Panel ─────────────────────────── */

function DiffPanel({ promptId, versions }) {
	const { appId } = useParams();
	const triggerApi = useApi();
	const [v1, setV1] = useState('');
	const [v2, setV2] = useState('');
	const [chunks, setChunks] = useState(null);
	const [meta, setMeta] = useState(null);
	const [loading, setLoading] = useState(false);

	const canCompare = v1 && v2 && v1 !== v2;

	const handleCompare = async () => {
		if (!canCompare) return;
		setLoading(true);
		setChunks(null);
		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/ai/prompts/${promptId}/compare/?v1=${v1}&v2=${v2}`,
			type: 'GET',
			loader: false,
			showErrorModal: false,
		});
		setLoading(false);
		if (success) {
			setMeta({ v1: response.version_1, v2: response.version_2 });
			setChunks(diffWords(response.version_1.content, response.version_2.content));
		} else {
			notify('error', 'Compare Failed', response?.message || 'Could not compare versions');
		}
	};

	const addedCount = chunks ? chunks.filter((c) => c.type === 'added').length : 0;
	const removedCount = chunks ? chunks.filter((c) => c.type === 'removed').length : 0;

	return (
		<div className="rounded-[8px] border border-[#E5E7EB] bg-[#F9FAFB] p-[16px]">
			{/* Header */}
			<div className="flex items-center gap-[10px] mb-[14px]">
				<svg width="14" height="14" viewBox="0 0 14 14" fill="none">
					<path d="M1 7h5M8 7h5M3.5 4L1 7l2.5 3M10.5 4L13 7l-2.5 3" stroke="#6B7280" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
				</svg>
				<span className="font-lato text-[12px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
					Compare Versions
				</span>
			</div>

			{/* Version selectors */}
			<div className="flex items-center gap-[8px]">
				<select
					value={v1}
					onChange={(e) => { setV1(e.target.value); setChunks(null); }}
					className="flex-1 rounded-[6px] border border-[#DDE2E5] px-[10px] py-[6px] font-lato text-[13px] text-[#111827] outline-none focus:border-[#5048ED]"
				>
					<option value="">Base…</option>
					{versions.map((v) => (
						<option key={v.id} value={v.version_number}>
							v{v.version_number} {v.status === 'active' ? '(active)' : ''}
						</option>
					))}
				</select>
				<svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="flex-shrink-0 text-[#9CA3AF]">
					<path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
				</svg>
				<select
					value={v2}
					onChange={(e) => { setV2(e.target.value); setChunks(null); }}
					className="flex-1 rounded-[6px] border border-[#DDE2E5] px-[10px] py-[6px] font-lato text-[13px] text-[#111827] outline-none focus:border-[#5048ED]"
				>
					<option value="">Compare…</option>
					{versions.map((v) => (
						<option key={v.id} value={v.version_number}>
							v{v.version_number} {v.status === 'active' ? '(active)' : ''}
						</option>
					))}
				</select>
				<button
					onClick={handleCompare}
					disabled={!canCompare || loading}
					className="flex-shrink-0 flex items-center gap-[5px] rounded-[6px] bg-[#5048ED] px-[14px] py-[6px] font-lato text-[12px] font-medium text-white hover:bg-[#4338CA] disabled:opacity-40 transition-colors"
				>
					{loading ? (
						<svg className="animate-spin" width="11" height="11" viewBox="0 0 11 11" fill="none">
							<path d="M5.5 1.5A4 4 0 1 0 9.5 5.5" stroke="white" strokeWidth="1.5" strokeLinecap="round"/>
						</svg>
					) : (
						<>
							<svg width="11" height="11" viewBox="0 0 11 11" fill="none">
								<circle cx="5.5" cy="5.5" r="4.5" stroke="white" strokeWidth="1.2"/>
								<path d="M3.5 5.5h4M5.5 3.5v4" stroke="white" strokeWidth="1.2" strokeLinecap="round"/>
							</svg>
							Diff
						</>
					)}
				</button>
			</div>

			{/* Diff result */}
			{chunks && meta && (
				<div className="mt-[14px]">
					{/* Summary bar */}
					<div className="flex items-center gap-[10px] mb-[10px]">
						<span className="font-lato text-[11px] font-semibold text-[#6B7280]">
							v{meta.v1.version_number} → v{meta.v2.version_number}
						</span>
						<span className="inline-flex items-center gap-[3px] rounded-[4px] bg-[#DCFCE7] px-[7px] py-[2px] font-mono text-[11px] font-semibold text-[#166534]">
							+{addedCount}
						</span>
						<span className="inline-flex items-center gap-[3px] rounded-[4px] bg-[#FEE2E2] px-[7px] py-[2px] font-mono text-[11px] font-semibold text-[#991B1B]">
							−{removedCount}
						</span>
						{addedCount === 0 && removedCount === 0 && (
							<span className="font-lato text-[11px] text-[#9CA3AF] italic">Identical</span>
						)}
					</div>

					{/* Unified diff view */}
					<div className="rounded-[8px] bg-[#1F2937] p-[14px] max-h-[420px] overflow-y-auto">
						<pre className="whitespace-pre-wrap break-words font-mono text-[13px] leading-[22px]">
							{chunks.map((chunk, i) => {
								if (chunk.type === 'equal') {
									return (
										<span key={i} className="text-[#E5E7EB]">{chunk.value}</span>
									);
								}
								if (chunk.type === 'removed') {
									return (
										<span key={i} className="rounded-[2px] bg-red-900/50 text-red-300 line-through">{chunk.value}</span>
									);
								}
								return (
									<span key={i} className="rounded-[2px] bg-green-900/50 text-green-300">{chunk.value}</span>
								);
							})}
						</pre>
					</div>
				</div>
			)}
		</div>
	);
}

/* ─────────────────────────── Live Inline Diff Preview ─────────────────────────── */

function LiveDiffPreview({ baseContent, newContent }) {
	const chunks = diffWords(baseContent || '', newContent || '');
	const addedCount = chunks.filter((c) => c.type === 'added').length;
	const removedCount = chunks.filter((c) => c.type === 'removed').length;
	const isIdentical = addedCount === 0 && removedCount === 0;

	return (
		<div className="flex flex-col gap-[8px]">
			<div className="flex items-center gap-[8px]">
				<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
					Live Diff
				</span>
				{isIdentical ? (
					<span className="font-lato text-[11px] text-[#9CA3AF] italic">No changes yet</span>
				) : (
					<>
						<span className="inline-flex items-center gap-[3px] rounded-[4px] bg-[#DCFCE7] px-[6px] py-[1px] font-mono text-[11px] font-semibold text-[#166534]">
							+{addedCount}
						</span>
						<span className="inline-flex items-center gap-[3px] rounded-[4px] bg-[#FEE2E2] px-[6px] py-[1px] font-mono text-[11px] font-semibold text-[#991B1B]">
							−{removedCount}
						</span>
					</>
				)}
			</div>
			<div className="rounded-[8px] bg-[#1F2937] p-[14px] min-h-[200px] max-h-[420px] overflow-y-auto">
				<pre className="whitespace-pre-wrap break-words font-mono text-[13px] leading-[22px]">
					{isIdentical ? (
						<span className="text-[#6B7280] italic">Start editing to see changes highlighted here…</span>
					) : (
						chunks.map((chunk, i) => {
							if (chunk.type === 'equal') return <span key={i} className="text-[#E5E7EB]">{chunk.value}</span>;
							if (chunk.type === 'removed') return <span key={i} className="rounded-[2px] bg-red-900/50 text-red-300 line-through">{chunk.value}</span>;
							return <span key={i} className="rounded-[2px] bg-green-900/50 text-green-300">{chunk.value}</span>;
						})
					)}
				</pre>
			</div>
		</div>
	);
}

/* ─────────────────────────── Prompt Row ─────────────────────────── */

function PromptRow({ prompt, onEdit, onNewVersion, onPromote, onDeactivate, onActivate, promotingId }) {
	const [expanded, setExpanded] = useState(false);
	const activeVersion = prompt.active_version;
	const versions = prompt.versions || [];
	const variables = extractVariables(activeVersion?.content);
	const usedByAgents = prompt.used_by_agents || [];
	const isInactive = prompt.is_active === false;

	return (
		<div className={`rounded-[10px] border bg-white transition-shadow ${isInactive ? 'bg-[#FAFAFA]' : ''} ${expanded ? 'border-[#C7D2FE] shadow-[0_0_0_3px_rgba(80,72,237,0.06)]' : isInactive ? 'border-[#E5E7EB]' : 'border-[#E5E7EB] hover:border-[#C7D2FE] hover:shadow-sm'}`}>
			{/* ── collapsed header ── */}
			<div
				className="flex items-center gap-[14px] px-[20px] py-[14px] cursor-pointer select-none"
				onClick={() => setExpanded(!expanded)}
			>
				{/* Chevron */}
				<svg
					width="12" height="12" viewBox="0 0 12 12" fill="none"
					className={`flex-shrink-0 text-[#9CA3AF] transition-transform duration-200 ${expanded ? 'rotate-90' : ''}`}
				>
					<path d="M4.5 2L8.5 6L4.5 10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
				</svg>

				{/* Icon */}
				<div className="flex h-[36px] w-[36px] flex-shrink-0 items-center justify-center rounded-[8px] bg-[#FEF3C7]">
					<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
						<path d="M3 2.5h10v9H8.5L6 14V11.5H3V2.5Z" stroke="#D97706" strokeWidth="1.2" strokeLinejoin="round"/>
						<path d="M5.5 5.5h5M5.5 7.5h3" stroke="#D97706" strokeWidth="1" strokeLinecap="round"/>
					</svg>
				</div>

				{/* Name + description */}
				<div className="flex-1 min-w-0">
					<div className="flex items-center gap-[8px] flex-wrap">
						<span className="font-source-sans-pro text-[15px] font-semibold text-[#111827]">
							{prompt.name}
						</span>
						<TypeBadge type={prompt.type} />
						{isInactive && (
							<span className="inline-flex items-center gap-[4px] rounded-[4px] border border-[#E5E7EB] bg-[#F3F4F6] px-[8px] py-[2px] font-lato text-[11px] font-medium text-[#6B7280]">
								<svg width="8" height="8" viewBox="0 0 8 8" fill="none"><circle cx="4" cy="4" r="3" stroke="#9CA3AF" strokeWidth="1"/><path d="M2 2L6 6M6 2L2 6" stroke="#9CA3AF" strokeWidth="1" strokeLinecap="round"/></svg>
								Deactivated
							</span>
						)}
						{!isInactive && usedByAgents.length > 0 && (
							<span className="inline-flex items-center gap-[4px] rounded-[4px] bg-[#F0FDF4] px-[8px] py-[2px] font-lato text-[11px] text-[#059669]">
								<svg width="10" height="10" viewBox="0 0 10 10" fill="none">
									<circle cx="5" cy="3.5" r="1.5" stroke="#059669" strokeWidth="1"/>
									<path d="M1.5 8.5C1.5 7 3 6 5 6s3.5 1 3.5 2.5" stroke="#059669" strokeWidth="1" strokeLinecap="round"/>
								</svg>
								{usedByAgents.length} agent{usedByAgents.length > 1 ? 's' : ''}
							</span>
						)}
					</div>
					{prompt.description && (
						<p className="mt-[2px] font-lato text-[13px] text-[#6B7280] truncate">
							{prompt.description}
						</p>
					)}
				</div>

				{/* Metadata cells */}
				<div className="flex items-center gap-[28px] flex-shrink-0 ml-[8px]">
					<div className="text-center hidden md:block">
						<p className="font-lato text-[10px] font-bold uppercase tracking-[0.5px] text-[#9CA3AF]">Active</p>
						<p className="mt-[2px] font-lato text-[14px] font-semibold text-[#111827]">
							{prompt.active_version_number ? `v${prompt.active_version_number}` : <span className="text-[#D97706]">None</span>}
						</p>
					</div>
					<div className="text-center hidden md:block">
						<p className="font-lato text-[10px] font-bold uppercase tracking-[0.5px] text-[#9CA3AF]">Versions</p>
						<p className="mt-[2px] font-lato text-[14px] text-[#111827]">{prompt.total_versions || versions.length || 0}</p>
					</div>
					<div className="text-center hidden lg:block">
						<p className="font-lato text-[10px] font-bold uppercase tracking-[0.5px] text-[#9CA3AF]">Modified</p>
						<p className="mt-[2px] font-lato text-[12px] text-[#6B7280]">{formatDate(prompt.modified_at)}</p>
					</div>

					{/* Quick actions */}
					{isInactive ? (
						<div className="flex items-center gap-[4px]" onClick={(e) => e.stopPropagation()}>
							<button
								onClick={() => onActivate(prompt)}
								title="Activate"
								className="flex h-[30px] items-center gap-[4px] rounded-[6px] px-[8px] text-[#059669] hover:bg-[#F0FDF4] transition-colors font-lato text-[12px]"
							>
								<svg width="13" height="13" viewBox="0 0 13 13" fill="none">
									<circle cx="6.5" cy="6.5" r="5.5" stroke="currentColor" strokeWidth="1.2"/>
									<path d="M4.5 6.5l1.5 1.5 3-3" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
								</svg>
								Activate
							</button>
						</div>
					) : (
					<div className="flex items-center gap-[4px]" onClick={(e) => e.stopPropagation()}>
							<button
								onClick={() => onNewVersion(prompt)}
								title="New Version"
								className="flex h-[30px] w-[30px] items-center justify-center rounded-[6px] text-[#5048ED] hover:bg-[#EEF2FF] transition-colors"
							>
								<svg width="14" height="14" viewBox="0 0 14 14" fill="none">
									<path d="M7 2.5V11.5M2.5 7H11.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
								</svg>
							</button>
							<button
								onClick={() => onEdit(prompt)}
								title="Edit Metadata"
								className="flex h-[30px] w-[30px] items-center justify-center rounded-[6px] text-[#6B7280] hover:bg-[#F3F4F6] hover:text-[#111827] transition-colors"
							>
								<svg width="14" height="14" viewBox="0 0 14 14" fill="none">
									<path d="M9.5 2L12 4.5L4.5 12H2V9.5L9.5 2Z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round"/>
								</svg>
							</button>
							<button
								onClick={() => onDeactivate(prompt)}
								title="Deactivate"
								className="flex h-[30px] items-center gap-[4px] rounded-[6px] px-[8px] text-[#6B7280] hover:bg-[#FEF2F2] hover:text-[#EF4444] transition-colors font-lato text-[12px]"
							>
								<svg width="13" height="13" viewBox="0 0 13 13" fill="none">
									<circle cx="6.5" cy="6.5" r="5.5" stroke="currentColor" strokeWidth="1.2"/>
									<path d="M4.5 6.5h4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
								</svg>
								Deactivate
							</button>
						</div>
					)}
				</div>
			</div>


			{/* ── expanded detail ── */}
			{expanded && (
				<div className="border-t border-[#E5E7EB]">
					{isInactive ? (
						/* ── Deactivated view — read-only, activate CTA ── */
						<div className="grid grid-cols-[1fr_300px] divide-x divide-[#E5E7EB]">
							{/* Left — archived content (read-only) */}
							<div className="p-[24px] flex flex-col gap-[16px] overflow-y-auto max-h-[600px]">
								{/* Archived banner */}
								<div className="flex items-center justify-between rounded-[8px] border border-[#FDE68A] bg-[#FFFBEB] px-[16px] py-[12px]">
									<div className="flex items-center gap-[10px]">
										<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
											<path d="M2 4.5h12v9H2V4.5Z" stroke="#D97706" strokeWidth="1.2" strokeLinejoin="round"/>
											<path d="M1 2.5h14v2H1V2.5Z" fill="#FDE68A" stroke="#D97706" strokeWidth="1.2" strokeLinejoin="round"/>
											<path d="M6.5 7.5h3" stroke="#D97706" strokeWidth="1.2" strokeLinecap="round"/>
										</svg>
										<span className="font-lato text-[13px] font-medium text-[#92400E]">
											This prompt is archived. Content and versions are read-only.
										</span>
									</div>
									<button
										onClick={() => onActivate(prompt)}
										className="flex-shrink-0 flex items-center gap-[5px] rounded-[6px] bg-[#059669] px-[12px] py-[5px] font-lato text-[12px] font-medium text-white hover:bg-[#047857] transition-colors"
									>
										<svg width="10" height="10" viewBox="0 0 10 10" fill="none">
											<circle cx="5" cy="5" r="4" stroke="white" strokeWidth="1.2"/>
											<path d="M3 5l1.5 1.5 3-3" stroke="white" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
										</svg>
										Activate Prompt
									</button>
								</div>

								{/* Last active content (read-only preview) */}
								<div>
									<h4 className="mb-[10px] font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
										Last Active Content
										{activeVersion && (
											<span className="ml-[8px] font-lato text-[11px] normal-case tracking-normal font-normal text-[#9CA3AF]">
												v{activeVersion.version_number}
											</span>
										)}
									</h4>
									{activeVersion ? (
										<div className="rounded-[8px] bg-[#1F2937] p-[18px] max-h-[300px] overflow-y-auto opacity-75">
											<HighlightedContent content={activeVersion.content} />
										</div>
									) : (
										<p className="font-lato text-[13px] text-[#9CA3AF]">No active version was set.</p>
									)}
								</div>

								{/* Variables (read-only) */}
								{variables.length > 0 && (
									<div>
										<p className="mb-[8px] font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Template Variables</p>
										<div className="flex flex-wrap gap-[6px]">
											{variables.map((v) => <VariableChip key={v} name={v} />)}
										</div>
									</div>
								)}
							</div>

							{/* Right — version history (read-only, no promote buttons) */}
							<div className="p-[24px] bg-[#FAFAFA] overflow-y-auto max-h-[600px]">
								{versions.length > 0 ? (
									<VersionTimeline
										versions={versions}
										onPromote={onPromote}
										promotingId={promotingId}
										readOnly
									/>
								) : (
									<p className="font-lato text-[13px] text-[#9CA3AF]">No versions yet.</p>
								)}
							</div>
						</div>
					) : (
					<div className="grid grid-cols-[1fr_300px] divide-x divide-[#E5E7EB]">
						{/* Left — active content + diff */}
						<div className="p-[24px] flex flex-col gap-[16px] overflow-y-auto max-h-[600px]">
							<div>
								<div className="flex items-center justify-between mb-[12px]">
									<h4 className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
										Active Content
										{activeVersion && (
											<span className="ml-[8px] font-lato text-[11px] normal-case tracking-normal font-normal text-[#9CA3AF]">
												v{activeVersion.version_number}
											</span>
										)}
									</h4>
									<button
										onClick={() => onNewVersion(prompt)}
										className="flex items-center gap-[5px] rounded-[6px] bg-[#5048ED] px-[12px] py-[5px] font-lato text-[12px] font-medium text-white hover:bg-[#4338CA] transition-colors"
									>
										<svg width="10" height="10" viewBox="0 0 10 10" fill="none">
											<path d="M5 1.5V8.5M1.5 5H8.5" stroke="white" strokeWidth="1.4" strokeLinecap="round"/>
										</svg>
										New Version
									</button>
								</div>

								{activeVersion ? (
									<div className="rounded-[8px] bg-[#1F2937] p-[18px] max-h-[340px] overflow-y-auto">
										<HighlightedContent content={activeVersion.content} />
									</div>
								) : (
									<div className="flex flex-col items-center justify-center gap-[8px] rounded-[8px] border border-dashed border-[#E5E7EB] bg-[#F9FAFB] py-[32px]">
										<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
											<path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="#D1D5DB" strokeWidth="1.5"/>
											<path d="M12 8V12M12 16H12.01" stroke="#D1D5DB" strokeWidth="1.5" strokeLinecap="round"/>
										</svg>
										<p className="font-lato text-[13px] text-[#9CA3AF]">No active version — promote a version to make it live</p>
									</div>
								)}
							</div>

							{/* Variables */}
							{variables.length > 0 && (
								<div>
									<p className="mb-[8px] font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
										Template Variables
									</p>
									<div className="flex flex-wrap gap-[6px]">
										{variables.map((v) => <VariableChip key={v} name={v} />)}
									</div>
								</div>
							)}

							{/* Used by agents */}
							{usedByAgents.length > 0 && (
								<div>
									<p className="mb-[8px] font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
										Used By
									</p>
									<div className="flex flex-wrap gap-[6px]">
										{usedByAgents.map((a) => (
											<span key={a.id || a.name} className="inline-flex items-center gap-[5px] rounded-[5px] border border-[#E5E7EB] bg-[#F9FAFB] px-[10px] py-[4px] font-lato text-[12px] text-[#374151]">
												<span className="h-[6px] w-[6px] rounded-full bg-[#10B981]" />
												{a.name}
											</span>
										))}
									</div>
								</div>
							)}

							{/* Diff — only show if 2+ versions */}
							{versions.length >= 2 && (
								<DiffPanel promptId={prompt.id} versions={versions} />
							)}
						</div>

						{/* Right — version timeline */}
						<div className="p-[24px] bg-[#FAFAFA] overflow-y-auto max-h-[600px]">
							{versions.length > 0 ? (
								<VersionTimeline
									versions={versions}
									onPromote={onPromote}
									promotingId={promotingId}
								/>
							) : (
								<p className="font-lato text-[13px] text-[#9CA3AF]">No versions yet.</p>
							)}
						</div>
					</div>
					)}
				</div>
			)}
		</div>
	);
}

/* ─────────────────────────── Empty State ─────────────────────────── */

function EmptyState({ onCreateClick }) {
	return (
		<div className="flex flex-col items-center justify-center gap-[16px] rounded-[12px] border border-dashed border-[#D1D5DB] bg-white py-[60px]">
			<div className="flex h-[56px] w-[56px] items-center justify-center rounded-[16px] bg-[#FEF3C7]">
				<svg width="28" height="28" viewBox="0 0 28 28" fill="none">
					<path d="M5 4.5h18v16H14L10 24V20.5H5V4.5Z" stroke="#D97706" strokeWidth="1.5" strokeLinejoin="round"/>
					<path d="M9.5 9.5h9M9.5 13h6" stroke="#D97706" strokeWidth="1.2" strokeLinecap="round"/>
				</svg>
			</div>
			<div className="text-center">
				<p className="font-source-sans-pro text-[16px] font-semibold text-[#111827]">No prompts yet</p>
				<p className="mt-[4px] font-lato text-[14px] text-[#6B7280]">
					Create versioned, reusable prompt templates for your agents.
				</p>
			</div>
			<button
				onClick={onCreateClick}
				className="flex items-center gap-[6px] rounded-[8px] bg-[#5048ED] px-[18px] py-[9px] font-lato text-[14px] font-medium text-white hover:bg-[#4338CA] transition-colors"
			>
				<svg width="14" height="14" viewBox="0 0 14 14" fill="none">
					<path d="M7 2V12M2 7H12" stroke="white" strokeWidth="1.5" strokeLinecap="round"/>
				</svg>
				Create First Prompt
			</button>
		</div>
	);
}

/* ─────────────────────────── Stats Bar ─────────────────────────── */

function StatPill({ label, value, color }) {
	return (
		<div className="flex items-center gap-[8px]">
			<span className="font-lato text-[13px] text-[#6B7280]">{label}</span>
			<span className={`font-lato text-[14px] font-semibold ${color || 'text-[#111827]'}`}>{value}</span>
		</div>
	);
}

/* ─────────────────────────── New Version Modal Body ─────────────────────────── */

function NewVersionModalBody({ formik, versionPrompt, onClose }) {
	const currentContent = versionPrompt?.active_version?.content;
	// three modes: 'edit' | 'sidebyside' | 'diff'
	const [viewMode, setViewMode] = useState('edit');

	return (
		<form onSubmit={formik.handleSubmit} className="flex flex-col gap-[20px]">
			{/* Mode toggle — only if there's an existing active version */}
			{currentContent && (
				<div className="flex items-center justify-between">
					<span className="font-lato text-[12px] text-[#6B7280]">
						Editing from v{versionPrompt?.active_version_number || '?'} (active)
					</span>
					<div className="flex items-center rounded-[7px] border border-[#E5E7EB] overflow-hidden">
						{[
							{ key: 'edit', label: 'Edit' },
							{ key: 'sidebyside', label: 'Side by Side' },
							{ key: 'diff', label: 'Live Diff' },
						].map(({ key, label }) => (
							<button
								key={key}
								type="button"
								onClick={() => setViewMode(key)}
								className={`px-[10px] py-[5px] font-lato text-[12px] font-medium transition-colors ${
									viewMode === key
										? 'bg-[#5048ED] text-white'
										: 'text-[#6B7280] hover:bg-[#F9FAFB]'
								}`}
							>
								{label}
							</button>
						))}
					</div>
				</div>
			)}

			{/* Content editing area */}
			{viewMode === 'sidebyside' && currentContent ? (
				<div className="grid grid-cols-2 gap-[14px]">
					<div className="flex flex-col">
						<p className="mb-[6px] font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#9CA3AF]">
							Current (v{versionPrompt?.active_version_number}) — read only
						</p>
						<div className="rounded-[8px] bg-[#1F2937] p-[14px] min-h-[400px] max-h-[480px] overflow-y-auto flex-1">
							<HighlightedContent content={currentContent} />
						</div>
					</div>
					<div className="flex flex-col">
						<p className="mb-[6px] font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#9CA3AF]">
							New version
						</p>
						<PromptContentEditor
							value={formik.values.content}
							onChange={(e) => formik.setFieldValue('content', e.target.value)}
							onBlur={() => formik.setFieldTouched('content', true)}
							error={formik.touched.content && formik.errors.content}
							rows={18}
						/>
					</div>
				</div>
			) : viewMode === 'diff' && currentContent ? (
				<div className="grid grid-cols-2 gap-[14px]">
					<div className="flex flex-col">
						<p className="mb-[6px] font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#9CA3AF]">
							New version
						</p>
						<PromptContentEditor
							value={formik.values.content}
							onChange={(e) => formik.setFieldValue('content', e.target.value)}
							onBlur={() => formik.setFieldTouched('content', true)}
							error={formik.touched.content && formik.errors.content}
							rows={18}
						/>
					</div>
					<div className="flex flex-col">
						<LiveDiffPreview baseContent={currentContent} newContent={formik.values.content} />
					</div>
				</div>
			) : (
				<div>
					<label className="font-lato text-[12px] font-semibold uppercase tracking-[0.6px] text-[#6C747D]">
						Prompt Content
					</label>
					<div className="mt-[6px]">
						<PromptContentEditor
							value={formik.values.content}
							onChange={(e) => formik.setFieldValue('content', e.target.value)}
							onBlur={() => formik.setFieldTouched('content', true)}
							error={formik.touched.content && formik.errors.content}
							rows={16}
						/>
					</div>
				</div>
			)}

			<InputField
				label="What changed?"
				name="change_description"
				id="change_description"
				placeholder="e.g. Added pharmacovigilance topic weighting"
			/>

			{/* Draft notice */}
			<div className="flex items-start gap-[8px] rounded-[8px] bg-[#F0FDF4] border border-[#BBF7D0] px-[14px] py-[10px]">
				<svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="mt-[1px] flex-shrink-0">
					<circle cx="7" cy="7" r="6" stroke="#10B981" strokeWidth="1.2"/>
					<path d="M4.5 7L6.5 9L9.5 5" stroke="#10B981" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
				</svg>
				<p className="font-lato text-[12px] text-[#065F46]">
					Created as a <strong>draft</strong>. Promote it in the version history to make it active for all agent calls.
				</p>
			</div>

			<div className="flex justify-end gap-[12px] pt-[4px] border-t border-[#F3F4F6]">
				<button
					type="button"
					onClick={onClose}
					className="rounded-[8px] border border-[#DDE2E5] px-[20px] py-[9px] font-lato text-[14px] text-[#374151] hover:bg-[#F9FAFB] transition-colors"
				>
					Cancel
				</button>
				<button
					type="submit"
					disabled={formik.isSubmitting || !formik.isValid}
					className="rounded-[8px] bg-[#5048ED] px-[24px] py-[9px] font-lato text-[14px] font-medium text-white hover:bg-[#4338CA] disabled:opacity-50 disabled:pointer-events-none transition-colors"
				>
					{formik.isSubmitting ? 'Creating…' : 'Create Version'}
				</button>
			</div>
		</form>
	);
}

/* ─── Pagination bar ─── */
function PaginationBar({ page, totalPages, totalRecords, onPrev, onNext, onGoTo }) {
	const pageNumbers = [];
	const delta = 2;
	for (let i = Math.max(1, page - delta); i <= Math.min(totalPages, page + delta); i++) {
		pageNumbers.push(i);
	}
	const showLeftEllipsis = pageNumbers[0] > 2;
	const showRightEllipsis = pageNumbers[pageNumbers.length - 1] < totalPages - 1;
	return (
		<div className="flex items-center justify-between px-[16px] py-[14px] border-t border-[#E5E7EB] bg-[#F9FAFB] rounded-b-[8px]">
			<span className="font-lato text-[12px] text-[#6B7280]">
				{totalRecords != null ? `${totalRecords.toLocaleString()} prompt${totalRecords !== 1 ? 's' : ''}` : ''}
			</span>
			<div className="flex items-center gap-[4px]">
				<button onClick={onPrev} disabled={page === 1} className="flex items-center gap-[4px] rounded-[6px] border border-[#DDE2E5] px-[10px] py-[5px] font-lato text-[12px] text-[#374151] hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed">
					<svg width="12" height="12" viewBox="0 0 10 10"><path d="M7 1L3 5l4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" fill="none"/></svg>
					Prev
				</button>
				{pageNumbers[0] > 1 && (
					<>
						<button onClick={() => onGoTo(1)} className="rounded-[6px] border border-[#DDE2E5] px-[8px] py-[5px] font-lato text-[12px] text-[#374151] hover:bg-white">1</button>
						{showLeftEllipsis && <span className="px-[4px] font-lato text-[12px] text-[#9CA3AF]">…</span>}
					</>
				)}
				{pageNumbers.map(n => (
					<button key={n} onClick={() => onGoTo(n)} className={`rounded-[6px] border px-[8px] py-[5px] font-lato text-[12px] transition-colors ${n === page ? 'border-[#5048ED] bg-[#5048ED] text-white font-semibold' : 'border-[#DDE2E5] text-[#374151] hover:bg-white'}`}>{n}</button>
				))}
				{pageNumbers[pageNumbers.length - 1] < totalPages && (
					<>
						{showRightEllipsis && <span className="px-[4px] font-lato text-[12px] text-[#9CA3AF]">…</span>}
						<button onClick={() => onGoTo(totalPages)} className="rounded-[6px] border border-[#DDE2E5] px-[8px] py-[5px] font-lato text-[12px] text-[#374151] hover:bg-white">{totalPages}</button>
					</>
				)}
				<button onClick={onNext} disabled={page === totalPages} className="flex items-center gap-[4px] rounded-[6px] border border-[#DDE2E5] px-[10px] py-[5px] font-lato text-[12px] text-[#374151] hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed">
					Next
					<svg width="12" height="12" viewBox="0 0 10 10"><path d="M3 1l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" fill="none"/></svg>
				</button>
			</div>
			<span className="font-lato text-[12px] text-[#6B7280]">Page {page} of {totalPages}</span>
		</div>
	);
}

/* ─────────────────────────── Main Component ─────────────────────────── */

export default function Prompts({ onReady, refreshSignal, onFetchComplete }) {
	const { appId } = useParams();
	const triggerApi = useApi();
	const readyCalledRef = useRef(false);

	const [prompts, setPrompts] = useState([]);
	const [stats, setStats] = useState({});
	const [loading, setLoading] = useState(true);
	const [refreshing, setRefreshing] = useState(false);
	const [searching, setSearching] = useState(false);
	const [search, setSearch] = useState('');
	const [debouncedSearch, setDebouncedSearch] = useState('');
	const [typeFilter, setTypeFilter] = useState('');
	const [showInactive, setShowInactive] = useState(false);

	// Pagination
	const [page, setPage] = useState(1);
	const [totalPages, setTotalPages] = useState(1);
	const [totalRecords, setTotalRecords] = useState(0);

	// Debounce search input — wait 400ms after last keystroke before fetching
	useEffect(() => {
		const t = setTimeout(() => setDebouncedSearch(search), 400);
		return () => clearTimeout(t);
	}, [search]);

	const [createModalOpen, setCreateModalOpen] = useState(false);
	const [editModalOpen, setEditModalOpen] = useState(false);
	const [editingPrompt, setEditingPrompt] = useState(null);
	const [newVersionModalOpen, setNewVersionModalOpen] = useState(false);
	const [versionPrompt, setVersionPrompt] = useState(null);

	const [deactivateModal, setDeactivateModal] = useState({ show: false, prompt: null });
	const [depModal, setDepModal] = useState({ show: false, entityName: '', agentCount: 0, agents: [] });
	const [promotingId, setPromotingId] = useState(null);
	const [actionLoading, setActionLoading] = useState(false);

	/* ── fetch ── */
	const isFirstLoad = useRef(true);
	const fetchPrompts = useCallback(async ({ background = false } = {}) => {
		if (background) {
			setRefreshing(true);
		} else if (isFirstLoad.current) {
			setLoading(true);
		} else {
			setSearching(true);
		}
		const params = new URLSearchParams({ page: String(page) });
		if (showInactive) params.set('include_inactive', 'true');
		if (debouncedSearch) params.set('search', debouncedSearch);
		if (typeFilter) params.set('type', typeFilter);
		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/ai/prompts/?${params}`,
			type: 'GET',
			loader: false,
		});
		if (success && response) {
			const data = response.prompts || {};
			const records = Array.isArray(data.records) ? data.records : [];
			setTotalPages(data.total_pages || 1);
			setTotalRecords(data.total_records || 0);
			if (response.stats) setStats(response.stats);
			setPrompts(records);
			onFetchComplete?.();
		}
		isFirstLoad.current = false;
		setLoading(false);
		setSearching(false);
		setRefreshing(false);
		if (!readyCalledRef.current && onReady) {
			readyCalledRef.current = true;
			onReady();
		}
	}, [appId, triggerApi, showInactive, page, debouncedSearch, typeFilter, onFetchComplete]);

	useEffect(() => { fetchPrompts(); }, [fetchPrompts]);

	// Background re-fetch when parent signals staleness (skip first render)
	const isFirstRefreshSignal = useRef(true);
	useEffect(() => {
		if (isFirstRefreshSignal.current) { isFirstRefreshSignal.current = false; return; }
		if (!refreshSignal) return;
		fetchPrompts({ background: true });
	}, [refreshSignal]);

	/* ── filtered list (client-side no longer needed — server handles it) ── */
	const filteredPrompts = prompts;

	/* ── CRUD handlers ── */
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

	const handleEditPrompt = async (values, { resetForm, setSubmitting }) => {
		if (!editingPrompt) return;
		const { success } = await triggerApi({
			url: `/api/v1/apps/${appId}/ai/prompts/${editingPrompt.id}/`,
			type: 'PUT',
			loader: true,
			payload: { name: values.name, description: values.description, type: values.type },
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

	const handleCreateVersion = async (values, { resetForm, setSubmitting }) => {
		if (!versionPrompt) return;
		const { success } = await triggerApi({
			url: `/api/v1/apps/${appId}/ai/prompts/${versionPrompt.id}/versions/`,
			type: 'POST',
			loader: true,
			payload: { content: values.content, change_description: values.change_description },
		});
		setSubmitting(false);
		if (success) {
			setNewVersionModalOpen(false);
			setVersionPrompt(null);
			resetForm();
			notify('success', 'Version Created', 'New draft version created. Promote it to make it active.');
			fetchPrompts();
		}
	};

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

	const handleDeactivate = (prompt) => {
		setDeactivateModal({ show: true, prompt });
	};

	const handleActivate = async (prompt) => {
		const { success } = await triggerApi({
			url: `/api/v1/apps/${appId}/ai/prompts/${prompt.id}/activate/`,
			type: 'POST',
			loader: false,
			showErrorModal: false,
		});
		if (success) {
			notify('success', 'Prompt Activated', `${prompt.name} is now active.`);
			fetchPrompts();
		}
	};

	const confirmDeactivate = async () => {
		const prompt = deactivateModal.prompt;
		setActionLoading(true);
		const { success, response } = await triggerApi({
			url: `/api/v1/apps/${appId}/ai/prompts/${prompt.id}/`,
			type: 'DELETE',
			loader: false,
		});
		setActionLoading(false);
		setDeactivateModal({ show: false, prompt: null });

		if (!success && response?.error_code === 'PROMPT_IN_USE') {
			setDepModal({
				show: true,
				entityName: prompt.name,
				agentCount: response.agents?.length ?? 0,
				agents: response.agents ?? [],
			});
			return;
		}

		if (success) {
			const isDeactivated = response?.message?.includes('deactivated');
			notify(
				'success',
				isDeactivated ? 'Prompt Deactivated' : 'Prompt Deleted',
				isDeactivated
					? `${prompt.name} has been deactivated and removed from the registry.`
					: `${prompt.name} has been permanently deleted.`
			);
			fetchPrompts();
		}
	};

	const openEdit = (prompt) => { setEditingPrompt(prompt); setEditModalOpen(true); };
	const openNewVersion = (prompt) => { setVersionPrompt(prompt); setNewVersionModalOpen(true); };

	/* ── validation schemas ── */
	const createValidation = Yup.object({
		name: Yup.string()
			.matches(/^[a-z0-9-]+$/, 'Lowercase letters, numbers, and hyphens only')
			.required('Name is required'),
		type: Yup.string().oneOf(['system', 'user']).required(),
		content: Yup.string().required('Prompt content is required'),
	});
	const editValidation = Yup.object({
		name: Yup.string().required('Name is required'),
		type: Yup.string().oneOf(['system', 'user']).required(),
	});
	const versionValidation = Yup.object({
		content: Yup.string().required('Content is required'),
	});

	return (
		<div className="flex flex-col gap-[20px]">

			{/* ── Header card ── */}
			<div className="rounded-[14px] border border-[#E5E7EB] bg-white p-[24px]">
				<div className="flex items-start justify-between gap-[16px]">
					<div>
						<h2 className="font-source-sans-pro text-[18px] font-semibold text-[#111827]">
							Prompt Registry
						</h2>
						<p className="mt-[2px] font-lato text-[13px] text-[#6B7280] max-w-[520px]">
							Versioned prompt templates with variable slots. Code references prompts by name; the panel controls which version is live — no deploys needed.
						</p>
						<div className="mt-[14px] flex items-center gap-[20px] flex-wrap">
							<StatPill label="Total prompts" value={stats.total_prompts ?? '—'} />
							<div className="h-[14px] w-[1px] bg-[#E5E7EB]" />
							<StatPill label="With active version" value={stats.active_versions ?? '—'} color="text-[#10B981]" />
							<div className="h-[14px] w-[1px] bg-[#E5E7EB]" />
							<StatPill label="Total versions" value={stats.total_versions ?? '—'} />
						</div>
					</div>
					<div className="flex items-center gap-[8px]">
						<button
							onClick={() => fetchPrompts({ background: true })}
							disabled={refreshing}
							className="flex items-center gap-[5px] rounded-[6px] border border-[#DDE2E5] px-[10px] py-[8px] font-lato text-[13px] text-[#374151] hover:bg-[#F9FAFB] disabled:opacity-50 transition-colors"
						>
							<svg
								width="12" height="12" viewBox="0 0 12 12" fill="none"
								className={refreshing ? 'animate-spin' : ''}
							>
								<path d="M10.5 6A4.5 4.5 0 1 1 8.5 2.1" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
								<path d="M8.5 1v2.5H11" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
							</svg>
							{refreshing ? 'Refreshing…' : 'Refresh'}
						</button>
						<button
							onClick={() => setCreateModalOpen(true)}
							className="flex-shrink-0 flex items-center gap-[6px] rounded-[8px] bg-[#5048ED] px-[16px] py-[9px] font-lato text-[14px] font-medium text-white hover:bg-[#4338CA] transition-colors shadow-sm"
						>
							<svg width="13" height="13" viewBox="0 0 13 13" fill="none">
								<path d="M6.5 1.5V11.5M1.5 6.5H11.5" stroke="white" strokeWidth="1.5" strokeLinecap="round"/>
							</svg>
							Create Prompt
						</button>
					</div>
				</div>
			</div>

			{/* ── Search + filter bar ── */}
			{!loading && (
				<div className="flex items-center gap-[10px]">
					<div className="relative flex-1 max-w-[360px]">
						{searching ? (
							<svg className="absolute left-[12px] top-1/2 -translate-y-1/2 animate-spin text-[#5048ED]" width="14" height="14" viewBox="0 0 14 14" fill="none">
								<path d="M7 1.5A5.5 5.5 0 1 0 12.5 7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
							</svg>
						) : (
							<svg
								width="14" height="14" viewBox="0 0 14 14" fill="none"
								className="absolute left-[12px] top-1/2 -translate-y-1/2 text-[#9CA3AF]"
							>
								<circle cx="6" cy="6" r="4.5" stroke="currentColor" strokeWidth="1.3"/>
								<path d="M9.5 9.5L12.5 12.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
							</svg>
						)}
						<input
							type="text"
							value={search}
							onChange={(e) => { setSearch(e.target.value); setPage(1); }}
							placeholder="Search prompts…"
							className="w-full rounded-[8px] border border-[#DDE2E5] pl-[36px] pr-[12px] py-[8px] font-lato text-[13px] text-[#111827] placeholder-[#9CA3AF] outline-none focus:border-[#5048ED] focus:ring-1 focus:ring-[#5048ED] transition-colors"
						/>
					</div>
					<div className="flex items-center gap-[6px]">
						{['', 'system', 'user'].map((t) => (
							<button
								key={t}
								onClick={() => { setTypeFilter(t); setPage(1); }}
								className={`rounded-[7px] px-[12px] py-[7px] font-lato text-[12px] font-medium transition-colors ${
									typeFilter === t
										? t === 'system'
											? 'bg-[#EFF6FF] text-[#346BD4] border border-[#BFDBFE]'
											: t === 'user'
											? 'bg-[#F3E8FF] text-[#7C3AED] border border-[#DDD6FE]'
											: 'bg-[#F3F4F6] text-[#374151] border border-[#E5E7EB]'
										: 'border border-[#E5E7EB] text-[#6B7280] hover:bg-[#F9FAFB]'
								}`}
							>
								{t === '' ? 'All' : t.charAt(0).toUpperCase() + t.slice(1)}
							</button>
						))}
					</div>
					{(search || typeFilter) && (
						<button
							onClick={() => { setSearch(''); setTypeFilter(''); setPage(1); }}
							className="font-lato text-[12px] text-[#9CA3AF] hover:text-[#6B7280] transition-colors"
						>
							Clear
						</button>
					)}
					<div className="ml-auto">
						<button
							onClick={() => { setShowInactive((v) => !v); setPage(1); }}
							className={`flex items-center gap-[6px] rounded-[7px] border px-[12px] py-[7px] font-lato text-[12px] font-medium transition-colors ${
								showInactive
									? 'border-[#DDD6FE] bg-[#F5F3FF] text-[#5048ED]'
									: 'border-[#E5E7EB] text-[#6B7280] hover:bg-[#F9FAFB]'
							}`}
						>
							<svg width="12" height="12" viewBox="0 0 12 12" fill="none">
								<circle cx="6" cy="6" r="4.5" stroke="currentColor" strokeWidth="1.3"/>
								<path d="M3.5 3.5L8.5 8.5M8.5 3.5L3.5 8.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
							</svg>
							{showInactive ? 'Hide deactivated' : 'Show deactivated'}
						</button>
					</div>
				</div>
			)}

			{/* ── Table header (when items exist) ── */}
			{filteredPrompts.length > 0 && (
				<div className="flex items-center px-[20px]">
					<span className="ml-[62px] flex-1 font-lato text-[10px] font-bold uppercase tracking-[0.6px] text-[#9CA3AF]">
						Prompt
					</span>
					<div className="flex items-center gap-[28px] flex-shrink-0 mr-[4px]">
						<span className="hidden md:block w-[60px] text-center font-lato text-[10px] font-bold uppercase tracking-[0.6px] text-[#9CA3AF]">Active</span>
						<span className="hidden md:block w-[60px] text-center font-lato text-[10px] font-bold uppercase tracking-[0.6px] text-[#9CA3AF]">Versions</span>
						<span className="hidden lg:block w-[80px] text-center font-lato text-[10px] font-bold uppercase tracking-[0.6px] text-[#9CA3AF]">Modified</span>
						<span className="w-[130px]" />
					</div>
				</div>
			)}

			{/* ── Prompt list ── */}
			<div className="flex flex-col gap-[10px]">
				{loading ? (
					<div className="flex items-center justify-center py-[48px]">
						<svg className="animate-spin text-[#5048ED]" width="24" height="24" viewBox="0 0 24 24" fill="none">
							<path d="M12 3a9 9 0 1 0 9 9" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
						</svg>
					</div>
				) : filteredPrompts.length === 0 ? (
					prompts.length === 0 ? (
						<EmptyState onCreateClick={() => setCreateModalOpen(true)} />
					) : (
						<div className="rounded-[10px] border border-[#E5E7EB] bg-white px-[24px] py-[32px] text-center">
							<p className="font-lato text-[14px] text-[#9CA3AF]">
								No prompts match your filters.{' '}
								<button onClick={() => { setSearch(''); setTypeFilter(''); setPage(1); }} className="text-[#5048ED] hover:underline">
									Clear filters
								</button>
							</p>
						</div>
					)
				) : (
					filteredPrompts.map((prompt) => (
						<PromptRow
							key={prompt.id}
							prompt={prompt}
							onEdit={openEdit}
							onNewVersion={openNewVersion}
							onPromote={handlePromote}
							onDeactivate={handleDeactivate}
						onActivate={handleActivate}
							promotingId={promotingId}
						/>
					))
				)}
				{totalPages > 1 && !loading && (
					<div className="rounded-[10px] border border-[#E5E7EB] bg-white overflow-hidden">
						<PaginationBar
							page={page}
							totalPages={totalPages}
							totalRecords={totalRecords}
							onPrev={() => setPage(p => Math.max(1, p - 1))}
							onNext={() => setPage(p => Math.min(totalPages, p + 1))}
							onGoTo={setPage}
						/>
					</div>
				)}
			</div>

			{/* ═══════════════════════════════════════════════════
			    CREATE PROMPT MODAL
			═══════════════════════════════════════════════════ */}
			<Formik
				initialValues={{ name: '', description: '', type: 'system', content: '', change_description: '' }}
				validationSchema={createValidation}
				onSubmit={handleCreatePrompt}
				enableReinitialize
			>
				{(formik) => (
					<Modal
						label="Create Prompt"
						maxWidth="max-w-[680px]"
						show={createModalOpen}
						closeModal={() => { setCreateModalOpen(false); formik.resetForm(); }}
						ModalBody={
							<form
								onSubmit={formik.handleSubmit}
								className="flex flex-col gap-[20px]"
							>
								{/* Name + Type row */}
								<div className="grid grid-cols-[1fr_140px] gap-[12px]">
									<div>
										<InputField
											label="Prompt Name"
											name="name"
											id="name"
											placeholder="e.g. assessment-system"
										/>
										<p className="mt-[4px] font-lato text-[11px] text-[#9CA3AF]">
											Lowercase letters, numbers, hyphens only
										</p>
									</div>
									<div>
										<label className="font-lato text-[12px] font-semibold uppercase tracking-[0.6px] text-[#6C747D]">
											Type
										</label>
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
								</div>

								<InputField
									label="Description"
									name="description"
									id="description"
									placeholder="What this prompt does (optional)"
								/>

								<div>
									<label className="font-lato text-[12px] font-semibold uppercase tracking-[0.6px] text-[#6C747D]">
										Prompt Content
									</label>
									<div className="mt-[6px]">
										<PromptContentEditor
											value={formik.values.content}
											onChange={(e) => formik.setFieldValue('content', e.target.value)}
											onBlur={() => formik.setFieldTouched('content', true)}
											error={formik.touched.content && formik.errors.content}
											rows={8}
										/>
									</div>
								</div>

								<InputField
									label="Version Note"
									name="change_description"
									id="change_description"
									placeholder="e.g. Initial version"
								/>

								<div className="flex justify-end gap-[12px] pt-[4px] border-t border-[#F3F4F6]">
									<button
										type="button"
										onClick={() => { setCreateModalOpen(false); formik.resetForm(); }}
										className="rounded-[8px] border border-[#DDE2E5] px-[20px] py-[9px] font-lato text-[14px] text-[#374151] hover:bg-[#F9FAFB] transition-colors"
									>
										Cancel
									</button>
									<button
										type="submit"
										disabled={formik.isSubmitting || !formik.isValid}
										className="rounded-[8px] bg-[#5048ED] px-[24px] py-[9px] font-lato text-[14px] font-medium text-white hover:bg-[#4338CA] disabled:opacity-50 disabled:pointer-events-none transition-colors"
									>
										{formik.isSubmitting ? 'Creating…' : 'Create Prompt'}
									</button>
								</div>
							</form>
						}
					/>
				)}
			</Formik>

			{/* ═══════════════════════════════════════════════════
			    EDIT PROMPT MODAL
			═══════════════════════════════════════════════════ */}
			<Formik
				initialValues={
					editingPrompt
						? { name: editingPrompt.name, description: editingPrompt.description || '', type: editingPrompt.type }
						: { name: '', description: '', type: 'system' }
				}
				validationSchema={editValidation}
				onSubmit={handleEditPrompt}
				enableReinitialize
			>
				{(formik) => (
					<Modal
						label={`Edit — ${editingPrompt?.name || ''}`}
						show={editModalOpen}
						closeModal={() => { setEditModalOpen(false); setEditingPrompt(null); formik.resetForm(); }}
						ModalBody={
							<form onSubmit={formik.handleSubmit} className="flex flex-col gap-[20px]">
								<div className="rounded-[8px] border border-[#FEF3C7] bg-[#FFFBEB] px-[14px] py-[10px]">
									<p className="font-lato text-[13px] text-[#92400E]">
										Editing metadata only. To change the prompt text, create a new version.
									</p>
								</div>
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
								<div className="flex justify-end gap-[12px] pt-[4px] border-t border-[#F3F4F6]">
									<button
										type="button"
										onClick={() => { setEditModalOpen(false); setEditingPrompt(null); formik.resetForm(); }}
										className="rounded-[8px] border border-[#DDE2E5] px-[20px] py-[9px] font-lato text-[14px] text-[#374151] hover:bg-[#F9FAFB] transition-colors"
									>
										Cancel
									</button>
									<button
										type="submit"
										disabled={formik.isSubmitting || !formik.isValid}
										className="rounded-[8px] bg-[#5048ED] px-[24px] py-[9px] font-lato text-[14px] font-medium text-white hover:bg-[#4338CA] disabled:opacity-50 disabled:pointer-events-none transition-colors"
									>
										{formik.isSubmitting ? 'Saving…' : 'Save Changes'}
									</button>
								</div>
							</form>
						}
					/>
				)}
			</Formik>

			{/* ═══════════════════════════════════════════════════
			    NEW VERSION MODAL — edit / side-by-side / live diff
			═══════════════════════════════════════════════════ */}
			<Formik
				initialValues={{
					content: versionPrompt?.active_version?.content || '',
					change_description: '',
				}}
				validationSchema={versionValidation}
				onSubmit={handleCreateVersion}
				enableReinitialize
			>
				{(formik) => (
					<Modal
						label={`New Version — ${versionPrompt?.name || ''}`}
						maxWidth="max-w-[900px]"
						show={newVersionModalOpen}
						closeModal={() => {
							setNewVersionModalOpen(false);
							setVersionPrompt(null);
							formik.resetForm();
						}}
						ModalBody={
							<NewVersionModalBody
								formik={formik}
								versionPrompt={versionPrompt}
								onClose={() => {
									setNewVersionModalOpen(false);
									setVersionPrompt(null);
									formik.resetForm();
								}}
							/>
						}
					/>
				)}
			</Formik>

			{/* ── Deactivate confirmation ── */}
			<DeactivateModal
				show={deactivateModal.show}
				prompt={deactivateModal.prompt}
				onClose={() => setDeactivateModal({ show: false, prompt: null })}
				onConfirm={confirmDeactivate}
				loading={actionLoading}
			/>

			{/* ── Dependency block — shown when prompt is in use by active agents ── */}
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
