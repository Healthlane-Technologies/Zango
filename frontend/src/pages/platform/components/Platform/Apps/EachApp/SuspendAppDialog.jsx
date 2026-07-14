import { useEffect, useRef, useState } from 'react';
import toast from 'react-hot-toast';
import useApi from '../../../../../../hooks/useApi';

/**
 * SuspendAppDialog — type-to-confirm modal.
 *
 * Requires the operator to type the app name exactly before the Suspend
 * button enables — same pattern GitHub uses for destructive repo actions.
 * The 2s of extra friction essentially eliminates accidental suspensions.
 *
 * Data preservation is stated inline so anxious admins don't panic.
 */
export default function SuspendAppDialog({ app, onClose, onSuspended }) {
	const triggerApi = useApi();
	const [typedName, setTypedName] = useState('');
	const [busy, setBusy] = useState(false);
	const inputRef = useRef(null);

	const matches = typedName.trim() === app?.name;

	useEffect(() => {
		// Focus the input on mount so the operator can type immediately.
		inputRef.current?.focus();
	}, []);

	useEffect(() => {
		const onKey = (e) => {
			if (e.key === 'Escape') onClose();
		};
		window.addEventListener('keydown', onKey);
		return () => window.removeEventListener('keydown', onKey);
	}, [onClose]);

	const handleSuspend = async () => {
		if (!matches || busy) return;
		setBusy(true);
		const { success, response } = await triggerApi({
			url: `/api/v1/platform/apps/${app.uuid}/status/suspend/`,
			type: 'POST',
			loader: false,
			showErrorModal: false,
		});
		setBusy(false);
		if (success) {
			toast.success(`Suspended "${app.name}"`);
			onSuspended?.(response?.tenant);
			onClose();
		} else {
			toast.error(response?.message || 'Failed to suspend app');
		}
	};

	return (
		<div
			className="fixed inset-0 z-50 flex items-center justify-center px-[16px]"
			style={{ backgroundColor: 'rgba(15,19,36,0.42)' }}
			onClick={onClose}
			role="dialog"
			aria-modal="true"
		>
			<div
				className="w-full max-w-[460px] rounded-[14px] bg-white p-[28px] shadow-[0_20px_60px_-16px_rgba(15,19,36,0.35)]"
				onClick={(e) => e.stopPropagation()}
			>
				{/* Icon */}
				<div
					className="mb-[16px] grid h-[44px] w-[44px] place-items-center rounded-[10px] border"
					style={{
						backgroundColor: '#FEF6E7',
						borderColor: 'rgba(218,144,17,0.28)',
						color: '#8A5A07',
					}}
				>
					<svg
						width="20"
						height="20"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						strokeWidth="2"
						strokeLinecap="round"
						strokeLinejoin="round"
					>
						<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
						<line x1="12" y1="9" x2="12" y2="13" />
						<line x1="12" y1="17" x2="12.01" y2="17" />
					</svg>
				</div>

				<h2
					className="font-source-sans-pro text-[18px] font-semibold text-[#0B0D14]"
					style={{ letterSpacing: '-0.012em' }}
				>
					Suspend "{app.name}"?
				</h2>
				<p className="mt-[6px] font-lato text-[13px] leading-[1.55] text-[#5A607A]">
					All traffic to <strong className="text-[#0B0D14]">{app.domain_url || app.name}</strong>{' '}
					will be blocked with a support-contact message. Panel-scheduled tasks will pause. Your data
					is preserved and can be restored anytime by unsuspending.
				</p>

				<label className="mt-[18px] block">
					<span className="mb-[6px] block font-lato text-[10.5px] font-semibold uppercase tracking-[0.06em] text-[#8389A3]">
						Type the app name to confirm
					</span>
					<input
						ref={inputRef}
						type="text"
						value={typedName}
						onChange={(e) => setTypedName(e.target.value)}
						placeholder={app.name}
						className="w-full rounded-[8px] border border-[#D4D8E5] bg-[#F0F2F7] px-[12px] py-[8px] font-mono text-[13px] text-[#2C3047] outline-none transition-colors focus:border-[#5961E5] focus:bg-white"
					/>
				</label>

				<div className="mt-[20px] flex justify-end gap-[10px]">
					<button
						type="button"
						onClick={onClose}
						className="rounded-[8px] border border-[#D4D8E5] bg-white px-[16px] py-[8px] font-lato text-[13px] font-medium text-[#2C3047] transition-colors hover:bg-[#F0F2F7]"
					>
						Cancel
					</button>
					<button
						type="button"
						onClick={handleSuspend}
						disabled={!matches || busy}
						className="rounded-[8px] px-[16px] py-[8px] font-lato text-[13px] font-medium text-white transition-opacity disabled:cursor-not-allowed disabled:opacity-40"
						style={{
							backgroundColor: '#DA9011',
							boxShadow: '0 2px 6px -1px rgba(218,144,17,0.4)',
						}}
					>
						{busy ? 'Suspending…' : 'Suspend app'}
					</button>
				</div>
			</div>
		</div>
	);
}
