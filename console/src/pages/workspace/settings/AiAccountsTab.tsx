import { useState } from 'react';
import { Link } from 'react-router-dom';
import type { AvailableProvider, ProviderModelInfo } from '@/api/ai';
import {
	aiAccountKeys,
	checkAiAccount,
	createAiAccount,
	deleteAiAccount,
	inUseApps,
	updateAiAccount,
	useAiAccounts,
	validateAiAccount,
	type AiAccount,
	type AiAccountApp,
} from '@/api/aiAccounts';
import { useApiMutation } from '@/api/hooks';
import { timeAgo } from '@/format/time';
import {
	buildConfig,
	CredentialFields,
	keyless,
	missingFields,
	ModelPicker,
	ServicePicker,
	Steps,
	suggestedModel,
} from '@/ai/parts';
import {
	Badge,
	Banner,
	Button,
	ConfirmModal,
	Drawer,
	ErrorState,
	Field,
	Icon,
	Input,
	Modal,
	ProviderLogo,
	RowMenu,
	SectionTitle,
	serviceMeta,
	Skeleton,
	SwitchField,
	toast,
	type Tone,
} from '@/ui';

// Platform → Settings → AI accounts. One key per AI service for every app: App Studio
// links new apps' AI helpers to the default account; app admins can pick any account.

const STATUS: Record<AiAccount['status'], [string, Tone]> = {
	connected: ['Connected', 'green'],
	failing: ['Key check failed', 'red'],
	off: ['Off', 'gray'],
};

