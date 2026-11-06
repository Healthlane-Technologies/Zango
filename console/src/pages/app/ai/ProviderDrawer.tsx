import { useMemo, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
	aiKeys,
	createProvider,
	fetchModels,
	isAuthError,
	updateProvider,
	useAvailableProviders,
	useToggleProviderModel,
	type AvailableProvider,
	type ConfigField,
	type Provider,
	type ProviderModelInfo,
} from '@/api/ai';
import { api } from '@/api/client';
import {
	Banner,
	Button,
	cx,
	Drawer,
	Field,
	Input,
	SectionTitle,
	Select,
	Skeleton,
	Switch,
	toast,
} from '@/ui';
import { serviceLabel } from './parts';

/** Config fields that belong in `config` (default_model is a top-level body field). */
const configFields = (svc: AvailableProvider | undefined) =>
	(svc?.config_fields ?? []).filter((f) => f.options_from !== 'supported_models');

const numOrNull = (s: string) => (s.trim() === '' ? null : Number(s));

function modelLabel(m: ProviderModelInfo) {
	const bits = [m.name !== m.id ? m.name : null];
	if (m.context_window) bits.push(`${Math.round(m.context_window / 1000)}K context`);
	return `${m.id}${bits.filter(Boolean).length ? ` · ${bits.filter(Boolean).join(' · ')}` : ''}`;
}

/**
 * Add a provider (pick a service, enter credentials, check them by loading models, choose a
 * default model) or edit one (credentials left blank keep the saved ones).
 */
