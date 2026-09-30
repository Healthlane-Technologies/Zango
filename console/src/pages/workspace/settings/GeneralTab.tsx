import { useState } from 'react';

import {
	generalSettingsKey,
	previewSubdomains,
	saveGeneralSettings,
	useGeneralSettings,
	type GeneralSettings,
	type GeneralSettingsForm,
	type ThemeConfig,
} from '@/api/platformSettings';

import { useApiMutation } from '@/api/hooks';

import {
	Button,
	Card,
	CardBody,
	CardHeader,
	ErrorState,
	Field,
	Input,
	SaveBar,
	Select,
	Skeleton,
	SwitchField,
	toast,
} from '@/ui';

const SWATCHES: Array<[string, string]> = [
	['color.primary', 'Primary'],
	['color.secondary', 'Secondary'],
	['color.background', 'Background'],
	['button.background', 'Button'],
];

function getPath(obj: ThemeConfig | null | undefined, path: string): string | undefined {
	return path
		.split('.')
		.reduce<unknown>((o, k) => (o == null ? undefined : (o as Record<string, unknown>)[k]), obj) as
		string | undefined;
}

function setPath(obj: ThemeConfig, path: string, value: string): ThemeConfig {
	const [head, ...rest] = path.split('.');
	const next = { ...obj } as Record<string, unknown>;
	next[head] = rest.length
		? setPath((next[head] as ThemeConfig) ?? {}, rest.join('.'), value)
		: value;
	return next as ThemeConfig;
}

function toForm(s: GeneralSettings): GeneralSettingsForm {
	return {
		auto_domain_enabled: s.auto_domain_enabled,
		base_domain: s.base_domain ?? '',
		auto_domain_is_primary: s.auto_domain_is_primary,
		default_timezone: s.default_timezone ?? '',
		default_date_format: s.default_date_format ?? '',
		default_datetime_format: s.default_datetime_format ?? '',
		default_language: s.default_language ?? '',
		default_theme_config: s.default_theme_config ?? null,
	};
}