const money = (n: number | null | undefined) =>
	n == null ? 'No cap' : `$${Number(n).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;

const modelName = (a: AiAccount) =>
	a.models.find((m) => m.id === a.default_model)?.name || a.default_model || '—';

export function AiAccountsTab() {
	const { data, isLoading, error, refetch } = useAiAccounts();
	const [wizard, setWizard] = useState(false);
	const [editing, setEditing] = useState<string | null>(null);
	const [removing, setRemoving] = useState<AiAccount | null>(null);
	const [blocked, setBlocked] = useState<{ account: AiAccount; apps: AiAccountApp[] } | null>(null);

	const update = useApiMutation({
		fn: ({ uuid, ...body }: { uuid: string; is_default?: boolean; is_enabled?: boolean }) =>
			updateAiAccount(uuid, body),
		invalidate: [aiAccountKeys.all],
		success: (r) => r.message,
	});
	const check = useApiMutation({
		fn: (uuid: string) => validateAiAccount(uuid),
		invalidate: [aiAccountKeys.all],
		success: (r) => r.message,
	});
	const remove = useApiMutation({
		fn: (a: AiAccount) => deleteAiAccount(a.uuid),
		invalidate: [aiAccountKeys.all],
		success: 'Account deleted.',
	});

	if (isLoading) return <AccountsSkeleton />;
	if (error || !data)
		return <ErrorState error={error ?? new Error('Could not load the AI accounts.')} onRetry={() => refetch()} />;

	const accounts = data.accounts;
	const current = accounts.find((a) => a.uuid === editing);

	return (
		<>
			{accounts.length === 0 ? (
				<Hero onConnect={() => setWizard(true)} />
			) : (
				<>
					{!accounts.some((a) => a.is_default && a.status === 'connected') && (
						<div className="mb-4">
							<Banner>
								No working default account. New apps built with AI helpers get a placeholder that
								waits for a key. Make a connected account the default to switch them on.
							</Banner>
						</div>
					)}
					<div className="zai-grid">
						{accounts.map((a) => (
							<AccountCard
								key={a.uuid}
								a={a}
								onOpen={() => setEditing(a.uuid)}
								menu={
									<RowMenu
										label={`Actions for ${a.name}`}
										items={[
											{ label: 'Edit', icon: 'pen', onSelect: () => setEditing(a.uuid) },
											{ label: 'Check the key', icon: 'check', onSelect: () => check.mutate(a.uuid) },
											!a.is_default && a.status === 'connected'
												? {
														label: 'Use for new apps',
														icon: 'zap',
														onSelect: () => update.mutate({ uuid: a.uuid, is_default: true }),
													}
												: null,
											a.is_enabled
												? {
														label: 'Turn off',
														icon: 'x',
														disabled: a.is_default,
														onSelect: () => update.mutate({ uuid: a.uuid, is_enabled: false }),
													}
												: {
														label: 'Turn on',
														icon: 'check',
														onSelect: () => update.mutate({ uuid: a.uuid, is_enabled: true }),
													},
											null,
											{
												label: 'Delete',
												icon: 'x',
												danger: true,
												onSelect: () =>
													a.apps?.length
														? setBlocked({ account: a, apps: a.apps })
														: setRemoving(a),
											},
										]}
									/>
								}
							/>
						))}
						<button type="button" className="zai-add" onClick={() => setWizard(true)}>
							<span className="zai-add-i">
								<Icon name="plus" />
							</span>
							Connect another AI service
						</button>
					</div>
					<HowItWorks />
				</>
			)}

			{wizard && (
				<ConnectWizard
					services={data.services}
					first={accounts.length === 0}
					taken={accounts.map((a) => a.name)}
					onClose={() => setWizard(false)}
				/>
			)}
			{current && (
				<AccountDrawer
					key={current.uuid}
					account={current}
					service={data.services.find((s) => s.slug === current.provider_slug)}
					onClose={() => setEditing(null)}
				/>
			)}

			<ConfirmModal
				open={removing != null}
				onOpenChange={(o) => !o && setRemoving(null)}
				title="Delete AI account"
				confirmLabel="Delete"
				danger
				loading={remove.isPending}
				onConfirm={() =>
					removing &&
					remove.mutate(removing, {
						onSettled: () => setRemoving(null),
						onError: (err) => {
							const apps = inUseApps(err);
							if (apps && removing) setBlocked({ account: removing, apps });
						},
					})
				}
			>
				<p className="text-t2">
					Delete <b>{removing?.name}</b> and its saved key? No app uses it. This can't be undone.
				</p>
			</ConfirmModal>

			<Modal
				open={blocked != null}
				onOpenChange={(o) => !o && setBlocked(null)}
				title="This account is in use"
				footer={<Button onClick={() => setBlocked(null)}>Close</Button>}
			>
				<p className="mb-3 text-t2">
					{blocked?.apps.length} app(s) call the AI through <b>{blocked?.account.name}</b>. Switch them
					to another account in each app's AI → Providers, or turn this one off instead.
				</p>
				<AppList apps={blocked?.apps ?? []} />
			</Modal>
		</>
	);
}

function AccountsSkeleton() {
	return (
		<div className="zai-grid">
			{[0, 1].map((i) => (
				<div key={i} className="zai-card" style={{ cursor: 'default' }}>
					<Skeleton width="60%" height={16} />
					<Skeleton height={44} />
					<Skeleton width="40%" />
				</div>
			))}
		</div>
	);
}

function Hero({ onConnect }: { onConnect: () => void }) {
	return (
		<div className="zai-hero">
			<div>
				<Badge tone="violet">AI for every app</Badge>
				<h2 className="mt-3">Connect an AI service once. Every app can use it.</h2>
				<p>
					Apps built with AI helpers link to this account instead of asking each app creator for a
					key. Rotate the key here and every linked app follows.
				</p>
				<div className="zai-points">
					<div>
						<Icon name="shield" />
						<span>
							<b>The key stays here.</b> Stored encrypted, never shown again, never copied into
							an app.
						</span>
					</div>
					<div>
						<Icon name="zap" />
						<span>
							<b>AI works from the first build.</b> No waiting for someone to paste a key.
						</span>
					</div>
					<div>
						<Icon name="pulse" />
						<span>
							<b>Spend stays per app.</b> Each app has its own budget and usage, under a cap you
							set.
						</span>
					</div>
				</div>
				<div className="mt-6 flex gap-2">
					<Button variant="primary" icon="plus" onClick={onConnect}>
						Connect an AI service
					</Button>
				</div>
			</div>
			<div className="zai-orbit" aria-hidden>
				<ProviderLogo slug="anthropic" size={54} />
				<ProviderLogo slug="openai" size={50} />
				<ProviderLogo slug="azure_openai" size={50} />
				<ProviderLogo slug="bedrock" size={50} />
				<div className="zai-orbit-core">
					<Icon name="bot" />
				</div>
			</div>
		</div>
	);
}

function HowItWorks() {
	return (
		<div className="zai-how">
			<div>
				<span className="n">1</span>
				<span>
					<b>Connect once</b>
					<small>Add a key per AI service. The default one is used for new apps.</small>
				</span>
			</div>
			<div>
				<span className="n">2</span>
				<span>
					<b>Apps link to it</b>
					<small>
						App Studio links each new app's AI helpers here. App admins can switch in App → AI.
					</small>
				</span>
			</div>
			<div>
				<span className="n">3</span>
				<span>
					<b>Manage it here</b>
					<small>Replace the key or turn the account off; every linked app follows at once.</small>
				</span>
			</div>
		</div>
	);
}

function AccountCard({
	a,
	onOpen,
	menu,
}: {
	a: AiAccount;
	onOpen: () => void;
	menu: React.ReactNode;
}) {
	const [label, tone] = STATUS[a.status];
	const apps = a.apps?.length ?? 0;
	return (
		<div
			className={`zai-card${a.is_default ? ' def' : ''}${a.is_enabled ? '' : ' off'}`}
			role="button"
			tabIndex={0}
			onClick={onOpen}
			onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && (e.preventDefault(), onOpen())}
		>
			<div className="zai-card-h">
				<ProviderLogo slug={a.provider_slug} size={42} />
				<div className="min-w-0 flex-1">
					<b title={a.name}>{a.name}</b>
					<small>
						{serviceMeta(a.provider_slug).name} · {modelName(a)}
					</small>
				</div>
				<div onClick={(e) => e.stopPropagation()} onKeyDown={(e) => e.stopPropagation()}>
					{menu}
				</div>
			</div>
			<div className="zai-stats">
				<div>
					<small>Apps</small>
					<b>{apps}</b>
				</div>
				<div>
					<small>Models</small>
					<b>{a.models.length || '—'}</b>
				</div>
				<div>
					<small>Cap per app</small>
					<b>{money(a.app_monthly_budget_usd)}</b>
				</div>
			</div>
			<div className="zai-card-f">
				<Badge tone={tone} dot>
					{label}
				</Badge>
				{a.status === 'failing' && a.validation_error ? (
					<span className="err" title={a.validation_error}>
						{a.validation_error}
					</span>
				) : (
					a.last_validated_at && <span>Checked {timeAgo(a.last_validated_at)}</span>
				)}
				{a.is_default && (
					<span className="zai-default ml-auto" title="App Studio links new apps to this account">
						<Icon name="zap" />
						Default for new apps
					</span>
				)}
			</div>
		</div>
	);
}

function AppList({ apps }: { apps: AiAccountApp[] }) {
	if (!apps.length) return <p className="text-t3">No app uses this account yet.</p>;
	return (
		<div className="flex flex-col divide-y divide-[var(--border-soft)] rounded-[10px] border border-[var(--border)]">
			{apps.map((app) => (
				<Link
					key={app.uuid}
					to={`/apps/${app.uuid}/ai?tab=providers`}
					className="flex items-center gap-3 px-3 py-2.5 hover:bg-[var(--hover)]"
				>
					<span className="min-w-0 flex-1">
						<b className="block text-[13px] text-t1">{app.name}</b>
						<small className="text-[12px] text-t3">{app.providers.join(', ')}</small>
					</span>
					<Icon name="ext" />
				</Link>
			))}
		</div>
	);
}

/* ---------- connect a new account ---------- */

function suggestName(slug: string, taken: string[]) {
	const base = `${slug.replace(/_/g, '-')}-main`;
	if (!taken.includes(base)) return base;
	let i = 2;
	while (taken.includes(`${base}-${i}`)) i++;
	return `${base}-${i}`;
}

function ConnectWizard({
	services,
	first,
	taken,
	onClose,
}: {
	services: AvailableProvider[];
	first: boolean;
	taken: string[];
	onClose: () => void;
}) {
	const [step, setStep] = useState(0);
	const [slug, setSlug] = useState('');
	const svc = services.find((s) => s.slug === slug);
	const [values, setValues] = useState<Record<string, string>>({});
	const [checking, setChecking] = useState(false);
	const [checkError, setCheckError] = useState<string | null>(null);
	const [models, setModels] = useState<ProviderModelInfo[]>([]);
	const [selected, setSelected] = useState<string[]>([]);
	const [defaultModel, setDefaultModel] = useState('');
	const [name, setName] = useState('');
	const [cap, setCap] = useState('');
	const [isDefault, setIsDefault] = useState(true);

	const create = useApiMutation({
		fn: () =>
			createAiAccount({
				name: name.trim(),
				provider_slug: slug,
				config: buildConfig(svc, values),
				default_model: defaultModel,
				model_ids: selected,
				app_monthly_budget_usd: cap.trim() === '' ? null : Number(cap),
				is_default: first || isDefault,
			}),
		invalidate: [aiAccountKeys.all],
		success: (r) => `${r.account.name} is connected.`,
		onSuccess: onClose,
	});

	const pick = (s: string) => {
		setSlug(s);
		setValues({});
		setCheckError(null);
		setName(suggestName(s, taken));
	};

	const runCheck = async () => {
		if (!svc) return;
		setChecking(true);
		setCheckError(null);
		try {
			const list = await checkAiAccount({ provider_slug: svc.slug, config: buildConfig(svc, values) });
			const usable = list.length ? list : svc.supported_models;
			setModels(usable);
			setSelected(usable.map((m) => m.id));
			setDefaultModel(suggestedModel(svc, usable));
			setStep(2);
		} catch (err) {
			setCheckError(err instanceof Error ? err.message : String(err));
		} finally {
			setChecking(false);
		}
	};

	const missing = missingFields(svc, values);
	const meta = serviceMeta(slug);

	const footer =
		step === 0 ? (
			<>
				<Button variant="ghost" onClick={onClose}>
					Cancel
				</Button>
				<Button variant="primary" disabled={!svc} onClick={() => setStep(1)}>
					Continue
				</Button>
			</>
		) : step === 1 ? (
			<>
				<Button variant="ghost" className="mr-auto" onClick={() => setStep(0)}>
					Back
				</Button>
				<Button variant="primary" loading={checking} disabled={missing.length > 0} onClick={runCheck}>
					{keyless(svc) ? 'Continue' : 'Check the key'}
				</Button>
			</>
		) : (
			<>
				<Button variant="ghost" className="mr-auto" onClick={() => setStep(1)}>
					Back
				</Button>
				<Button
					variant="primary"
					icon="check"
					loading={create.isPending}
					disabled={!name.trim() || !defaultModel}
					onClick={() => create.mutate()}
				>
					Connect
				</Button>
			</>
		);

	return (
		<Modal
			open
			large
			onOpenChange={(o) => !o && onClose()}
			title="Connect an AI service"
			subtitle="For every app on this platform"
			footer={footer}
		>
			<Steps steps={['Service', keyless(svc) ? 'Sign-in' : 'Key', 'Models & limits']} at={step} />

			{step === 0 && (
				<>
					<p className="mb-3 text-t2">Which AI company should the apps use?</p>
					<ServicePicker services={services} value={slug} onChange={pick} />
				</>
			)}

			{step === 1 && svc && (
				<div className="grid gap-5 md:grid-cols-[minmax(0,1fr)_220px]">
					<div>
						<CredentialFields
							svc={svc}
							values={values}
							onChange={(n, v) => {
								setValues((cur) => ({ ...cur, [n]: v }));
								setCheckError(null);
							}}
						/>
						{checkError && (
							<div className="mt-3 flex gap-2 rounded-[10px] bg-[var(--red-soft)] px-3 py-2.5 text-[12.5px] text-[var(--red-t)]">
								<Icon name="alert" />
								<span>{checkError}</span>
							</div>
						)}
					</div>
					<aside className="flex flex-col items-start gap-2 rounded-[12px] border border-[var(--border-soft)] bg-[var(--bg)] p-4">
						<ProviderLogo slug={slug} size={44} />
						<b className="mt-1 text-[13.5px] text-t1">{meta.name}</b>
						<small className="text-[12px] leading-[1.45] text-t3">{meta.tagline}</small>
						<small className="mt-2 text-[12px] leading-[1.45] text-t3">
							{keyless(svc)
								? 'No key to enter. Next, pick the models apps may use.'
								: 'We make one tiny call to check the key and list the models it can use.'}
						</small>
					</aside>
				</div>
			)}

			{step === 2 && (
				<div className="flex flex-col gap-5">
					<div className="flex items-center gap-3 rounded-[12px] border border-[var(--green-soft)] bg-[var(--green-soft)] px-3.5 py-2.5 text-[12.5px] text-[var(--green-t)]">
						<Icon name="check" />
						<span>
							{keyless(svc) ? 'Ready.' : 'The key works.'} {models.length} model
							{models.length === 1 ? '' : 's'} available.
						</span>
					</div>
					<div>
						<SectionTitle>Models apps may use</SectionTitle>
						<ModelPicker
							models={models}
							selected={selected}
							onSelected={setSelected}
							defaultModel={defaultModel}
							onDefault={setDefaultModel}
						/>
					</div>
					<div className="grid gap-4 sm:grid-cols-2">
						<Field label="Account name" hint="How app admins see it when they pick an account.">
							{(p) => <Input {...p} value={name} onChange={(e) => setName(e.target.value)} />}
						</Field>
						<Field label="Monthly cap per app (USD)" hint="Each linked app gets its own budget, at most this. Blank = no cap.">
							{(p) => (
								<Input
									{...p}
									type="number"
									min={0}
									step="1"
									placeholder="No cap"
									value={cap}
									onChange={(e) => setCap(e.target.value)}
								/>
							)}
						</Field>
					</div>
					{first ? (
						<p className="text-[12.5px] text-t3">
							Your first account is used for new apps automatically.
						</p>
					) : (
						<SwitchField
							checked={isDefault}
							onChange={setIsDefault}
							label="Use for new apps"
							hint="App Studio links the AI helpers of newly built apps to this account."
						/>
					)}
				</div>
			)}
		</Modal>
	);
}

/* ---------- edit an account ---------- */

function AccountDrawer({
	account,
	service,
	onClose,
}: {
	account: AiAccount;
	service: AvailableProvider | undefined;
	onClose: () => void;
}) {
	const [name, setName] = useState(account.name);
	const [description, setDescription] = useState(account.description);
	const [cap, setCap] = useState(
		account.app_monthly_budget_usd == null ? '' : String(account.app_monthly_budget_usd),
	);
	const [values, setValues] = useState<Record<string, string>>({});
	const [models, setModels] = useState<ProviderModelInfo[]>(account.models);
	const [selected, setSelected] = useState<string[]>(account.models.map((m) => m.id));
	const [defaultModel, setDefaultModel] = useState(account.default_model);
	const [loading, setLoading] = useState(false);

	const typedKey = Object.values(values).some((v) => v.trim());

	const save = useApiMutation({
		fn: () =>
			updateAiAccount(account.uuid, {
				name: name.trim(),
				description,
				app_monthly_budget_usd: cap.trim() === '' ? null : Number(cap),
				default_model: defaultModel,
				model_ids: selected,
				models,
				...(typedKey && service ? { config: buildConfig(service, values, account.masked_config) } : {}),
			}),
		invalidate: [aiAccountKeys.all],
		success: (r) => r.message,
		onSuccess: onClose,
	});

	/** Load every model the key can use, to allow more. */
	const loadModels = async () => {
		if (!service) return;
		setLoading(true);
		try {
			const list = await checkAiAccount({
				provider_slug: service.slug,
				config: buildConfig(service, values, account.masked_config),
				account_uuid: account.uuid,
			});
			const known = new Set(list.map((m) => m.id));
			setModels([...list, ...models.filter((m) => !known.has(m.id))]);
		} catch (err) {
			toast.error(err instanceof Error ? err.message : String(err));
		} finally {
			setLoading(false);
		}
	};

	const [label, tone] = STATUS[account.status];

	return (
		<Drawer
			open
			onOpenChange={(o) => !o && onClose()}
			title={
				<span className="flex items-center gap-3">
					<ProviderLogo slug={account.provider_slug} size={30} />
					{account.name}
				</span>
			}
			actions={
				<Badge tone={tone} dot>
					{label}
				</Badge>
			}
			footer={
				<>
					<Button variant="ghost" onClick={onClose}>
						Cancel
					</Button>
					<Button
						variant="primary"
						loading={save.isPending}
						disabled={!name.trim() || !defaultModel}
						onClick={() => save.mutate()}
					>
						{typedKey ? 'Check the key and save' : 'Save'}
					</Button>
				</>
			}
		>
			<div className="flex flex-col gap-6">
				{account.status === 'failing' && account.validation_error && (
					<div className="flex gap-2 rounded-[10px] bg-[var(--red-soft)] px-3 py-2.5 text-[12.5px] text-[var(--red-t)]">
						<Icon name="alert" />
						<span>
							The last check failed: {account.validation_error}. Linked apps can't use the AI until
							the key works.
						</span>
					</div>
				)}

				<section>
					<SectionTitle>{keyless(service) ? 'Sign-in' : 'Key'}</SectionTitle>
					{service ? (
						<CredentialFields
							svc={service}
							values={values}
							saved={account.masked_config}
							onChange={(n, v) => setValues((cur) => ({ ...cur, [n]: v }))}
						/>
					) : (
						<p className="text-t3">This AI service is no longer installed.</p>
					)}
				</section>

				<section>
					<SectionTitle
						action={
							<Button size="xs" variant="ghost" loading={loading} onClick={loadModels}>
								Load all models
							</Button>
						}
					>
						Models apps may use
					</SectionTitle>
					<ModelPicker
						models={models}
						selected={selected}
						onSelected={setSelected}
						defaultModel={defaultModel}
						onDefault={setDefaultModel}
					/>
				</section>

				<section className="flex flex-col gap-4">
					<SectionTitle>Details</SectionTitle>
					<Field label="Account name">
						{(p) => <Input {...p} value={name} onChange={(e) => setName(e.target.value)} />}
					</Field>
					<Field label="Note" hint="Optional. Shown to app admins when they pick an account.">
						{(p) => (
							<Input {...p} value={description} onChange={(e) => setDescription(e.target.value)} />
						)}
					</Field>
					<Field label="Monthly cap per app (USD)" hint="Applies when an app links to this account. Blank = no cap.">
						{(p) => (
							<Input
								{...p}
								type="number"
								min={0}
								placeholder="No cap"
								value={cap}
								onChange={(e) => setCap(e.target.value)}
							/>
						)}
					</Field>
				</section>

				<section>
					<SectionTitle>Apps using it</SectionTitle>
					<AppList apps={account.apps ?? []} />
				</section>
			</div>
		</Drawer>
	);
}
