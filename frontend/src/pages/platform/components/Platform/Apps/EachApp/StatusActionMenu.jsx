import { useEffect, useRef, useState } from 'react';
import toast from 'react-hot-toast';
import useApi from '../../../../../../hooks/useApi';
import SuspendAppDialog from './SuspendAppDialog';

/**
 * StatusActionMenu — kebab menu floated onto each app card.
 *
 * Placed at the card's top-right corner. Clicking the kebab stops
 * propagation so the underlying <Link> doesn't navigate. Menu contents
 * are dependent on the current status:
 *   - deployed → "Suspend app" (opens type-to-confirm dialog)
 *   - suspended → "Unsuspend app" (fires immediately — resuming is low-risk)
 */
export default function StatusActionMenu({ app, onStatusChanged }) {
	const triggerApi = useApi();
	const [open, setOpen] = useState(false);
	const [dialogOpen, setDialogOpen] = useState(false);
	const [busy, setBusy] = useState(false);
	const menuRef = useRef(null);

	// Close on outside click.
	useEffect(() => {
		if (!open) return undefined;
		const onDoc = (e) => {
			if (menuRef.current && !menuRef.current.contains(e.target)) setOpen(false);
		};
		document.addEventListener('mousedown', onDoc);
		return () => document.removeEventListener('mousedown', onDoc);
	}, [open]);

	const stop = (e) => {
		e.preventDefault();
		e.stopPropagation();
	};

	const openSuspend = (e) => {
		stop(e);
		setOpen(false);
		setDialogOpen(true);
	};

	const handleUnsuspend = async (e) => {
		stop(e);
		setOpen(false);
		if (busy) return;
		setBusy(true);
		const { success, response } = await triggerApi({
			url: `/api/v1/apps/${app.uuid}/status/unsuspend/`,
			type: 'POST',
			loader: false,
			showErrorModal: false,
		});
		setBusy(false);
		if (success) {
			toast.success(`Unsuspended "${app.name}"`);
			onStatusChanged?.(response?.tenant);
		} else {
			toast.error(response?.message || 'Failed to unsuspend app');
		}
	};

	const isSuspended = app.status === 'suspended';

	return (
		<>
			<div
				ref={menuRef}
				className="absolute right-[10px] top-[10px] z-[2]"
				onClick={stop}
			>
				<button
					type="button"
					aria-label="App actions"
					onClick={(e) => {
						stop(e);
						setOpen((v) => !v);
					}}
					className="grid h-[28px] w-[28px] place-items-center rounded-[6px] border border-transparent bg-white/70 backdrop-blur-sm text-[#5A607A] transition-colors hover:border-[#DDE2E5] hover:bg-white hover:text-[#0B0D14]"
				>
					<svg
						width="14"
						height="14"
						viewBox="0 0 24 24"
						fill="currentColor"
					>
						<circle cx="5" cy="12" r="1.6" />
						<circle cx="12" cy="12" r="1.6" />
						<circle cx="19" cy="12" r="1.6" />
					</svg>
				</button>
				{open && (
					<div className="absolute right-0 top-[32px] min-w-[176px] rounded-[8px] border border-[#DDE2E5] bg-white py-[4px] shadow-[0_8px_24px_-8px_rgba(15,19,36,0.18)]">
						{isSuspended ? (
							<button
								type="button"
								onClick={handleUnsuspend}
								disabled={busy}
								className="flex w-full items-center gap-[10px] px-[12px] py-[8px] font-lato text-[13px] text-[#3938B5] transition-colors hover:bg-[#EEF1FE] disabled:cursor-not-allowed disabled:opacity-40"
							>
								<svg
									width="14"
									height="14"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									strokeWidth="2"
									strokeLinecap="round"
									strokeLinejoin="round"
								>
									<polygon points="5 3 19 12 5 21 5 3" />
								</svg>
								Unsuspend app
							</button>
						) : (
							<button
								type="button"
								onClick={openSuspend}
								className="flex w-full items-center gap-[10px] px-[12px] py-[8px] font-lato text-[13px] text-[#8A5A07] transition-colors hover:bg-[#FEF6E7]"
							>
								<svg
									width="14"
									height="14"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									strokeWidth="2"
									strokeLinecap="round"
									strokeLinejoin="round"
								>
									<rect x="6" y="4" width="4" height="16" />
									<rect x="14" y="4" width="4" height="16" />
								</svg>
								Suspend app
							</button>
						)}
					</div>
				)}
			</div>

			{dialogOpen && (
				<SuspendAppDialog
					app={app}
					onClose={() => setDialogOpen(false)}
					onSuspended={onStatusChanged}
				/>
			)}
		</>
	);
}
