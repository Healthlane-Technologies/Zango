import { useEffect, useMemo, useState } from 'react';
import { createPortal } from 'react-dom';
import useApi from '../../../../hooks/useApi';

const COMPONENT_LABEL = {
	app: 'App',
	celery: 'Celery worker',
	celery_beat: 'Celery beat',
};

const FORMAT_OPTIONS = [
	{ value: 'verbose', label: 'verbose · [schema:domain] prefix' },
	{ value: 'plain', label: 'plain · no tenant prefix' },
	{ value: 'json', label: 'json · structured (future)', disabled: true },
];

const emptyForm = {
	connector: 'cloudwatch',
	config: {
		region: 'ap-south-1',
		log_group_name: '',
		stream_prefix: '',
		format: 'verbose',
		aws_access_key_id: '',
		aws_secret_access_key: '',
		role_arn: '',
	},
	is_active: true,
};

export default function ConnectorEditModal({
	environment,
	component,
	row,
	availableTypes,
	onClose,
	onSaved,
}) {
	const triggerApi = useApi();
	const isEdit = !!row;

	const [form, setForm] = useState(() => {
		if (row) {
			return {
				connector: row.connector,
				config: {
					region: row.config?.region || '',
					log_group_name: row.config?.log_group_name || '',
					stream_prefix: row.config?.stream_prefix || '',
					format: row.config?.format || 'verbose',
					// Server masks the key (last 4 chars only) and blanks the secret.
					// Both forms are recognized as "no change" on save.
					aws_access_key_id: row.config?.aws_access_key_id || '',
					aws_secret_access_key: '',
					role_arn: row.config?.role_arn || '',
				},
				is_active: row.is_active ?? true,
			};
		}
		return emptyForm;
	});

	const [testStatus, setTestStatus] = useState(null); // { ok, stream_count, error }
	const [saving, setSaving] = useState(false);
	const [errors, setErrors] = useState(null);

	useEffect(() => {
		const onKey = (e) => {
			if (e.key === 'Escape') onClose();
		};
		document.addEventListener('keydown', onKey);
		return () => document.removeEventListener('keydown', onKey);
	}, [onClose]);

	const updateConfig = (key, value) =>
		setForm((f) => ({ ...f, config: { ...f.config, [key]: value } }));

	const payload = useMemo(() => {
		const config = { ...form.config };
		if (!config.stream_prefix) delete config.stream_prefix;
		if (!config.role_arn) delete config.role_arn;
		// Drop blank auth fields so the server-side merge takes over for
		// "leave blank to keep existing" behaviour on edit.
		if (!config.aws_access_key_id) delete config.aws_access_key_id;
		if (!config.aws_secret_access_key) delete config.aws_secret_access_key;
		return {
			environment,
			component,
			connector: form.connector,
			config,
			is_active: form.is_active,
		};
	}, [environment, component, form]);

	const handleTest = async () => {
		setTestStatus({ pending: true });
		const { response, success } = await triggerApi({
			url: '/api/v1/platform/logs/connectors/test/',
			type: 'POST',
			payload: { connector: payload.connector, config: payload.config },
			loader: false,
			showErrorModal: false,
		});
		if (success && response?.ok) {
			setTestStatus({
				ok: true,
				stream_count: response.stream_count,
				newest_event_ts: response.newest_event_ts,
			});
		} else {
			setTestStatus({
				ok: false,
				error: response?.detail || response?.message || 'Test failed',
			});
		}
	};

	const handleSave = async () => {
		setSaving(true);
		setErrors(null);
		const { response, success, responseStatus } = await triggerApi({
			url: '/api/v1/platform/logs/connectors/',
			type: 'POST',
			payload,
			loader: false,
			showErrorModal: false,
			notify: true,
		});
		setSaving(false);
		if (success || responseStatus === 200 || responseStatus === 201) {
			onSaved();
		} else {
			setErrors(response || { detail: 'Failed to save connector.' });
		}
	};

	return createPortal(
		<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-[20px] animate-modal-backdrop">
			<div className="flex w-full max-w-[680px] flex-col rounded-[14px] bg-white shadow-2xl animate-modal-card">
				<style>{`
					@keyframes modal-backdrop { from { opacity: 0 } to { opacity: 1 } }
					@keyframes modal-card {
						from { opacity: 0; transform: scale(0.97) translateY(8px); }
						to   { opacity: 1; transform: scale(1) translateY(0); }
					}
					.animate-modal-backdrop { animation: modal-backdrop 180ms ease-out both; }
					.animate-modal-card { animation: modal-card 220ms cubic-bezier(0.22, 1, 0.36, 1) both; }
					@media (prefers-reduced-motion: reduce) {
						.animate-modal-backdrop, .animate-modal-card { animation: none; }
					}
				`}</style>
				<header className="flex items-center gap-[10px] border-b border-[#E3E6EF] px-[22px] py-[14px]">
					<h3 className="text-[14.5px] font-semibold text-[#0B0D14]">
						{isEdit ? 'Edit' : 'Configure'} · {COMPONENT_LABEL[component]} connector
					</h3>
					<span className="rounded-full bg-[#EEF1FE] px-[8px] py-[2px] text-[10.5px] font-medium text-[#3938B5]">
						{environment} × {component}
					</span>
					<button
						type="button"
						onClick={onClose}
						className="ml-auto text-[#5A607A] hover:text-[#0B0D14]"
						aria-label="Close"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							width="16"
							height="16"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							strokeWidth="2"
						>
							<line x1="18" y1="6" x2="6" y2="18" />
							<line x1="6" y1="6" x2="18" y2="18" />
						</svg>
					</button>
				</header>

				<div className="grid grid-cols-1 gap-[16px] px-[22px] py-[18px] md:grid-cols-2">
					<Field label="Environment">
						<input
							type="text"
							value={environment}
							disabled
							className="w-full cursor-not-allowed rounded-[8px] border border-[#D4D8E5] bg-[#F0F2F7] px-[10px] py-[6px] text-[12.5px] text-[#5A607A]"
						/>
					</Field>
					<Field label="Component">
						<input
							type="text"
							value={COMPONENT_LABEL[component]}
							disabled
							className="w-full cursor-not-allowed rounded-[8px] border border-[#D4D8E5] bg-[#F0F2F7] px-[10px] py-[6px] text-[12.5px] text-[#5A607A]"
						/>
					</Field>

					<Field label="Connector type" required>
						<select
							value={form.connector}
							onChange={(e) =>
								setForm((f) => ({ ...f, connector: e.target.value }))
							}
							className="w-full rounded-[8px] border border-[#D4D8E5] bg-white px-[10px] py-[6px] text-[12.5px] text-[#0B0D14]"
						>
							{availableTypes.map((t) => (
								<option key={t} value={t}>
									{t}
								</option>
							))}
						</select>
					</Field>

					<Field label="AWS region" required>
						<input
							type="text"
							value={form.config.region}
							onChange={(e) => updateConfig('region', e.target.value)}
							placeholder="ap-south-1"
							className="w-full rounded-[8px] border border-[#D4D8E5] bg-white px-[10px] py-[6px] text-[12.5px] text-[#0B0D14]"
						/>
					</Field>

					<div className="md:col-span-2">
						<Field label="Log group name" required>
							<input
								type="text"
								value={form.config.log_group_name}
								onChange={(e) =>
									updateConfig('log_group_name', e.target.value)
								}
								placeholder="/ecs/zango-india-staging/app"
								className="w-full rounded-[8px] border border-[#D4D8E5] bg-white px-[10px] py-[6px] font-mono text-[12px] text-[#0B0D14]"
							/>
							<Help>Validated when you click "Test connection".</Help>
						</Field>
					</div>

					<Field label="Stream prefix · optional">
						<input
							type="text"
							value={form.config.stream_prefix}
							onChange={(e) => updateConfig('stream_prefix', e.target.value)}
							placeholder="app/app/"
							className="w-full rounded-[8px] border border-[#D4D8E5] bg-white px-[10px] py-[6px] font-mono text-[12px] text-[#0B0D14]"
						/>
						<Help>Restrict reads to streams starting with this prefix.</Help>
					</Field>

					<Field label="Line format">
						<select
							value={form.config.format}
							onChange={(e) => updateConfig('format', e.target.value)}
							className="w-full rounded-[8px] border border-[#D4D8E5] bg-white px-[10px] py-[6px] text-[12.5px] text-[#0B0D14]"
						>
							{FORMAT_OPTIONS.map((opt) => (
								<option key={opt.value} value={opt.value} disabled={opt.disabled}>
									{opt.label}
								</option>
							))}
						</select>
						<Help>Drives the CloudWatch filter pattern for tenant scoping.</Help>
					</Field>

					<div className="md:col-span-2">
						<div className="mb-[8px] flex items-center gap-[10px]">
							<div className="text-[10.5px] font-semibold uppercase tracking-[0.07em] text-[#8389A3]">
								Authentication · optional
							</div>
							<div className="flex-1 border-t border-[#ECEEF5]" />
						</div>
						<div className="mb-[10px] rounded-[8px] border-l-[3px] border-[#5961E5] bg-[#EEF1FE] px-[12px] py-[8px] text-[11.5px] text-[#2C3047]">
							Pick <strong>one</strong> of: explicit access keys, or a Role
							ARN. Leave both blank to use the default AWS credential chain
							(env vars / <span className="font-mono">~/.aws/credentials</span>{' '}
							/ task role).
							{isEdit && (
								<>
									{' '}On edit, leave the secret blank to keep the saved value.
								</>
							)}
						</div>
					</div>

					<Field label="AWS Access Key ID · optional">
						<input
							type="text"
							value={form.config.aws_access_key_id}
							onChange={(e) =>
								updateConfig('aws_access_key_id', e.target.value)
							}
							placeholder="AKIA…"
							autoComplete="off"
							className="w-full rounded-[8px] border border-[#D4D8E5] bg-white px-[10px] py-[6px] font-mono text-[12px] text-[#0B0D14]"
						/>
						<Help>Use together with the secret key below.</Help>
					</Field>

					<Field label="AWS Secret Access Key · optional">
						<input
							type="password"
							value={form.config.aws_secret_access_key}
							onChange={(e) =>
								updateConfig('aws_secret_access_key', e.target.value)
							}
							placeholder={isEdit ? '•••••• (leave blank to keep)' : '••••••'}
							autoComplete="new-password"
							className="w-full rounded-[8px] border border-[#D4D8E5] bg-white px-[10px] py-[6px] font-mono text-[12px] text-[#0B0D14]"
						/>
						<Help>Stored in DB; only this server can read it back.</Help>
					</Field>

					<div className="md:col-span-2 flex items-center gap-[10px] text-[10.5px] uppercase tracking-[0.07em] text-[#8389A3]">
						<div className="flex-1 border-t border-[#ECEEF5]" />
						<span>OR</span>
						<div className="flex-1 border-t border-[#ECEEF5]" />
					</div>

					<div className="md:col-span-2">
						<Field label="Role ARN · cross-account · optional">
							<input
								type="text"
								value={form.config.role_arn}
								onChange={(e) => updateConfig('role_arn', e.target.value)}
								placeholder="arn:aws:iam::123456789012:role/zango-logs-reader"
								className="w-full rounded-[8px] border border-[#D4D8E5] bg-white px-[10px] py-[6px] font-mono text-[12px] text-[#0B0D14]"
							/>
							<Help>
								If set (without keys above), STS AssumeRole before each read
								using the process's default credentials.
							</Help>
						</Field>
					</div>
				</div>

				{errors && (
					<div className="mx-[22px] mb-[12px] rounded-[8px] border border-l-[3px] border-l-[#D3424E] border-[#F8D5D9] bg-[#FCEDEF] p-[10px] text-[12px] text-[#931F2A]">
						<strong>Could not save.</strong>{' '}
						{typeof errors === 'string'
							? errors
							: errors.detail ||
							  (errors.config &&
									(Array.isArray(errors.config)
										? errors.config.join(' ')
										: errors.config)) ||
							  JSON.stringify(errors)}
					</div>
				)}

				<footer className="flex items-center gap-[10px] rounded-b-[14px] border-t border-[#E3E6EF] bg-[#FAFBFD] px-[22px] py-[12px]">
					<button
						type="button"
						onClick={handleTest}
						className="inline-flex items-center gap-[6px] rounded-[8px] border border-[#D4D8E5] bg-white px-[11px] py-[5px] text-[12px] font-medium text-[#2C3047] hover:bg-[#F0F2F7]"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							width="13"
							height="13"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							strokeWidth="2"
						>
							<polyline points="20 6 9 17 4 12" />
						</svg>
						Test connection
					</button>
					{testStatus?.pending && (
						<span className="text-[11.5px] text-[#5A607A]">Testing…</span>
					)}
					{testStatus?.ok && (
						<span className="inline-flex items-center gap-[5px] text-[11.5px] font-medium text-[#36713A]">
							<span className="flex h-[16px] w-[16px] items-center justify-center rounded-full bg-[#5AA45B] text-[9px] text-white">
								✓
							</span>
							Verified · {testStatus.stream_count} streams
						</span>
					)}
					{testStatus && testStatus.ok === false && (
						<span className="text-[11.5px] text-[#931F2A]">
							✕ {testStatus.error}
						</span>
					)}
					<button
						type="button"
						onClick={onClose}
						className="ml-auto rounded-[8px] px-[11px] py-[5px] text-[12px] font-medium text-[#5A607A] hover:bg-[#F0F2F7]"
					>
						Cancel
					</button>
					<button
						type="button"
						onClick={handleSave}
						disabled={saving}
						className="rounded-[8px] bg-[#0B0D14] px-[11px] py-[5px] text-[12px] font-medium text-white hover:bg-[#14172A] disabled:opacity-50"
					>
						{saving ? 'Saving…' : 'Save'}
					</button>
				</footer>
			</div>
		</div>,
		document.body
	);
}

function Field({ label, required, children }) {
	return (
		<div>
			<label className="mb-[4px] block text-[10.5px] font-semibold uppercase tracking-[0.07em] text-[#8389A3]">
				{label}
				{required && <span className="ml-[2px] text-[#D3424E]">*</span>}
			</label>
			{children}
		</div>
	);
}

function Help({ children }) {
	return (
		<div className="mt-[4px] text-[10.5px] text-[#8389A3]">{children}</div>
	);
}