function GeneralForm({ settings }: { settings: GeneralSettings }) {
	const [form, setForm] = useState(() => toForm(settings));
	const [dirty, setDirty] = useState(false);
	const [samples, setSamples] = useState<string[]>([]);
	const [previewing, setPreviewing] = useState(false);
	const set = <K extends keyof GeneralSettingsForm>(key: K, value: GeneralSettingsForm[K]) => {
		setForm((f) => ({ ...f, [key]: value }));
		setDirty(true);
	};

	const save = useApiMutation({
		fn: () => saveGeneralSettings(form),
		invalidate: [generalSettingsKey],
		success: (r) => r.message || 'Saved',
		onSuccess: () => setDirty(false),
	});

	const preview = async () => {
		setPreviewing(true);
		try {
			setSamples((await previewSubdomains(form.base_domain)).samples);
		} catch (e) {
			setSamples([]);
			toast.error((e as Error).message);
		} finally {
			setPreviewing(false);
		}
	};

	const { options } = settings;
	const theme = form.default_theme_config ?? options.default_theme_config ?? {};

	return (
		<div className="grid gap-4">
			<Card>
				<CardHeader title="Automatic domain allocation" />
				<CardBody className="grid gap-4">
					<p className="-mt-1 text-t3">
						Apps are matched by hostname, so an app without a domain can't be opened. With this on,
						every new app gets one.
					</p>
					<SwitchField
						checked={form.auto_domain_enabled}
						onChange={(v) => set('auto_domain_enabled', v)}
						label="Give every new app a domain"
						hint="Existing apps are not changed."
					/>
					<div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-start">
						<Field
							label="Base domain"
							hint="Point a wildcard DNS record (*.your-domain) at this platform, or the names won't resolve."
						>
							{(p) => (
								<Input
									{...p}
									className="mono"
									value={form.base_domain}
									onChange={(e) => set('base_domain', e.target.value)}
									placeholder="zelthy.com"
								/>
							)}
						</Field>
						<Button
							className="sm:mt-[23px]"
							onClick={preview}
							loading={previewing}
							disabled={!form.base_domain.trim()}
						>
							Preview names
						</Button>
					</div>
					{samples.length > 0 && (
						<div className="flex flex-wrap gap-2">
							{samples.map((s) => (
								<span key={s} className="badge bd-line mono">
									{s}
								</span>
							))}
						</div>
					)}
					{!settings.base_domain_valid && settings.base_domain && (
						<p className="text-[12px] text-amber-t">
							The saved base domain isn't valid, so no domains are being allocated.
						</p>
					)}
					<SwitchField
						checked={form.auto_domain_is_primary}
						onChange={(v) => set('auto_domain_is_primary', v)}
						label="Make it the app's primary domain"
						hint="The primary domain is the one the platform links to and builds URLs from."
					/>
				</CardBody>
			</Card>

			<Card>
				<CardHeader title="Defaults for new apps" />
				<CardBody>
					<p className="-mt-1 mb-4 text-t3">
						Each new app starts with these values and owns them from then on. Changing them never
						alters an existing app.
					</p>
					<div className="grid gap-4 sm:grid-cols-2">
						<Field label="Timezone" hint="Leave blank to let each app choose.">
							{(p) => (
								<Select
									{...p}
									value={form.default_timezone}
									onChange={(e) => set('default_timezone', e.target.value)}
								>
									<option value="">No default</option>
									{options.timezones.map((tz) => (
										<option key={tz} value={tz}>
											{tz}
										</option>
									))}
								</Select>
							)}
						</Field>
						<Field label="Language">
							{(p) => (
								<Select
									{...p}
									value={form.default_language}
									onChange={(e) => set('default_language', e.target.value)}
								>
									<option value="">No default</option>
									{options.languages.map((l) => (
										<option key={l.value} value={l.value}>
											{l.label}
										</option>
									))}
								</Select>
							)}
						</Field>
						<Field label="Date format">
							{(p) => (
								<Select
									{...p}
									value={form.default_date_format}
									onChange={(e) => set('default_date_format', e.target.value)}
								>
									<option value="">No default</option>
									{options.date_formats.map((f, i) => (
										// Values repeat across locales, so key by position.
										<option key={i} value={f.value}>
											{f.example}
										</option>
									))}
								</Select>
							)}
						</Field>
						<Field label="Date and time format">
							{(p) => (
								<Select
									{...p}
									value={form.default_datetime_format}
									onChange={(e) => set('default_datetime_format', e.target.value)}
								>
									<option value="">No default</option>
									{options.datetime_formats.map((f, i) => (
										// Values repeat across locales, so key by position.
										<option key={i} value={f.value}>
											{f.example}
										</option>
									))}
								</Select>
							)}
						</Field>
					</div>
				</CardBody>
			</Card>

			<Card>
				<CardHeader
					title="Default theme"
					actions={
						form.default_theme_config ? (
							<Button size="xs" variant="ghost" onClick={() => set('default_theme_config', null)}>
								Reset to built-in
							</Button>
						) : (
							<span className="text-[12px] text-t3">Using the built-in theme</span>
						)
					}
				/>
				<CardBody>
					<p className="-mt-1 mb-4 text-t3">
						The palette each new app starts with. Apps can restyle themselves afterwards.
					</p>
					<div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
						{SWATCHES.map(([path, label]) => {
							const value = getPath(theme, path) || '#ffffff';
							return (
								<Field key={path} label={label}>
									{(p) => (
										<div className="flex items-center gap-2">
											<input
												{...p}
												type="color"
												value={value}
												onChange={(e) =>
													set('default_theme_config', setPath(theme, path, e.target.value))
												}
												className="h-8 w-10 cursor-pointer rounded-md border border-border bg-panel p-[2px]"
											/>
											<span className="mono text-t3">{value}</span>
										</div>
									)}
								</Field>
							);
						})}
					</div>
				</CardBody>
			</Card>

			<SaveBar
				note="Applies to apps created from now on."
				dirty={dirty}
				saving={save.isPending}
				onSave={() => save.mutate()}
			/>
		</div>
	);
}

export function SettingsSkeleton() {
	return (
		<div className="grid gap-4">
			{[0, 1].map((i) => (
				<div key={i} className="card grid gap-3 p-4">
					<Skeleton width={180} height={14} />
					<Skeleton width="70%" />
					<Skeleton width="45%" />
				</div>
			))}
		</div>
	);
}

export function GeneralTab() {
	const { data, isLoading, error, refetch } = useGeneralSettings();
	if (isLoading) return <SettingsSkeleton />;
	if (error || !data)
		return (
			<div className="card">
				<ErrorState error={error ?? new Error('No settings returned')} onRetry={() => refetch()} />
			</div>
		);
	// Remount on save so the form picks up the server's normalised values.
	return <GeneralForm key={data.modified_at ?? 'initial'} settings={data} />;
}
