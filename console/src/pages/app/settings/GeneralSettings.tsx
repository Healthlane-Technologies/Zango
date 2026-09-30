import { useEffect, useMemo, useState } from 'react';

import { useAppSettings, useUpdateApp, type AppDetail, type ExtraConfig } from '@/api/appSettings';

import {
	Button,
	Card,
	CardBody,
	CardHeader,
	Checkbox,
	ErrorState,
	Field,
	Icon,
	Input,
	SaveBar,
	Select,
	Skeleton,
	Textarea,
} from '@/ui';

interface Domain {
	domain: string;
	is_primary: boolean;
}

interface FormState {
	description: string;
	meta_title: string;
	timezone: string;
	date_format: string;
	datetime_format: string;
	domains: Domain[];
	repo_url: string;
	dev: string;
	staging: string;
	prod: string;
	sync_packages: boolean;
	logo?: File;
	fav_icon?: File;
}

function initialState(app: AppDetail): FormState {
	const x = app.extra_config ?? {};
	const git = x.git_config ?? {};
	const domains = app.domains.map((d) => ({ domain: d.domain, is_primary: d.is_primary }));
	if (domains.length && !domains.some((d) => d.is_primary)) domains[0].is_primary = true;
	return {
		description: app.description ?? '',
		meta_title: x.app_metadata?.meta_title ?? '',
		timezone: app.timezone ?? '',
		date_format: app.date_format ?? '',
		datetime_format: app.datetime_format ?? '',
		domains: domains.length ? domains : [{ domain: '', is_primary: true }],
		repo_url: git.repo_url ?? '',
		dev: git.branch?.dev ?? '',
		staging: git.branch?.staging ?? '',
		prod: git.branch?.prod ?? '',
		sync_packages: x.sync_packages ?? true,
	};
}

type Errors = Partial<Record<'description' | 'domains' | 'repo_url', string>>;

function validate(f: FormState): Errors {
	const e: Errors = {};
	if (!f.description.trim()) e.description = 'Required';
	const domains = f.domains.filter((d) => d.domain.trim());
	if (!domains.length) e.domains = 'Add at least one domain';
	else if (domains.filter((d) => d.is_primary).length !== 1)
		e.domains = 'Mark exactly one domain as primary';
	if (f.repo_url) {
		try {
			new URL(f.repo_url);
		} catch {
			e.repo_url = 'Must be a valid URL';
		}
	} else if (f.dev || f.staging || f.prod) {
		e.repo_url = 'Required when a branch is set';
	}
	return e;
}

/**
 * The serializer replaces extra_config wholesale, so merge our keys over whatever is already
 * stored instead of rebuilding it (the classic panel drops unknown keys).
 */
function mergedExtraConfig(existing: ExtraConfig | null, f: FormState): ExtraConfig {
	const hasGit = f.repo_url || f.dev || f.staging || f.prod;
	return {
		...(existing ?? {}),
		app_metadata: { ...(existing?.app_metadata ?? {}), meta_title: f.meta_title || null },
		git_config: hasGit
			? {
					repo_url: f.repo_url || null,
					branch: { dev: f.dev || null, staging: f.staging || null, prod: f.prod || null },
				}
			: {},
		sync_packages: f.sync_packages,
	};
}

function FileInput({
	label,
	current,
	onChange,
}: {
	label: string;
	current: string | null;
	onChange: (f?: File) => void;
}) {
	const [preview, setPreview] = useState<string | null>(null);
	useEffect(() => () => void (preview && URL.revokeObjectURL(preview)), [preview]);
	const src = preview ?? current;
	return (
		<Field label={label} hint="PNG, SVG or ICO">
			{(p) => (
				<div className="flex items-center gap-3">
					<span className="grid h-10 w-10 place-items-center overflow-hidden rounded-lg border border-border bg-bg">
						{src ? (
							<img src={src} alt="" className="h-full w-full object-contain" />
						) : (
							<Icon name="file" className="text-t4" />
						)}
					</span>
					<input
						{...p}
						type="file"
						accept="image/*"
						className="text-[12.5px] text-t3 file:mr-3 file:rounded-md file:border file:border-border file:bg-panel file:px-2.5 file:py-1 file:text-[12.5px] file:font-[550] file:text-t1"
						onChange={(e) => {
							const file = e.target.files?.[0];
							setPreview(file ? URL.createObjectURL(file) : null);
							onChange(file);
						}}
					/>
				</div>
			)}
		</Field>
	);
}