export function ProviderDrawer({
	appId,
	provider,
	onClose,
}: {
	appId: string;
	/** Omitted: add a new provider. */
	provider?: Provider;
	onClose: () => void;
}) {
	const available = useAvailableProviders(appId);
	const qc = useQueryClient();
	const editing = provider != null;

	const [slug, setSlug] = useState(provider?.provider_slug ?? '');
	const svc = available.data?.find((p) => p.slug === slug);
	const fields = configFields(svc);

	// Edit: every field starts blank except non-secret values, which show what's saved.
	const [initial] = useState<Record<string, string>>(() => {
		const out: Record<string, string> = {};
		for (const [k, v] of Object.entries(provider?.masked_config ?? {})) {
			if (typeof v === 'string' && v.includes('****')) continue;
			if (v != null) out[k] = String(v);
		}
		return out;
	});
	const [values, setValues] = useState<Record<string, string>>(initial);
	const [typedSecret, setTypedSecret] = useState(false);

	const [models, setModels] = useState<ProviderModelInfo[] | null>(null);
	const [modelNote, setModelNote] = useState<{ tone: 'red' | 'amber'; text: string } | null>(null);
	const [loadingModels, setLoadingModels] = useState(false);
	const [defaultModel, setDefaultModel] = useState(provider?.default_model ?? '');

	const [name, setName] = useState(provider?.name ?? '');
	const [description, setDescription] = useState(provider?.description ?? '');
	const [rpm, setRpm] = useState(provider?.rate_limit_rpm?.toString() ?? '');
	const [budget, setBudget] = useState(
		provider?.monthly_budget_usd != null ? String(Number(provider.monthly_budget_usd)) : '',
	);
	const [saving, setSaving] = useState(false);

	const pickService = (s: string) => {
		setSlug(s);
		setValues({});
		setModels(null);
		setModelNote(null);
		setDefaultModel('');
	};

	const set = (f: ConfigField, v: string) => {
		setValues((cur) => ({ ...cur, [f.name]: v }));
		if (f.type === 'secret') setTypedSecret(true);
		if (modelNote?.tone === 'red') setModelNote(null);
	};

	/** Typed values, then saved values (masked secrets are restored server-side), then defaults. */
	const buildConfig = () => {
		const out: Record<string, unknown> = {};
		for (const f of fields) {
			const typed = values[f.name]?.trim();
			const saved = provider?.masked_config?.[f.name];
			const v = typed || (saved != null && saved !== '' ? saved : f.default);
			if (v === undefined || v === '') continue;
			out[f.name] = f.type === 'integer' ? Number(v) : v;
		}
		return out;
	};

	const missing = fields.filter(
		(f) => f.required && !values[f.name]?.trim() && !(editing && provider?.masked_config?.[f.name]),
	);

	const loadModels = async () => {
		if (!svc) return;
		setLoadingModels(true);
		setModelNote(null);
		try {
			const list = await fetchModels(appId, svc.slug, buildConfig());
			setModels(list);
			if (!list.length) setModelNote({ tone: 'amber', text: 'The service returned no models.' });
			if (!defaultModel || !list.some((m) => m.id === defaultModel))
				setDefaultModel(list[0]?.id ?? '');
		} catch (err) {
			const msg = err instanceof Error ? err.message : String(err);
			if (isAuthError(err) || !svc.supported_models.length) {
				setModels(null);
				setModelNote({ tone: 'red', text: msg });
			} else {
				setModels(svc.supported_models);
				setModelNote({
					tone: 'amber',
					text: `Couldn't load the live model list (${msg}). Showing the known models instead.`,
				});
				if (!defaultModel) setDefaultModel(svc.supported_models[0]?.id ?? '');
			}
		} finally {
			setLoadingModels(false);
		}
	};

	// Edit mode offers the saved model rows until a fresh list is loaded.
	const modelOptions = useMemo(() => {
		if (models) return models.map((m) => ({ id: m.id, label: modelLabel(m) }));
		const saved = (provider?.enabled_models ?? [])
			.filter((m) => m.is_enabled)
			.map((m) => ({
				id: m.model_id,
				label: m.display_name !== m.model_id ? `${m.model_id} · ${m.display_name}` : m.model_id,
			}));
		if (defaultModel && !saved.some((m) => m.id === defaultModel))
			saved.unshift({ id: defaultModel, label: defaultModel });
		return saved;
	}, [models, provider, defaultModel]);

	const canSave =
		!!name.trim() &&
		!!defaultModel &&
		(editing ? !typedSecret || models != null : models != null && missing.length === 0);

	const save = async () => {
		setSaving(true);
		const limits = {
			rate_limit_rpm: numOrNull(rpm),
			monthly_budget_usd: budget.trim() === '' ? null : budget.trim(),
		};
		try {
			if (editing) {
				const credentialsTouched = fields.some(
					(f) => (values[f.name] ?? '').trim() !== (initial[f.name] ?? ''),
				);
				await updateProvider(appId, provider.id, {
					name: name.trim(),
					description,
					default_model: defaultModel,
					...(credentialsTouched ? { config: buildConfig() } : {}),
					...limits,
				});
				// PUT doesn't re-check credentials; do it so the status reflects the new key.
				if (credentialsTouched)
					await api(`/api/v1/apps/${appId}/ai/providers/${provider.id}/validate/`, 'POST', {});
				toast.success(`${name.trim()} updated`);
			} else {
				await createProvider(appId, {
					name: name.trim(),
					description,
					provider_slug: slug,
					config: buildConfig(),
					default_model: defaultModel,
					fetched_models: models ?? [],
					...limits,
				});
				toast.success(`${name.trim()} added`);
			}
			await qc.invalidateQueries({ queryKey: aiKeys.all(appId) });
			onClose();
		} catch (err) {
			toast.error(err instanceof Error ? err.message : String(err));
			await qc.invalidateQueries({ queryKey: aiKeys.providers(appId) });
		} finally {
			setSaving(false);
		}
	};

	return (
		<Drawer
			open
			onOpenChange={(o) => !o && onClose()}
			title={editing ? provider.name : 'Add provider'}
			subtitle={
				editing
					? `${serviceLabel(provider.provider_slug)} · credentials are stored encrypted`
					: 'Credentials are checked with the service, then stored encrypted for this app.'
			}
			footer={
				<>
					<Button onClick={onClose}>Cancel</Button>
					<Button variant="primary" disabled={!canSave} loading={saving} onClick={save}>
						{editing ? 'Save' : 'Add provider'}
					</Button>
				</>
			}
		>
			{!editing && (
				<>
					<SectionTitle>Service</SectionTitle>
					{available.isLoading ? (
						<Skeleton height={64} />
					) : (
						<div className="grid grid-cols-2 gap-2">
							{(available.data ?? []).map((p) => (
								<button
									key={p.slug}
									type="button"
									onClick={() => pickService(p.slug)}
									className={cx(
										'rounded-lg border px-3 py-2.5 text-left transition-colors',
										p.slug === slug
											? 'border-accent bg-accent-soft'
											: 'border-border bg-panel hover:bg-hover',
									)}
								>
									<b className="block text-[13px] text-t1">{p.display_name}</b>
									<small className="text-t3">
										{p.supported_models.length
											? `${p.supported_models.length} known models`
											: 'Models listed from your account'}
									</small>
								</button>
							))}
						</div>
					)}
				</>
			)}

			{svc && (
				<>
					<SectionTitle>Credentials</SectionTitle>
					{editing && (
						<p className="mb-3 text-[12px] text-t3">
							Leave a secret blank to keep the saved one. A new key is checked when you save.
						</p>
					)}
					<div className="grid gap-3">
						{fields.map((f) => {
							const saved = provider?.masked_config?.[f.name];
							return (
								<Field
									key={f.name}
									label={
										<>
											{f.label}
											{f.required && <span className="text-red"> *</span>}
										</>
									}
									hint={f.help_text}
								>
									{(p) => (
										<Input
											{...p}
											type={f.type === 'secret' ? 'password' : f.type === 'integer' ? 'number' : 'text'}
											className={f.type === 'secret' ? 'mono' : undefined}
											autoComplete="off"
											value={values[f.name] ?? ''}
											placeholder={
												f.type === 'secret' && saved
													? `${String(saved)} (saved)`
													: f.default != null
														? String(f.default)
														: ''
											}
											onChange={(e) => set(f, e.target.value)}
										/>
									)}
								</Field>
							);
						})}
					</div>
					<div className="mt-3 flex items-center gap-2">
						<Button
							icon="check"
							loading={loadingModels}
							disabled={missing.length > 0}
							onClick={loadModels}
						>
							{editing ? 'Check and reload models' : 'Check credentials and load models'}
						</Button>
						{models && !modelNote && (
							<span className="text-[12px] text-green">{models.length} models available</span>
						)}
					</div>
					{modelNote && (
						<div
							className={cx(
								'mt-3 rounded-lg border px-3 py-2 text-[12.5px]',
								modelNote.tone === 'red'
									? 'border-red bg-red-soft text-red-t'
									: 'border-amber bg-amber-soft text-amber-t',
							)}
						>
							{modelNote.tone === 'red' && <b>Credentials rejected. </b>}
							{modelNote.text}
						</div>
					)}
					{editing && typedSecret && !models && (
						<p className="mt-2 text-[12px] text-amber-t">
							Check the new credentials before saving.
						</p>
					)}

					{(models || editing) && (
						<>
							<SectionTitle>Default model</SectionTitle>
							<Field label="Model" hint="Used when an agent or a direct call doesn't name one.">
								{(p) => (
									<Select
										{...p}
										className="mono"
										value={defaultModel}
										onChange={(e) => setDefaultModel(e.target.value)}
									>
										{!defaultModel && <option value="">Choose a model</option>}
										{modelOptions.map((m) => (
											<option key={m.id} value={m.id}>
												{m.label}
											</option>
										))}
									</Select>
								)}
							</Field>
						</>
					)}

					<SectionTitle>Details</SectionTitle>
					<div className="grid gap-3">
						<Field label="Name" hint="How agents and app code refer to this provider.">
							{(p) => (
								<Input
									{...p}
									value={name}
									placeholder="e.g. claude-primary"
									onChange={(e) => setName(e.target.value)}
								/>
							)}
						</Field>
						<Field label="Description">
							{(p) => (
								<Input
									{...p}
									value={description}
									placeholder="Optional"
									onChange={(e) => setDescription(e.target.value)}
								/>
							)}
						</Field>
						<div className="grid grid-cols-2 gap-3">
							<Field label="Rate limit (requests/min)">
								{(p) => (
									<Input
										{...p}
										type="number"
										min={1}
										value={rpm}
										placeholder="Unlimited"
										onChange={(e) => setRpm(e.target.value)}
									/>
								)}
							</Field>
							<Field label="Monthly budget (USD)">
								{(p) => (
									<Input
										{...p}
										type="number"
										min={0}
										step="0.01"
										value={budget}
										placeholder="Unlimited"
										onChange={(e) => setBudget(e.target.value)}
									/>
								)}
							</Field>
						</div>
					</div>

					{editing && provider.enabled_models.length > 0 && (
						<ProviderModels appId={appId} provider={provider} />
					)}
				</>
			)}

			{!editing && !svc && !available.isLoading && (
				<Banner>Pick the AI service this app should call.</Banner>
			)}
		</Drawer>
	);
}

