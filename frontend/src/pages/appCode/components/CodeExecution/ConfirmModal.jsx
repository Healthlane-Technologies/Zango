import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';

/** A small confirmation dialog. Replaces window.confirm.
 *
 * Props:
 *   open: bool
 *   title: string
 *   description: string
 *   confirmLabel: string ("Confirm" default)
 *   confirmTone: 'danger' | 'primary' (default 'primary')
 *   onCancel: () => void
 *   onConfirm: () => void
 */
export default function ConfirmModal({
	open,
	title,
	description,
	confirmLabel = 'Confirm',
	cancelLabel = 'Cancel',
	confirmTone = 'primary',
	onCancel,
	onConfirm,
}) {
	const [mounted, setMounted] = useState(false);

	useEffect(() => {
		if (!open) { setMounted(false); return; }
		// Tick to allow CSS transition to fire on first paint.
		const t = setTimeout(() => setMounted(true), 10);
		return () => clearTimeout(t);
	}, [open]);

	useEffect(() => {
		if (!open) return;
		const onKey = (e) => {
			if (e.key === 'Escape') onCancel?.();
			if (e.key === 'Enter') onConfirm?.();
		};
		window.addEventListener('keydown', onKey);
		return () => window.removeEventListener('keydown', onKey);
	}, [open, onCancel, onConfirm]);

	if (!open) return null;

	const confirmClasses =
		confirmTone === 'danger'
			? 'bg-rose-600 hover:bg-rose-700 text-white shadow-sm'
			: 'bg-[#346BD4] hover:bg-[#2557C0] text-white shadow-sm';

	const content = (
		<div
			className={`fixed inset-0 z-[1100] flex items-center justify-center p-6 bg-slate-900/55 backdrop-blur-[2px] transition-opacity duration-200 ease-out ${mounted ? 'opacity-100' : 'opacity-0'}`}
			onMouseDown={(e) => { if (e.target === e.currentTarget) onCancel?.(); }}
		>
			<div
				className={`bg-white rounded-xl shadow-2xl w-full max-w-[440px] overflow-hidden transition-all duration-200 ease-out ${mounted ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-1 scale-[0.985]'}`}
				role="dialog"
				aria-modal="true"
			>
				<div className="px-5 py-4">
					<div className="text-[15px] font-semibold text-slate-900 mb-1">{title}</div>
					<div className="text-[13px] text-slate-600 leading-relaxed">{description}</div>
				</div>
				<div className="flex items-center justify-end gap-2 px-5 py-3 bg-slate-50 border-t border-slate-200">
					<button
						onClick={onCancel}
						className="px-3.5 h-9 rounded-md text-[12.5px] font-medium text-slate-700 hover:bg-slate-200 transition-colors"
					>
						{cancelLabel}
					</button>
					<button
						onClick={onConfirm}
						className={`px-3.5 h-9 rounded-md text-[12.5px] font-medium transition-colors ${confirmClasses}`}
					>
						{confirmLabel}
					</button>
				</div>
			</div>
		</div>
	);

	return createPortal(content, document.body);
}