export function GeneralSettings({ appId }: { appId: string }) {
	const { data, isLoading, error, refetch } = useAppSettings(appId);
	const update = useUpdateApp(appId);
	const app = data?.app;
	const initial = useMemo(() => (app ? initialState(app) : null), [app]);
	const [form, setForm] = useState<FormState | null>(null);
	const [touched, setTouched] = useState(false);

	useEffect(() => {
		if (initial) setForm(initial);
	}, [initial]);

	if (error)
		return (
			<div className="card">
				<ErrorState error={error} onRetry={() => refetch()} />
			</div>
		);
	if (isLoading || !form || !app || !initial) {
		return (
			<div className="card card-b grid gap-4">
				{[0, 1, 2, 3].map((i) => (
					<Skeleton key={i} height={32} />
				))}
			</div>
		);
	}

	const opts = data.dropdown_options;
	const errors = touched ? validate(form) : {};
	const dirty =
		JSON.stringify({ ...form, logo: undefined, fav_icon: undefined }) !== JSON.stringify(initial) ||
		!!form.logo ||
		!!form.fav_icon;
	const set = <K extends keyof FormState>(k: K, v: FormState[K]) => setForm({ ...form, [k]: v });
	const setDomain = (i: number, patch: Partial<Domain>) =>
		set(
			'domains',
			form.domains.map((d, j) =>
				j === i ? { ...d, ...patch } : patch.is_primary ? { ...d, is_primary: false } : d,
			),
		);

	const save = () => {
		setTouched(true);
		if (Object.keys(validate(form)).length) return;
		update.mutate(
			{
				description: form.description,
				timezone: form.timezone,
				date_format: form.date_format,
				datetime_format: form.datetime_format,
				domains: form.domains
					.filter((d) => d.domain.trim())
					.map((d) => ({ domain: d.domain.trim(), is_primary: d.is_primary })),
				extra_config: mergedExtraConfig(app.extra_config, form),
				logo: form.logo,
				fav_icon: form.fav_icon,
			},
			{ onSuccess: () => setTouched(false) },
		);
	};

	return (
		<form
			className="grid gap-4"
			onSubmit={(e) => {
				e.preventDefault();
				save();
			}}
		>
			<Card>
				<CardHeader title="General" />
				<CardBody className="grid gap-4">
					<Field label="App name" hint="The name is the tenant identifier and can't be changed.">
						{(p) => <Input {...p} value={app.name} disabled className="bg-bg text-t3" />}
					</Field>
					<Field label="Description" error={errors.description}>
						{(p) => (
							<Textarea
								{...p}
								rows={3}
								value={form.description}
								onChange={(e) => set('description', e.target.value)}
							/>
						)}
					</Field>
				</CardBody>
			</Card>

			<Card>
				<CardHeader title="Branding" />
				<CardBody className="grid gap-4">
					<Field label="Browser tab title">
						{(p) => (
							<Input
								{...p}
								value={form.meta_title}
								placeholder={app.name}
								onChange={(e) => set('meta_title', e.target.value)}
							/>
						)}
					</Field>
					<div className="grid gap-4 md:grid-cols-2">
						<FileInput label="Logo" current={app.logo} onChange={(f) => set('logo', f)} />
						<FileInput
							label="Favicon"
							current={app.fav_icon}
							onChange={(f) => set('fav_icon', f)}
						/>
					</div>
				</CardBody>
			</Card>

			<Card>
				<CardHeader
					title="Domains"
					actions={
						<Button
							size="sm"
							icon="plus"
							onClick={() => set('domains', [...form.domains, { domain: '', is_primary: false }])}
						>
							Add domain
						</Button>
					}
				/>
				<CardBody className="grid gap-2">
					{form.domains.map((d, i) => (
						<div key={i} className="flex items-center gap-2">
							<Input
								aria-label={`Domain ${i + 1}`}
								className="mono"
								value={d.domain}
								placeholder="app.example.com"
								onChange={(e) => setDomain(i, { domain: e.target.value })}
							/>
							<label className="flex shrink-0 cursor-pointer items-center gap-1.5 text-[12.5px] text-t2">
								<input
									type="radio"
									name="primary-domain"
									className="accent-[var(--accent)]"
									checked={d.is_primary}
									onChange={() => setDomain(i, { is_primary: true })}
								/>
								Primary
							</label>
							<button
								type="button"
								className="ib shrink-0"
								aria-label={`Remove ${d.domain || 'domain'}`}
								disabled={form.domains.length === 1}
								onClick={() => {
									const rest = form.domains.filter((_, j) => j !== i);
									if (d.is_primary && rest.length) rest[0] = { ...rest[0], is_primary: true };
									set('domains', rest);
								}}
							>
								<Icon name="x" />
							</button>
						</div>
					))}
					{errors.domains && <span className="text-[12px] text-red-t">{errors.domains}</span>}
				</CardBody>
			</Card>

			<Card>
				<CardHeader title="Regional" />
				<CardBody className="grid gap-4 md:grid-cols-3">
					<Field label="Timezone">
						{(p) => (
							<Select
								{...p}
								value={form.timezone}
								onChange={(e) => set('timezone', e.target.value)}
							>
								{opts.timezones.map((o, i) => (
									// The server's option lists can repeat an id.
									<option key={`${o.id}-${i}`} value={o.id}>
										{o.label}
									</option>
								))}
							</Select>
						)}
					</Field>
					<Field label="Date format">
						{(p) => (
							<Select
								{...p}
								value={form.date_format}
								onChange={(e) => set('date_format', e.target.value)}
							>
								{opts.date_formats.map((o, i) => (
									// The server's option lists can repeat an id.
									<option key={`${o.id}-${i}`} value={o.id}>
										{o.label}
									</option>
								))}
							</Select>
						)}
					</Field>
					<Field label="Date & time format">
						{(p) => (
							<Select
								{...p}
								value={form.datetime_format}
								onChange={(e) => set('datetime_format', e.target.value)}
							>
								{opts.datetime_formats.map((o, i) => (
									// The server's option lists can repeat an id.
									<option key={`${o.id}-${i}`} value={o.id}>
										{o.label}
									</option>
								))}
							</Select>
						)}
					</Field>
				</CardBody>
			</Card>

			<Card>
				<CardHeader title="Repository" />
				<CardBody className="grid gap-4">
					<Field
						label="Repository URL"
						error={errors.repo_url}
						hint="Releases are pulled from this repository."
					>
						{(p) => (
							<Input
								{...p}
								className="mono"
								value={form.repo_url}
								placeholder="https://github.com/org/repo"
								onChange={(e) => set('repo_url', e.target.value)}
							/>
						)}
					</Field>
					<div className="grid gap-4 md:grid-cols-3">
						{(
							[
								['dev', 'Development branch', 'development'],
								['staging', 'Staging branch', 'staging'],
								['prod', 'Production branch', 'main'],
							] as const
						).map(([k, label, ph]) => (
							<Field key={k} label={label}>
								{(p) => (
									<Input
										{...p}
										className="mono"
										value={form[k]}
										placeholder={ph}
										onChange={(e) => set(k, e.target.value)}
									/>
								)}
							</Field>
						))}
					</div>
					<Checkbox
						checked={form.sync_packages}
						onChange={(e) => set('sync_packages', e.target.checked)}
						label="Sync packages"
						hint="Install the packages listed in the repository on each release."
					/>
				</CardBody>
			</Card>

			<SaveBar
				submit
				dirty={dirty}
				saving={update.isPending}
				onDiscard={() => {
					setForm(initial);
					setTouched(false);
				}}
			/>
		</form>
	);
}
