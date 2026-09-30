import { useState, type FormEvent } from 'react';

import { ApiError } from '@/api/client';

import { useApiMutation } from '@/api/hooks';

import {
	logKeys,
	saveConnector,
	testConnector,
	useConnectors,
	type ConnectorPayload,
	type ConnectorRow,
	type LogComponent,
} from '@/api/logConnectors';

import { formatDateTime, timeAgo } from '@/format/time';

import {
	Badge,
	Banner,
	Button,
	Card,
	ErrorState,
	Field,
	Icon,
	Input,
	Modal,
	Select,
	SwitchField,
} from '@/ui';

import { SettingsSkeleton } from './GeneralTab';

const META: Record<LogComponent, { label: string; sub: string }> = {
	app: { label: 'App', sub: 'Django · gunicorn output' },
	celery: { label: 'Celery worker', sub: 'Background tasks' },
	celery_beat: { label: 'Celery beat', sub: 'Scheduler' },
};

const FORMATS = [
	{ value: 'verbose', label: 'verbose · [schema:domain] prefix' },
	{ value: 'plain', label: 'plain · no tenant prefix' },
	{ value: 'json', label: 'json · structured (not yet supported)', disabled: true },
];

function ConnectorCard({
	component,
	row,
	onEdit,
}: {
	component: LogComponent;
	row: ConnectorRow | undefined;
	onEdit: () => void;
}) {
	const meta = META[component] ?? { label: component, sub: '' };
	const cfg = row?.config ?? {};
	return (
		<Card className={row ? '' : 'border-dashed'}>
			<div className="flex items-center gap-3 px-4 pb-3 pt-4">
				<span
					className={`grid h-8 w-8 place-items-center rounded-lg ${row ? 'bg-accent-soft text-accent-t' : 'bg-subtle text-t3'}`}
				>
					<Icon name="logs" />
				</span>
				<div className="min-w-0">
					<b className="block text-t1">{meta.label}</b>
					<small className="text-t3">{meta.sub}</small>
				</div>
				<span className="ml-auto">
					{!row ? (
						<Badge tone="gray">Not configured</Badge>
					) : row.is_active ? (
						<Badge tone="green" dot>
							Active
						</Badge>
					) : (
						<Badge tone="amber" dot>
							Paused
						</Badge>
					)}
				</span>
			</div>
			<dl
				className={`kv mx-4 rounded-lg bg-bg p-3 mono !text-[11.5px] ${row ? '' : 'opacity-50'}`}
				style={{ gridTemplateColumns: '64px 1fr' }}
			>
				<dt>type</dt>
				<dd>{row?.connector ?? '—'}</dd>
				<dt>region</dt>
				<dd>{cfg.region || '—'}</dd>
				<dt>group</dt>
				<dd className="truncate" title={cfg.log_group_name}>
					{cfg.log_group_name || '—'}
				</dd>
				<dt>format</dt>
				<dd>{cfg.format || '—'}</dd>
			</dl>
			<div className="flex items-center gap-2 px-4 py-3">
				<span
					className="text-[12px] text-t3"
					title={row ? formatDateTime(row.modified_at) : undefined}
				>
					{row ? `Updated ${timeAgo(row.modified_at)}` : ''}
				</span>
				<Button
					size="sm"
					variant={row ? 'secondary' : 'primary'}
					icon={row ? undefined : 'plus'}
					className="ml-auto"
					onClick={onEdit}
				>
					{row ? 'Edit' : 'Configure'}
				</Button>
			</div>
		</Card>
	);
}

/** Pull a readable message out of the serializer's `errors` blob. */
function describeError(err: unknown): string {
	if (err instanceof ApiError) {
		const errors = (err.body as { response?: { errors?: Record<string, unknown> } })?.response
			?.errors;
		if (errors) {
			return Object.entries(errors)
				.map(
					([k, v]) =>
						`${k}: ${Array.isArray(v) ? v.join(' ') : typeof v === 'object' ? JSON.stringify(v) : String(v)}`,
				)
				.join(' · ');
		}
	}
	return (err as Error).message;
}