/** Per-model on/off; disabled models can't be used by agents on this provider. */
function ProviderModels({ appId, provider }: { appId: string; provider: Provider }) {
	const toggle = useToggleProviderModel(appId);
	return (
		<>
			<SectionTitle
				action={
					<span className="text-[12px] text-t3">
						{provider.enabled_models.filter((m) => m.is_enabled).length} of{' '}
						{provider.enabled_models.length} on
					</span>
				}
			>
				Models
			</SectionTitle>
			<div className="max-h-[260px] overflow-auto rounded-lg border border-border">
				{provider.enabled_models.map((m) => (
					<div
						key={m.id}
						className="flex items-center gap-3 border-b border-border-soft px-3 py-2 last:border-b-0"
					>
						<div className="min-w-0 flex-1">
							<div className="mono truncate text-[12.5px] text-t1">{m.model_id}</div>
							{m.display_name !== m.model_id && (
								<div className="truncate text-[11.5px] text-t3">{m.display_name}</div>
							)}
						</div>
						{m.model_id === provider.default_model && (
							<span className="text-[11px] text-t3">default</span>
						)}
						<Switch
							label={`Allow ${m.model_id}`}
							checked={m.is_enabled}
							disabled={toggle.isPending}
							onChange={(v) =>
								toggle.mutate({ providerId: provider.id, modelPk: m.id, is_enabled: v })
							}
						/>
					</div>
				))}
			</div>
		</>
	);
}
