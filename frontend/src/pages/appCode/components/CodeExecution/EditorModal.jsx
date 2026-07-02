import React, { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import Editor from '@monaco-editor/react';
import toast from 'react-hot-toast';
import useApi from '../../../../hooks/useApi';
import ConfirmModal from './ConfirmModal';
import Spinner from './Spinner';

// Helpers list shown inside the modal — keep in sync with src/zango/codexec.py
const HELPERS = [
	{ sig: 'codexec.read(name)', ret: 'bytes', kind: 'read' },
	{ sig: 'codexec.read_text(name, enc="utf-8")', ret: 'str', kind: 'read' },
	{ sig: 'codexec.read_json(name)', ret: 'parsed', kind: 'read' },
	{ sig: 'codexec.open(name, mode="rb")', ret: 'file-like', kind: 'read' },
	{ sig: 'codexec.local_path(name)', ret: 'Path', kind: 'read' },
	{ sig: 'codexec.list_inputs()', ret: 'list[FileRef]', kind: 'read' },
	{ sig: 'codexec.write(name, data)', ret: 'FileRef', kind: 'write' },
	{ sig: 'codexec.write_text(name, text)', ret: 'FileRef', kind: 'write' },
	{ sig: 'codexec.write_json(name, obj, indent=2)', ret: 'FileRef', kind: 'write' },
	{ sig: 'codexec.open_output(name, mode="wb")', ret: 'file-like', kind: 'write' },
	{ sig: 'codexec.list_outputs()', ret: 'list[FileRef]', kind: 'write' },
];

const STARTER_CODE = `# Write your script here.
# Read inputs with: codexec.read_text("input.csv")
# Write outputs with: codexec.write_text("result.txt", "...")
# Optional: set codexec_result = {...} to record a return value.

print("hello, codexec!")
codexec_result = {"ok": True}
`;

function formatBytes(n) {
	if (n == null) return '';
	if (n < 1024) return `${n} B`;
	if (n < 1024 * 1024) return `${(n / 1024).toFixed(0)} KB`;
	return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

function extOf(name) {
	const i = (name || '').lastIndexOf('.');
	return i === -1 ? '' : name.substring(i + 1).slice(0, 4);
}

export default function EditorModal({ appId, snippet, onClose, onSaved }) {
	const triggerApi = useApi();
	const isEdit = Boolean(snippet);

	const [name, setName] = useState(snippet?.name || '');
	const [description, setDescription] = useState(snippet?.description || '');
	const [code, setCode] = useState(snippet?.code || STARTER_CODE);
	const [timeoutSeconds, setTimeoutSeconds] = useState(snippet?.timeout_seconds || 60);

	const [files, setFiles] = useState([]);          // existing snippet files
	const [pendingFiles, setPendingFiles] = useState([]); // newly added File objects
	const [violations, setViolations] = useState([]);
	const [validating, setValidating] = useState(false);
	const [saving, setSaving] = useState(false);
	const [mounted, setMounted] = useState(false);
	const [confirmRemoveFile, setConfirmRemoveFile] = useState(null);
	const [optionsOpen, setOptionsOpen] = useState(false);
	const fileInputRef = useRef(null);

	// Animate in on first paint + lock body scroll while modal is open.
	useEffect(() => {
		const t = setTimeout(() => setMounted(true), 10);
		const prevOverflow = document.body.style.overflow;
		document.body.style.overflow = 'hidden';
		return () => {
			clearTimeout(t);
			document.body.style.overflow = prevOverflow;
		};
	}, []);

	const requestClose = () => {
		setMounted(false);
		setTimeout(() => onClose?.(), 180);
	};

	// Load existing snippet files when editing
	useEffect(() => {
		if (!isEdit) return;
		(async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/code-execution/snippets/${snippet.object_uuid}/files/`,
				type: 'GET',
				loader: false,
			});
			if (success && response?.files) setFiles(response.files);
		})();
	}, [appId, snippet, isEdit, triggerApi]);

	const validateCode = async (src) => {
		setValidating(true);
		try {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/code-execution/snippets/validate/`,
				type: 'POST',
				payload: { code: src },
				loader: false,
				showErrorModal: false,
			});
			if (success && response) setViolations(response.violations || []);
		} finally {
			setValidating(false);
		}
	};

	// Debounced validation on code change
	useEffect(() => {
		const id = setTimeout(() => { validateCode(code); }, 600);
		return () => clearTimeout(id);
	}, [code]); // eslint-disable-line react-hooks/exhaustive-deps

	const onPickFiles = (e) => {
		const incoming = Array.from(e.target.files || []);
		setPendingFiles((prev) => [...prev, ...incoming]);
		e.target.value = '';  // allow re-picking same file
	};

	const askRemoveExistingFile = (file) => setConfirmRemoveFile(file);

	const confirmedRemoveExistingFile = async () => {
		const fileId = confirmRemoveFile?.object_uuid;
		setConfirmRemoveFile(null);
		if (!fileId) return;
		const { success } = await triggerApi({
			url: `/api/v1/apps/${appId}/code-execution/snippets/${snippet.object_uuid}/files/${fileId}/delete/`,
			type: 'POST',
			payload: {},
			loader: false,
		});
		if (success) {
			setFiles((prev) => prev.filter((f) => f.object_uuid !== fileId));
			toast.success('File removed');
		}
	};

	const removePending = (idx) => {
		setPendingFiles((prev) => prev.filter((_, i) => i !== idx));
	};

	const uploadPendingFiles = async (snippetId) => {
		if (pendingFiles.length === 0) return;
		const form = new FormData();
		pendingFiles.forEach((f) => form.append('files', f, f.name));
		await triggerApi({
			url: `/api/v1/apps/${appId}/code-execution/snippets/${snippetId}/files/`,
			type: 'POST',
			payload: form,
			loader: false,
		});
	};

	const handleSave = async (runAfter = false) => {
		if (!name.trim()) {
			toast.error('Name is required.');
			return;
		}
		setSaving(true);
		try {
			let saved = snippet;
			const payload = {
				name,
				description,
				code,
				timeout_seconds: Number(timeoutSeconds),
			};
			const url = isEdit
				? `/api/v1/apps/${appId}/code-execution/snippets/${snippet.object_uuid}/update/`
				: `/api/v1/apps/${appId}/code-execution/snippets/`;
			const { response, success } = await triggerApi({
				url,
				type: 'POST',
				payload,
				loader: false,
				showErrorModal: false,
			});
			if (!success) {
				if (response?.violations) {
					setViolations(response.violations);
					toast.error('Fix validation errors first.');
				} else {
					toast.error(response?.message || 'Save failed.');
				}
				return;
			}
			saved = response.snippet;

			await uploadPendingFiles(saved.object_uuid);

			toast.success(runAfter ? 'Saved · queuing run' : 'Saved');
			onSaved?.(saved, runAfter);
		} catch (e) {
			toast.error('Save failed.');
		} finally {
			setSaving(false);
		}
	};

	// Cmd+S = Save, Cmd+Enter = Save & Run, Esc to close
	useEffect(() => {
		const onKey = (e) => {
			if ((e.metaKey || e.ctrlKey) && e.key === 's') {
				e.preventDefault();
				handleSave(false);
			} else if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
				e.preventDefault();
				handleSave(true);
			} else if (e.key === 'Escape') {
				requestClose();
			}
		};
		window.addEventListener('keydown', onKey);
		return () => window.removeEventListener('keydown', onKey);
	}); // re-bind each render so closures see fresh state

	const modalContent = (
		<div
			className={`fixed inset-0 z-[1000] flex items-start justify-center overflow-auto p-8 bg-slate-900/55 backdrop-blur-[2px] transition-opacity duration-200 ease-out ${mounted ? 'opacity-100' : 'opacity-0'}`}
			onMouseDown={(e) => { if (e.target === e.currentTarget) requestClose(); }}
		>
			<div
				className={`bg-white rounded-2xl shadow-2xl w-full max-w-[1080px] overflow-hidden flex flex-col transition-all duration-200 ease-out ${mounted ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-2 scale-[0.985]'}`}
				role="dialog"
				aria-modal="true"
			>
				{/* Head */}
				<div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 bg-gradient-to-b from-slate-50 to-white">
					<div className="flex items-center gap-2.5">
						<div className="w-7 h-7 bg-indigo-50 text-indigo-600 rounded-md grid place-items-center font-mono text-[13px] font-semibold">py</div>
						<div className="text-[14px] font-semibold text-slate-900">
							{isEdit ? 'Edit snippet' : 'New code execution'}
						</div>
						<span className="text-slate-300">/</span>
						<span className="text-[13px] text-slate-500">{isEdit ? `v${snippet.version}` : 'Draft'}</span>
					</div>
					<button onClick={requestClose} className="w-7 h-7 grid place-items-center rounded text-slate-500 hover:bg-slate-100 transition-colors">
						<span style={{ fontSize: 18, lineHeight: 1 }}>×</span>
					</button>
				</div>

				{/* Body */}
				<div className="p-5 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 180px)' }}>
					{/* Name */}
					<label className="block">
						<div className="text-[10.5px] font-semibold uppercase tracking-[0.07em] text-slate-500 mb-1.5">Name</div>
						<input
							value={name}
							onChange={(e) => setName(e.target.value)}
							placeholder="e.g. Recompute MLR review SLAs"
							className="w-full px-3 py-2 text-[13px] border border-slate-300 rounded-md focus:outline-none focus:border-[#346BD4] focus:ring-2 focus:ring-[#346BD4]/15"
						/>
					</label>

					<label className="block mt-3">
						<div className="text-[10.5px] font-semibold uppercase tracking-[0.07em] text-slate-500 mb-1.5">
							Description <span className="font-normal text-slate-400 normal-case tracking-normal text-[11px]">(optional)</span>
						</div>
						<input
							value={description}
							onChange={(e) => setDescription(e.target.value)}
							placeholder="Briefly say what this snippet does."
							className="w-full px-3 py-2 text-[13px] border border-slate-300 rounded-md focus:outline-none focus:border-[#346BD4] focus:ring-2 focus:ring-[#346BD4]/15"
						/>
					</label>

					{/* Collapsible Options: Timeout + Input files */}
					<div className="mt-3 border border-slate-200 rounded-md overflow-hidden bg-white">
						<button
							type="button"
							onClick={() => setOptionsOpen((v) => !v)}
							className="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-slate-50 transition-colors"
							aria-expanded={optionsOpen}
						>
							<div className="flex items-center gap-2">
								<svg
									width="11" height="11" viewBox="0 0 16 16" fill="none"
									className={`text-slate-500 transition-transform duration-150 ${optionsOpen ? 'rotate-90' : ''}`}
								>
									<path d="M5 3L11 8L5 13" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
								</svg>
								<span className="text-[12.5px] font-medium text-slate-800">Options</span>
								<span className="text-[11.5px] text-slate-500">
									Timeout {timeoutSeconds}s · {(files.length + pendingFiles.length) || 'No'} input file{(files.length + pendingFiles.length) !== 1 ? 's' : ''}
								</span>
							</div>
							<span className="text-[11px] text-slate-400">{optionsOpen ? 'Hide' : 'Edit'}</span>
						</button>
						<div
							className={`grid transition-[grid-template-rows] duration-200 ease-out ${optionsOpen ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'}`}
							style={{ display: 'grid' }}
						>
							<div className="overflow-hidden">
								<div className="px-3 pb-3 pt-1 border-t border-slate-200">
									{/* Timeout */}
									<label className="block mt-3 max-w-[220px]">
										<div className="text-[10.5px] font-semibold uppercase tracking-[0.07em] text-slate-500 mb-1.5">Timeout (seconds)</div>
										<input
											type="number"
											min={5}
											max={86400}
											value={timeoutSeconds}
											onChange={(e) => setTimeoutSeconds(e.target.value)}
											className="w-full px-3 py-2 text-[13px] border border-slate-300 rounded-md focus:outline-none focus:border-[#346BD4]"
										/>
									</label>

									{/* Files */}
									<div className="mt-4">
										<div className="text-[10.5px] font-semibold uppercase tracking-[0.07em] text-slate-500 mb-1.5">
											Input files <span className="font-normal text-slate-400 normal-case tracking-normal text-[11px]">(saved with the snippet · auto-snapshotted into every run)</span>
										</div>
										<div className="border border-dashed border-slate-300 rounded-md bg-gradient-to-b from-slate-50 to-white p-3">
							<div className="flex items-center justify-between mb-2">
								<div className="flex items-center gap-2.5">
									<div className="w-6 h-6 bg-indigo-50 text-indigo-600 rounded grid place-items-center text-[13px] font-semibold">⇪</div>
									<div>
										<div className="text-[12.5px] font-medium text-slate-800">Drop files here or click to add</div>
										<div className="text-[11px] text-slate-500">Up to 10 files · 25 MB each</div>
									</div>
								</div>
								<button
									onClick={() => fileInputRef.current?.click()}
									className="px-2.5 py-1 bg-white border border-slate-300 rounded text-[11.5px] font-medium text-slate-700 hover:border-slate-400"
								>
									+ Add files
								</button>
								<input ref={fileInputRef} type="file" multiple hidden onChange={onPickFiles} />
							</div>
							<div className="flex flex-col gap-1.5">
								{files.map((f) => (
									<div key={f.object_uuid} className="grid items-center gap-2 bg-white border border-slate-200 rounded px-2.5 py-1.5 text-[12px] transition-shadow hover:shadow-sm" style={{ gridTemplateColumns: '22px 1fr auto auto auto' }}>
										<span className="w-[22px] h-[22px] bg-slate-100 text-slate-500 rounded font-mono text-[9.5px] uppercase font-semibold grid place-items-center">{extOf(f.name)}</span>
										<span className="text-slate-900 font-medium">{f.name}</span>
										<span className="font-mono text-slate-400 text-[10.5px]">saved</span>
										<span className="font-mono text-slate-500 text-[11px]">{formatBytes(f.size_bytes)}</span>
										<button onClick={() => askRemoveExistingFile(f)} className="text-slate-300 hover:text-rose-500 w-4 text-center transition-colors">×</button>
									</div>
								))}
								{pendingFiles.map((f, idx) => (
									<div key={`p-${idx}`} className="grid items-center gap-2 bg-amber-50/50 border border-amber-100 rounded px-2.5 py-1.5 text-[12px]" style={{ gridTemplateColumns: '22px 1fr auto auto auto' }}>
										<span className="w-[22px] h-[22px] bg-amber-100 text-amber-700 rounded font-mono text-[9.5px] uppercase font-semibold grid place-items-center">{extOf(f.name)}</span>
										<span className="text-slate-900 font-medium">{f.name}</span>
										<span className="font-mono text-amber-700 text-[10.5px]">pending</span>
										<span className="font-mono text-slate-500 text-[11px]">{formatBytes(f.size)}</span>
										<button onClick={() => removePending(idx)} className="text-slate-300 hover:text-rose-500 w-4 text-center">×</button>
									</div>
								))}
								{files.length === 0 && pendingFiles.length === 0 && (
									<div className="text-[11.5px] text-slate-400 text-center py-2">No files yet.</div>
								)}
							</div>
						</div>
									</div>{/* end Files outer wrapper */}
								</div>{/* end disclosure inner padding */}
							</div>{/* end overflow-hidden */}
						</div>{/* end grid rows */}
					</div>{/* end Options disclosure */}

					{/* Code */}
					<div className="mt-4">
						<div className="flex items-center justify-between mb-1.5">
							<div className="text-[10.5px] font-semibold uppercase tracking-[0.07em] text-slate-500">Code</div>
							<div className="text-[11px] inline-flex items-center gap-1.5">
								{validating ? (
									<>
										<Spinner size={11} color="#475569" />
										<span className="text-slate-500 font-medium">Validating…</span>
									</>
								) : violations.length === 0 ? (
									<>
										<span className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></span>
										<span className="text-emerald-600 font-medium">AST check passed</span>
									</>
								) : (
									<>
										<span className="w-1.5 h-1.5 bg-rose-500 rounded-full"></span>
										<span className="text-rose-600 font-medium">{violations.length} violation(s)</span>
									</>
								)}
							</div>
						</div>
						<div className="border border-slate-200 rounded-md overflow-hidden" style={{ height: optionsOpen ? 460 : 640 }}>
							<Editor
								height="100%"
								defaultLanguage="python"
								theme="vs-dark"
								value={code}
								onChange={(v) => setCode(v ?? '')}
								options={{
									minimap: { enabled: false },
									fontSize: 13,
									lineHeight: 22,
									tabSize: 4,
									insertSpaces: true,
									lineNumbers: 'on',
									scrollBeyondLastLine: true,
									automaticLayout: true,
									padding: { top: 12, bottom: 12 },
									smoothScrolling: true,
									cursorBlinking: 'smooth',
									cursorSmoothCaretAnimation: 'on',
									mouseWheelScrollSensitivity: 1,
									fastScrollSensitivity: 5,
								}}
							/>
						</div>
						{violations.length > 0 && (
							<div className="mt-2 border border-amber-200 bg-amber-50 rounded-md p-2.5 text-[12px] text-amber-800">
								{violations.slice(0, 5).map((v, i) => (
									<div key={i}>
										<span className="font-mono text-amber-600 mr-2">L{v.line}</span>
										<span className="font-mono mr-2">{v.code}</span>
										{v.message}
									</div>
								))}
								{violations.length > 5 && <div className="text-amber-600 mt-1">…and {violations.length - 5} more</div>}
							</div>
						)}
					</div>

					{/* Helpers cheatsheet */}
					<div className="mt-4">
						<div className="flex items-center justify-between mb-1.5">
							<div className="flex items-center gap-2">
								<div className="text-[10.5px] font-semibold uppercase tracking-[0.07em] text-slate-500">Available helpers</div>
								<span className="font-mono text-[11px] text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded font-medium">from zango import codexec</span>
							</div>
							<span className="text-[11px] text-slate-500">{HELPERS.length} functions</span>
						</div>
						<div className="bg-slate-50 border border-slate-200 rounded-md p-3">
							<div className="grid grid-cols-2 gap-x-4 gap-y-0">
								{HELPERS.map((h) => (
									<div key={h.sig} className="py-1 border-b border-slate-200 last:border-0 even:border-b first:border-t-0 flex items-baseline justify-between gap-2">
										<span className="font-mono text-[11px] text-slate-900">
											{h.sig.split(/(\.[a-z_]+)/).map((part, i) => {
												if (part.startsWith('.') && i > 0) {
													return (
														<strong key={i} className={h.kind === 'write' ? 'text-emerald-600' : 'text-indigo-600'}>
															{part}
														</strong>
													);
												}
												return <React.Fragment key={i}>{part}</React.Fragment>;
											})}
										</span>
										<span className="text-[10.5px] text-slate-500 font-mono">{h.ret}</span>
									</div>
								))}
							</div>
							<div className="mt-2 pt-2 border-t border-slate-200 flex gap-3 text-[10.5px] text-slate-500">
								<span className="inline-flex items-center gap-1"><span className="w-1.5 h-1.5 bg-indigo-500 rounded-full"></span>Read inputs</span>
								<span className="inline-flex items-center gap-1"><span className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></span>Write outputs (registered as CodeExecFile)</span>
							</div>
						</div>
					</div>
				</div>

				{/* Foot */}
				<div className="flex items-center justify-between px-5 py-3.5 border-t border-slate-200 bg-slate-50">
					<div className="flex items-center gap-3 text-[12px] text-slate-500">
						<span>Timeout: <span className="font-medium text-slate-900">{timeoutSeconds}s</span></span>
						<span className="inline-flex gap-1 items-center">Save <kbd className="font-mono text-[10.5px] px-1.5 py-0.5 bg-white border border-slate-300 rounded">⌘</kbd><kbd className="font-mono text-[10.5px] px-1.5 py-0.5 bg-white border border-slate-300 rounded">S</kbd></span>
						<span className="inline-flex gap-1 items-center">Save &amp; Run <kbd className="font-mono text-[10.5px] px-1.5 py-0.5 bg-white border border-slate-300 rounded">⌘</kbd><kbd className="font-mono text-[10.5px] px-1.5 py-0.5 bg-white border border-slate-300 rounded">↵</kbd></span>
					</div>
					<div className="flex gap-2">
						<button onClick={requestClose} disabled={saving} className="px-3.5 h-9 rounded-md text-[12.5px] font-medium text-slate-700 hover:bg-slate-200 transition-colors disabled:opacity-50">Cancel</button>
						<button
							onClick={() => handleSave(false)}
							disabled={saving}
							className="px-3.5 h-9 rounded-md text-[12.5px] font-medium bg-white border border-slate-300 text-slate-800 hover:border-slate-400 disabled:opacity-60 transition-all active:scale-[0.98] inline-flex items-center gap-1.5"
						>
							{saving && <Spinner size={12} color="#475569" />}
							{saving ? 'Saving…' : 'Save'}
						</button>
						<button
							onClick={() => handleSave(true)}
							disabled={saving}
							className="px-3.5 h-9 rounded-md text-[12.5px] font-medium bg-emerald-600 text-white hover:bg-emerald-700 shadow-sm disabled:opacity-60 transition-all active:scale-[0.98] inline-flex items-center gap-1.5"
						>
							{saving ? <Spinner size={12} color="#fff" /> : <span style={{ fontSize: 11 }}>▸</span>}
							{saving ? 'Running…' : 'Save & Run'}
						</button>
					</div>
				</div>
			</div>

			<ConfirmModal
				open={Boolean(confirmRemoveFile)}
				title="Remove this file?"
				description={confirmRemoveFile
					? `"${confirmRemoveFile.name}" will be removed from this snippet. Past runs that used it will still show it in their history.`
					: ''}
				confirmLabel="Remove"
				confirmTone="danger"
				onCancel={() => setConfirmRemoveFile(null)}
				onConfirm={confirmedRemoveExistingFile}
			/>
		</div>
	);

	return createPortal(modalContent, document.body);
}