function ConnectorModal({
	environment,
	component,
	row,
	types,
	onClose,
}: {
	environment: string;
	component: LogComponent;
	row: ConnectorRow | undefined;
	types: string[];
	onClose: () => void;
}) {
	const [connector, setConnector] = useState(row?.connector ?? types[0] ?? 'cloudwatch');
	const [cfg, setCfg] = useState({
		region: row?.config.region ?? 'ap-south-1',
		log_group_name: row?.config.log_group_name ?? '',
		stream_prefix: row?.config.stream_prefix ?? '',
		format: row?.config.format ?? 'verbose',
		// The server masks the key id to its last 4 characters and blanks the secret;
		// both are treated as "keep the stored value" on save.
		aws_access_key_id: row?.config.aws_access_key_id ?? '',
		aws_secret_access_key: '',
		role_arn: row?.config.role_arn ?? '',
	});
	const [active, setActive] = useState(row?.is_active ?? true);
	const [formError, setFormError] = useState<string>();
	const [test, setTest] = useState<
		{ state: 'pending' } | { state: 'ok'; streams: number } | { state: 'fail'; message: string }
	>();
	const update = (k: keyof typeof cfg, v: string) => setCfg((c) => ({ ...c, [k]: v }));

	const payload = (): ConnectorPayload => {
		const config: Record<string, string> = { ...cfg };
		// Blank optional fields are dropped so the server's merge keeps stored values.
		for (const k of ['stream_prefix', 'role_arn', 'aws_access_key_id', 'aws_secret_access_key'])
			if (!config[k]) delete config[k];
		return { environment, component, connector, config, is_active: active };
	};

	const save = useApiMutation({
		fn: () => saveConnector(payload()),
		invalidate: [logKeys.connectors, logKeys.components],
		success: `${META[component]?.label ?? component} connector saved`,
		onSuccess: onClose,
	});

	const submit = (e: FormEvent) => {
		e.preventDefault();
		if (!cfg.region.trim() || !cfg.log_group_name.trim())
			return setFormError('Region and log group name are required.');
		setFormError(undefined);
		save.mutate();
	};

	const runTest = async () => {
		setTest({ state: 'pending' });
		try {
			const r = await testConnector(payload());
			setTest({ state: 'ok', streams: r.stream_count });
		} catch (e) {
			setTest({ state: 'fail', message: describeError(e) });
		}
	};

	const saveError = save.error ? describeError(save.error) : undefined;

	return (
		<Modal
			open
			large
			onOpenChange={(o) => !o && onClose()}
			title={`${row ? 'Edit' : 'Configure'} ${META[component]?.label ?? component} connector`}
			subtitle={`${environment} × ${component}`}
			footer={
				<>
					<Button icon="check" onClick={runTest} loading={test?.state === 'pending'}>
						Test connection
					</Button>
					{test?.state === 'ok' && (
						<span className="self-center text-[12px] font-[550] text-green-t">
							Connected · {test.streams} streams
						</span>
					)}
					{test?.state === 'fail' && (
						<span
							className="max-w-[260px] self-center truncate text-[12px] text-red-t"
							title={test.message}
						>
							{test.message}
						</span>
					)}
					<span className="flex-1" />
					<Button onClick={onClose}>Cancel</Button>
					<Button variant="primary" type="submit" form="connector-form" loading={save.isPending}>
						Save
					</Button>
				</>
			}
		>
			<form id="connector-form" className="grid gap-4 sm:grid-cols-2" onSubmit={submit} noValidate>
				<Field label="Connector type">
					{(p) => (
						<Select {...p} value={connector} onChange={(e) => setConnector(e.target.value)}>
							{types.map((t) => (
								<option key={t} value={t}>
									{t}
								</option>
							))}
						</Select>
					)}
				</Field>
				<Field label="AWS region">
					{(p) => (
						<Input
							{...p}
							className="mono"
							value={cfg.region}
							onChange={(e) => update('region', e.target.value)}
							placeholder="ap-south-1"
						/>
					)}
				</Field>
				<div className="sm:col-span-2">
					<Field label="Log group name" hint='Checked when you click "Test connection".'>
						{(p) => (
							<Input
								{...p}
								className="mono"
								value={cfg.log_group_name}
								onChange={(e) => update('log_group_name', e.target.value)}
								placeholder="/ecs/zango-staging/app"
							/>
						)}
					</Field>
				</div>
				<Field label="Stream prefix" hint="Optional. Only read streams starting with this.">
					{(p) => (
						<Input
							{...p}
							className="mono"
							value={cfg.stream_prefix}
							onChange={(e) => update('stream_prefix', e.target.value)}
							placeholder="app/app/"
						/>
					)}
				</Field>
				<Field label="Line format" hint="Drives how lines are matched to apps.">
					{(p) => (
						<Select {...p} value={cfg.format} onChange={(e) => update('format', e.target.value)}>
							{FORMATS.map((f) => (
								<option key={f.value} value={f.value} disabled={f.disabled}>
									{f.label}
								</option>
							))}
						</Select>
					)}
				</Field>
				<div className="divider sm:col-span-2 !my-1" />
				<p className="text-t3 sm:col-span-2">
					<b className="font-[550] text-t1">Authentication, optional.</b> Use access keys or a role
					ARN. Leave both blank to use the server's default AWS credentials.
					{row && ' Leave the secret blank to keep the saved one.'}
				</p>
				<Field label="Access key ID">
					{(p) => (
						<Input
							{...p}
							className="mono"
							value={cfg.aws_access_key_id}
							onChange={(e) => update('aws_access_key_id', e.target.value)}
							placeholder="AKIA…"
							autoComplete="off"
						/>
					)}
				</Field>
				<Field label="Secret access key">
					{(p) => (
						<Input
							{...p}
							type="password"
							className="mono"
							value={cfg.aws_secret_access_key}
							onChange={(e) => update('aws_secret_access_key', e.target.value)}
							placeholder={row ? '•••••• (leave blank to keep)' : '••••••'}
							autoComplete="new-password"
						/>
					)}
				</Field>
				<div className="sm:col-span-2">
					<Field
						label="Role ARN"
						hint="Cross-account. Without keys above, the server assumes this role before each read."
					>
						{(p) => (
							<Input
								{...p}
								className="mono"
								value={cfg.role_arn}
								onChange={(e) => update('role_arn', e.target.value)}
								placeholder="arn:aws:iam::123456789012:role/zango-logs-reader"
							/>
						)}
					</Field>
				</div>
				<div className="sm:col-span-2">
					<SwitchField
						checked={active}
						onChange={setActive}
						label="Active"
						hint="Paused connectors are kept but not read from."
					/>
				</div>
				{(formError || saveError) && (
					<p
						role="alert"
						className="rounded-lg bg-red-soft px-3 py-2 text-[12.5px] text-red-t sm:col-span-2"
					>
						<b className="font-[550]">Could not save.</b> {formError ?? saveError}
					</p>
				)}
			</form>
		</Modal>
	);
}

export function LogConnectorsTab() {
	const { data, isLoading, error, refetch } = useConnectors();
	const [editing, setEditing] = useState<LogComponent | null>(null);

	if (isLoading) return <SettingsSkeleton />;
	if (error || !data)
		return (
			<div className="card">
				<ErrorState
					error={error ?? new Error('No connectors returned')}
					onRetry={() => refetch()}
				/>
			</div>
		);

	const rowFor = (c: LogComponent) => data.rows.find((r) => r.component === c);

	return (
		<>
			<Banner>
				<Icon name="logs" className="text-accent" />
				<span>
					One connector per component, set once for the platform. Every app reads from the same
					source, filtered to its own lines.
				</span>
				<Badge tone="amber" dot className="ml-auto">
					Environment: {data.environment}
				</Badge>
			</Banner>
			<div className="grid gap-4 md:grid-cols-3">
				{data.components.map((c) => (
					<ConnectorCard key={c} component={c} row={rowFor(c)} onEdit={() => setEditing(c)} />
				))}
			</div>
			{editing && (
				<ConnectorModal
					environment={data.environment}
					component={editing}
					row={rowFor(editing)}
					types={data.available_types}
					onClose={() => setEditing(null)}
				/>
			)}
		</>
	);
}
