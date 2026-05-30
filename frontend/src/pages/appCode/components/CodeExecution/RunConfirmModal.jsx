import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';

/** Run confirmation dialog with a read-only code preview.
 *
 * Props:
 *   open: boolean
 *   title: string                 (e.g. "Run latest code" or "Re-run v3")
 *   subtitle: string              (e.g. snippet name)
 *   code: string                  (the source that will run)
 *   version: number | null
 *   sourceHash: string | null
 *   loading: bool                 (the fetch / submit state)
 *   onCancel: () => void
 *   onConfirm: () => void
 */
export default function RunConfirmModal({
	open,
	title,
	subtitle,
	code,
	version,
	sourceHash,
	loading = false,
	onCancel,
	onConfirm,
}) {
	const [mounted, setMounted] = useState(false);

	useEffect(() => {
		if (!open) { setMounted(false); return; }
		const t = setTimeout(() => setMounted(true), 10);
		// Lock body scroll while open
		const prev = document.body.style.overflow;
		document.body.style.overflow = 'hidden';
		return () => {
			clearTimeout(t);
			document.body.style.overflow = prev;
		};
	}, [open]);

	useEffect(() => {
		if (!open) return;
		const onKey = (e) => {
			if (e.key === 'Escape') onCancel?.();
			if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') onConfirm?.();
		};
		window.addEventListener('keydown', onKey);
		return () => window.removeEventListener('keydown', onKey);
	}, [open, onCancel, onConfirm]);

	if (!open) return null;

	const lineCount = (code || '').split('\n').length;
	const sizeKb = ((code || '').length / 1024).toFixed(1);

	const content = (
		<div
			className={`fixed inset-0 z-[1100] flex items-center justify-center p-6 bg-slate-900/60 backdrop-blur-[3px] transition-opacity duration-200 ease-out ${mounted ? 'opacity-100' : 'opacity-0'}`}
			onMouseDown={(e) => { if (e.target === e.currentTarget) onCancel?.(); }}
			role="dialog"
			aria-modal="true"
		>
			<div
				className={`bg-white rounded-2xl shadow-2xl w-full max-w-[820px] overflow-hidden flex flex-col transition-all duration-200 ease-out ${mounted ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-2 scale-[0.985]'}`}
			>
				{/* Head */}
				<div className="px-5 py-4 border-b border-slate-200 bg-gradient-to-b from-slate-50 to-white">
					<div className="flex items-center justify-between">
						<div className="flex items-center gap-2.5 min-w-0">
							<div className="w-8 h-8 bg-emerald-50 text-emerald-700 rounded-md grid place-items-center font-mono text-[13px] font-bold flex-shrink-0">▸</div>
							<div className="min-w-0">
								<div className="text-[14px] font-semibold text-slate-900 truncate">{title}</div>
								{subtitle && <div className="text-[12px] text-slate-500 truncate">{subtitle}</div>}
							</div>
						</div>
						<button
							onClick={onCancel}
							className="w-7 h-7 grid place-items-center rounded text-slate-500 hover:bg-slate-100 transition-colors flex-shrink-0"
						>
							<span style={{ fontSize: 18, lineHeight: 1 }}>×</span>
						</button>
					</div>
					{(version != null || sourceHash) && (
						<div className="flex items-center gap-2 mt-2 text-[11px] text-slate-500">
							{version != null && (
								<span className="px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 font-medium">
									v{version}
								</span>
							)}
							{sourceHash && (
								<span className="font-mono text-slate-400">{sourceHash.slice(0, 12)}</span>
							)}
							<span className="text-slate-400">·</span>
							<span>{lineCount} line{lineCount !== 1 ? 's' : ''}</span>
							<span className="text-slate-400">·</span>
							<span>{sizeKb} KB</span>
						</div>
					)}
				</div>

				{/* Body — code preview */}
				<div className="px-5 py-4 bg-white">
					<div className="text-[10.5px] font-semibold uppercase tracking-[0.08em] text-slate-500 mb-2">
						Code to run
					</div>
					<div className="border border-slate-200 rounded-md overflow-hidden bg-[#0F1117]">
						<pre
							className="font-mono text-[12px] text-slate-200 leading-[1.65] p-4 overflow-auto whitespace-pre"
							style={{ maxHeight: 420 }}
						>
							{code || '(empty)'}
						</pre>
					</div>
				</div>

				{/* Foot */}
				<div className="flex items-center justify-between px-5 py-3.5 border-t border-slate-200 bg-slate-50">
					<div className="flex items-center gap-3 text-[11px] text-slate-500">
						<span className="inline-flex items-center gap-1">Confirm <kbd className="font-mono text-[10px] px-1.5 py-0.5 bg-white border border-slate-300 rounded">⌘</kbd><kbd className="font-mono text-[10px] px-1.5 py-0.5 bg-white border border-slate-300 rounded">↵</kbd></span>
						<span className="inline-flex items-center gap-1">Cancel <kbd className="font-mono text-[10px] px-1.5 py-0.5 bg-white border border-slate-300 rounded">Esc</kbd></span>
					</div>
					<div className="flex gap-2">
						<button
							onClick={onCancel}
							disabled={loading}
							className="px-3.5 h-9 rounded-md text-[12.5px] font-medium text-slate-700 hover:bg-slate-200 disabled:opacity-50 transition-colors"
						>
							Cancel
						</button>
						<button
							onClick={onConfirm}
							disabled={loading || !code}
							className="px-3.5 h-9 rounded-md text-[12.5px] font-medium bg-emerald-600 text-white shadow-sm hover:bg-emerald-700 hover:shadow disabled:opacity-50 transition-all active:scale-[0.98] inline-flex items-center gap-1.5"
						>
							{loading ? (
								<>
									<span className="inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
									Running…
								</>
							) : (
								<>
									<span style={{ fontSize: 11 }}>▸</span> Run
								</>
							)}
						</button>
					</div>
				</div>
			</div>
		</div>
	);

	return createPortal(content, document.body);
}
