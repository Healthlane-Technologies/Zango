import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import useApi from '../../hooks/useApi';

/**
 * Compact Export button that lives next to a list-page search box.
 *
 * Props:
 *   kind        one of "app_users" | "access_logs" | "audit_logs_app" | "audit_logs_framework"
 *   filters     object; POSTed verbatim as `filters` payload
 *   className   optional wrapper class
 */
export default function ExportButton({ kind, filters, className = '' }) {
	const { appId } = useParams();
	const triggerApi = useApi();
	const [submitting, setSubmitting] = useState(false);

	const handleClick = async () => {
		if (submitting) return;
		setSubmitting(true);
		try {
			const { response, success, responseStatus } = await triggerApi({
				url: `/api/v1/apps/${appId}/exports/${kind}/`,
				type: 'POST',
				payload: { filters: filters || {} },
				loader: false,
				showErrorModal: false,
			});

			if (success && response) {
				toast.success(
					response.message ||
						'Export queued. Track it in My Downloads.'
				);
				return;
			}

			const msg =
				response?.message ||
				(responseStatus === 409
					? 'An export of this kind is already in progress. Check My Downloads.'
					: 'Could not start export.');
			toast.error(msg);
		} catch (err) {
			toast.error('Could not start export.');
		} finally {
			setSubmitting(false);
		}
	};

	return (
		<button
			type="button"
			onClick={handleClick}
			disabled={submitting}
			data-cy={`export_${kind}`}
			title="Export current view as CSV"
			className={`inline-flex items-center gap-[8px] whitespace-nowrap rounded-[8px] border border-[#D4D8E5] bg-white px-[14px] py-[8px] font-lato text-[13px] font-semibold text-[#26210F] transition-colors hover:bg-[#F0F3F4] disabled:opacity-50 ${className}`}
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
				<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
				<polyline points="7 10 12 15 17 10" />
				<line x1="12" y1="15" x2="12" y2="3" />
			</svg>
			{submitting ? 'Queuing…' : 'Export CSV'}
		</button>
	);
}
