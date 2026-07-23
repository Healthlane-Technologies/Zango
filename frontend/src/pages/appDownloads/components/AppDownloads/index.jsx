import React, { useCallback, useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import BreadCrumbs from '../../../app/components/BreadCrumbs';
import useApi from '../../../../hooks/useApi';
import {
	selectAppDownloadsData,
	setAppDownloadsData,
} from '../../slice';

// Match backend ExportKind labels
const KIND_LABEL = {
	app_users: 'App Users',
	access_logs: 'Access Logs',
	audit_logs_app: 'Application Audit Logs',
	audit_logs_framework: 'Framework Audit Logs',
};

const KIND_ICON_COLOR = {
	app_users: 'from-[#5961E5] to-[#3938B5]',
	access_logs: 'from-[#DA9011] to-[#B87608]',
	audit_logs_app: 'from-[#119C85] to-[#0D6555]',
	audit_logs_framework: 'from-[#119C85] to-[#0D6555]',
};

const STATUS_STYLE = {
	queued: {
		text: 'Queued',
		bg: 'bg-[#F4F5F8]',
		fg: 'text-[#3D4159]',
		dot: 'bg-[#6E748D]',
	},
	running: {
		text: 'Running',
		bg: 'bg-[#FEF6E7]',
		fg: 'text-[#8A5A07]',
		dot: 'bg-[#DA9011] animate-pulse',
	},
	success: {
		text: 'Success',
		bg: 'bg-[#EFF7EE]',
		fg: 'text-[#36713A]',
		dot: 'bg-[#5AA45B]',
	},
	failed: {
		text: 'Failed',
		bg: 'bg-[#FCEDEF]',
		fg: 'text-[#931F2A]',
		dot: 'bg-[#D3424E]',
	},
};

function formatBytes(n) {
	if (!n && n !== 0) return '—';
	if (n < 1024) return `${n} B`;
	if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
	if (n < 1024 * 1024 * 1024) return `${(n / (1024 * 1024)).toFixed(1)} MB`;
	return `${(n / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

function formatDateTime(iso) {
	if (!iso) return '';
	try {
		const d = new Date(iso);
		return d.toLocaleString([], {
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit',
		});
	} catch (e) {
		return iso;
	}
}

function StatusPill({ status }) {
	const style = STATUS_STYLE[status] || STATUS_STYLE.queued;
	return (
		<span
			className={`inline-flex items-center gap-[6px] rounded-full px-[9px] py-[3px] font-lato text-[10.5px] font-semibold uppercase tracking-[0.06em] ${style.bg} ${style.fg}`}
		>
			<span className={`h-[5px] w-[5px] rounded-full ${style.dot}`} />
			{style.text}
		</span>
	);
}

function KindIcon({ kind }) {
	const letter = KIND_LABEL[kind]?.[0] || '?';
	const gradient =
		KIND_ICON_COLOR[kind] || 'from-[#5961E5] to-[#3938B5]';
	return (
		<div
			className={`flex h-[32px] w-[32px] items-center justify-center rounded-[8px] bg-gradient-to-br ${gradient} font-lato text-[14px] font-semibold text-white shadow`}
		>
			{letter}
		</div>
	);
}

function DownloadIcon() {
	return (
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
	);
}

function TrashIcon() {
	return (
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
			<polyline points="3 6 5 6 21 6" />
			<path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
			<path d="M10 11v6M14 11v6" />
		</svg>
	);
}

function InfoIcon() {
	return (
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
			<circle cx="12" cy="12" r="10" />
			<line x1="12" y1="8" x2="12" y2="12" />
			<line x1="12" y1="16" x2="12.01" y2="16" />
		</svg>
	);
}

function RefreshIcon() {
	return (
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
			<polyline points="23 4 23 10 17 10" />
			<path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
		</svg>
	);
}

export default function AppDownloads() {
	const { appId } = useParams();
	const triggerApi = useApi();
	const dispatch = useDispatch();
	const data = useSelector(selectAppDownloadsData);

	const [loading, setLoading] = useState(false);
	const [errorJob, setErrorJob] = useState(null);

	const fetchJobs = useCallback(async () => {
		setLoading(true);
		try {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/exports/?page=1&page_size=50`,
				type: 'GET',
				loader: false,
			});
			if (success && response) {
				dispatch(setAppDownloadsData(response));
			}
		} finally {
			setLoading(false);
		}
	}, [appId, dispatch, triggerApi]);

	useEffect(() => {
		fetchJobs();
	}, [fetchJobs]);

	const handleDelete = async (job) => {
		const label =
			job.status === 'running' || job.status === 'queued'
				? 'Cancel this export?'
				: 'Delete this export?';
		if (!window.confirm(label)) return;
		const { success, response } = await triggerApi({
			url: `/api/v1/apps/${appId}/exports/job/${job.object_uuid}/`,
			type: 'DELETE',
			loader: false,
			showErrorModal: false,
		});
		if (success) {
			toast.success(response?.message || 'Export deleted');
			fetchJobs();
		} else {
			toast.error(response?.message || 'Could not delete');
		}
	};

	const handleDownload = (job) => {
		if (job.status !== 'success' || !job.file_url) return;
		// Same-origin (dev): the `download` attribute forces the filename.
		// S3: the presigned URL already carries response-content-disposition=
		// attachment so the browser downloads instead of rendering inline.
		const a = document.createElement('a');
		a.href = job.file_url;
		a.download = job.filename || 'export.csv';
		a.rel = 'noopener noreferrer';
		document.body.appendChild(a);
		a.click();
		a.remove();
	};

	const jobs = data?.exports?.records || [];

	return (
		<div className="flex grow flex-col overflow-hidden">
			{/* Header */}
			<div className="flex items-center justify-between py-[12px] pl-[40px] pr-[48px]">
				<BreadCrumbs />
			</div>

			<div className="flex grow flex-col overflow-y-auto px-[40px] pb-[40px]">
				<div className="rounded-[12px] border border-[#E3E6EF] bg-white shadow-sm">
					{/* Panel header */}
					<div className="flex items-start justify-between gap-[14px] border-b border-[#ECEEF5] px-[24px] py-[20px]">
						<div>
							<h1 className="font-source-sans-pro text-[20px] font-semibold leading-[28px] tracking-[-0.015em] text-[#0B0D14]">
								My Downloads
							</h1>
							<p className="mt-[4px] font-lato text-[13px] leading-[18px] text-[#5A607A]">
								Exports you've requested from list pages · newest
								first · click{' '}
								<span className="inline-flex items-center gap-[3px] text-[#3938B5]">
									<RefreshIcon /> Refresh
								</span>{' '}
								to check for updates
							</p>
						</div>
						<button
							type="button"
							onClick={fetchJobs}
							disabled={loading}
							className="inline-flex items-center gap-[8px] rounded-[8px] border border-[#D4D8E5] bg-white px-[14px] py-[8px] font-lato text-[13px] font-medium text-[#2C3047] transition-colors hover:bg-[#F0F2F7] disabled:opacity-50"
						>
							<RefreshIcon />
							{loading ? 'Refreshing…' : 'Refresh'}
						</button>
					</div>

					{/* Table header */}
					<div className="grid grid-cols-[160px_1fr_150px_120px_100px_120px] items-center gap-[16px] bg-[#F0F2F7] px-[24px] py-[10px] font-lato text-[10px] font-semibold uppercase tracking-[0.09em] text-[#8389A3]">
						<div>Kind</div>
						<div>Filters</div>
						<div>Requested</div>
						<div>Status</div>
						<div>Size</div>
						<div className="text-right">Actions</div>
					</div>

					{/* Rows */}
					{jobs.length === 0 ? (
						<div className="px-[24px] py-[48px] text-center font-lato text-[13px] text-[#8389A3]">
							{loading
								? 'Loading…'
								: 'No exports yet. Click Export CSV on App Users, Access Logs, or Audit Logs to start one.'}
						</div>
					) : (
						jobs.map((job) => (
							<div
								key={job.object_uuid}
								className="grid grid-cols-[160px_1fr_150px_120px_100px_120px] items-center gap-[16px] border-b border-[#ECEEF5] px-[24px] py-[14px] last:border-b-0"
							>
								<div className="flex items-center gap-[10px]">
									<KindIcon kind={job.kind} />
									<div>
										<div className="font-lato text-[13px] font-semibold leading-[18px] tracking-[-0.005em] text-[#0B0D14]">
											{KIND_LABEL[job.kind] || job.kind_label || job.kind}
										</div>
										<div className="mt-[2px] font-mono text-[11px] text-[#8389A3]">
											{job.row_count != null
												? `${job.row_count.toLocaleString()} rows`
												: '—'}
										</div>
									</div>
								</div>
								<div
									className="overflow-hidden font-lato text-[12.5px] leading-[1.45] text-[#2C3047]"
									title={job.filters_summary}
								>
									{job.filters_summary || 'no filter'}
								</div>
								<div className="font-lato text-[12.5px] text-[#2C3047]">
									{formatDateTime(job.created_at)}
								</div>
								<div>
									<StatusPill status={job.status} />
								</div>
								<div className="font-mono text-[12.5px] text-[#2C3047]">
									{job.status === 'success'
										? formatBytes(job.size_bytes)
										: '—'}
								</div>
								<div className="flex items-center justify-end gap-[6px]">
									{job.status === 'failed' ? (
										<button
											type="button"
											onClick={() => setErrorJob(job)}
											title="View error details"
											className="grid h-[30px] w-[30px] place-items-center rounded-[6px] border border-[#E3E6EF] bg-white text-[#5A607A] transition-colors hover:border-[#DCE3FD] hover:bg-[#EEF1FE] hover:text-[#3938B5]"
										>
											<InfoIcon />
										</button>
									) : (
										<button
											type="button"
											onClick={() => handleDownload(job)}
											disabled={
												job.status !== 'success' || !job.file_url
											}
											title={
												job.status === 'success'
													? 'Download CSV'
													: 'Available when the job completes'
											}
											className="grid h-[30px] w-[30px] place-items-center rounded-[6px] border border-[#E3E6EF] bg-white text-[#5A607A] transition-colors hover:border-[#DCE3FD] hover:bg-[#EEF1FE] hover:text-[#3938B5] disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-[#E3E6EF] disabled:hover:bg-white disabled:hover:text-[#5A607A]"
										>
											<DownloadIcon />
										</button>
									)}
									<button
										type="button"
										onClick={() => handleDelete(job)}
										title={
											job.status === 'running' || job.status === 'queued'
												? 'Cancel this job'
												: 'Delete this export'
										}
										className="grid h-[30px] w-[30px] place-items-center rounded-[6px] border border-[#E3E6EF] bg-white text-[#5A607A] transition-colors hover:border-[#F8D5D9] hover:bg-[#FCEDEF] hover:text-[#931F2A]"
									>
										<TrashIcon />
									</button>
								</div>
							</div>
						))
					)}
				</div>
			</div>

			{/* Error modal */}
			{errorJob ? (
				<div
					className="fixed inset-0 z-[60] grid place-items-center bg-black/50 px-4"
					onClick={() => setErrorJob(null)}
				>
					<div
						className="w-full max-w-md rounded-[12px] bg-white p-[24px] shadow-2xl"
						onClick={(e) => e.stopPropagation()}
					>
						<h2 className="mb-[8px] font-source-sans-pro text-[18px] font-semibold text-[#0B0D14]">
							Export failed
						</h2>
						<p className="mb-[16px] font-lato text-[13px] text-[#5A607A]">
							{KIND_LABEL[errorJob.kind]} — requested{' '}
							{formatDateTime(errorJob.created_at)}
						</p>
						<div className="max-h-[240px] overflow-y-auto rounded-[6px] bg-[#F4F5F8] p-[12px] font-mono text-[12px] text-[#931F2A]">
							{errorJob.error_message || 'No error message recorded.'}
						</div>
						<div className="mt-[16px] flex justify-end">
							<button
								type="button"
								onClick={() => setErrorJob(null)}
								className="rounded-[8px] bg-[#5961E5] px-[16px] py-[8px] font-lato text-[13px] font-medium text-white hover:bg-[#3938B5]"
							>
								Close
							</button>
						</div>
					</div>
				</div>
			) : null}
		</div>
	);
}
