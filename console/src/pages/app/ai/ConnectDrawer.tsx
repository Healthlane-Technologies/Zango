import { useEffect, useState } from 'react';
import {
	aiKeys,
	connectProvider,
	useAvailableProviders,
	usePlatformAccounts,
	type ConnectBody,
	type PlatformAccountOption,
	type Provider,
	type ProviderModelInfo,
} from '@/api/ai';
import { useApiMutation } from '@/api/hooks';
import { api } from '@/api/client';
import {
	buildConfig,
	CredentialFields,
	missingFields,
	ModelPicker,
	ServicePicker,
	keyless,
	suggestedModel,
} from '@/ai/parts';
import { Button, cx, Drawer, Icon, ProviderLogo, SectionTitle, serviceMeta, Skeleton } from '@/ui';

type Mode = 'platform' | 'own';

/**
 * Give an AI account working credentials: link it to a platform AI account, or give it this
 * app's own key. Its agents stay linked; any on a model the new service lacks move to the
 * new default model.
 */
export function ConnectDrawer({
	appId,
	provider,
	onClose,
}: {
	appId: string;
	provider: Provider;
	onClose: () => void;
}) {
	const platform = usePlatformAccounts(appId);
	const available = useAvailableProviders(appId);
	const accounts = platform.data ?? [];

	const [mode, setMode] = useState<Mode | null>(null);
	const [accountUuid, setAccountUuid] = useState('');
	const [platformModel, setPlatformModel] = useState('');

	const [slug, setSlug] = useState(provider.source === 'own' && !provider.is_placeholder ? provider.provider_slug : '');
	const svc = available.data?.find((s) => s.slug === slug);
	const [values, setValues] = useState<Record<string, string>>({});
	const [models, setModels] = useState<ProviderModelInfo[] | null>(null);
	const [selected, setSelected] = useState<string[]>([]);
	const [ownModel, setOwnModel] = useState('');
	const [checking, setChecking] = useState(false);
	const [checkError, setCheckError] = useState<string | null>(null);

	// Start on the platform account in use, else the default one, else this app's own key.
	useEffect(() => {
		if (mode || !platform.isSuccess) return;
		const current = accounts.find((a) => a.uuid === provider.platform_account?.uuid);
		const pick = current ?? accounts.find((a) => a.is_default) ?? accounts[0];
		if (pick) {
			setMode('platform');
			choose(pick);
		} else setMode('own');
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [platform.isSuccess]);

	const account = accounts.find((a) => a.uuid === accountUuid);

	function choose(a: PlatformAccountOption) {
		setAccountUuid(a.uuid);
		const ids = a.models.map((m) => m.id);
		setPlatformModel(
			provider.default_model && ids.includes(provider.default_model) ? provider.default_model : a.default_model,
		);
	}

	const connect = useApiMutation({
		fn: (body: ConnectBody) => connectProvider(appId, provider.id, body),
		invalidate: [aiKeys.providers(appId), aiKeys.agents(appId)],
		success: (r) =>
			r.moved
				? `Connected. ${r.moved} agent(s) moved to ${r.default_model}.`
				: `Connected. ${provider.name} can use the AI now.`,
		onSuccess: onClose,
	});

	const pickService = (s: string) => {
		setSlug(s);
		setValues({});
		setModels(null);
		setCheckError(null);
	};

	const checkKey = async () => {
		if (!svc) return;
		setChecking(true);
		setCheckError(null);
		try {
			const list = await api<{ models: ProviderModelInfo[] }>(
				`/api/v1/apps/${appId}/ai/providers/fetch-models/`,
				'POST',
				{ provider_slug: svc.slug, config: buildConfig(svc, values) },
			).then((r) => (r.models.length ? r.models : svc.supported_models));
			setModels(list);
			setSelected(list.map((m) => m.id));
			const keep = list.find((m) => m.id === provider.default_model);
			setOwnModel(keep?.id ?? suggestedModel(svc, list));
		} catch (err) {
			setCheckError(err instanceof Error ? err.message : String(err));
		} finally {
			setChecking(false);
		}
	};

	const submit = () => {
		if (mode === 'platform' && account)
			connect.mutate({ source: 'platform', account_uuid: account.uuid, default_model: platformModel });
		else if (mode === 'own' && svc)
			connect.mutate({
				source: 'own',
				provider_slug: svc.slug,
				config: buildConfig(svc, values),
				default_model: ownModel,
				model_ids: selected,
			});
	};

	const ready =
		mode === 'platform' ? !!account && !!platformModel : mode === 'own' && !!models && !!ownModel;
	const loading = platform.isLoading || available.isLoading || mode == null;

	return (
		<Drawer
			open
			wide
			onOpenChange={(o) => !o && onClose()}
			title={`Connect ${provider.name}`}
			subtitle="Choose where this app's AI helpers get their key"
			footer={
				<>
					<Button variant="ghost" onClick={onClose}>
						Cancel
					</Button>
					{mode === 'own' && !models ? (
						<Button
							variant="primary"
							loading={checking}
							disabled={!svc || missingFields(svc, values).length > 0}
							onClick={checkKey}
						>
							{keyless(svc) ? 'Continue' : 'Check the key'}
						</Button>
					) : (
						<Button variant="primary" icon="check" loading={connect.isPending} disabled={!ready} onClick={submit}>
							Connect
						</Button>
					)}
				</>
			}
		>
			{loading ? (
				<div className="flex flex-col gap-3">
					<Skeleton height={64} />
					<Skeleton height={140} />
				</div>
			) : (
				<>
					<div className="zai-choice" role="radiogroup" aria-label="Where the key comes from">
						<button
							type="button"
							role="radio"
							aria-checked={mode === 'platform'}
							disabled={!accounts.length}
							className={cx('zai-pick', mode === 'platform' && 'on')}
							onClick={() => setMode('platform')}
						>
							<span className="ic">
								<Icon name="shield" />
							</span>
							<span className="min-w-0 flex-1">
								<b>Use a platform account</b>
								<small>
									{accounts.length
										? 'Set up by your platform admin. No key to manage; spend still counts per app.'
										: 'None set up yet. A platform admin can add one in Settings → AI accounts.'}
								</small>
							</span>
							<span className="zai-radio" aria-hidden>
								{mode === 'platform' && <Icon name="check" />}
							</span>
						</button>
						<button
							type="button"
							role="radio"
							aria-checked={mode === 'own'}
							className={cx('zai-pick', mode === 'own' && 'on')}
							onClick={() => setMode('own')}
						>
							<span className="ic">
								<Icon name="key" />
							</span>
							<span className="min-w-0 flex-1">
								<b>Use this app's own key</b>
								<small>Bring a key from your company's AI account. Only this app uses it.</small>
							</span>
							<span className="zai-radio" aria-hidden>
								{mode === 'own' && <Icon name="check" />}
							</span>
						</button>
					</div>

					{mode === 'platform' && (
						<div className="flex flex-col gap-5">
							<section>
								<SectionTitle>Account</SectionTitle>
								<div className="zai-acc" role="radiogroup" aria-label="Platform account">
									{accounts.map((a) => (
										<button
											key={a.uuid}
											type="button"
											role="radio"
											aria-checked={a.uuid === accountUuid}
											className={cx('zai-svc-t', a.uuid === accountUuid && 'on')}
											onClick={() => choose(a)}
										>
											<ProviderLogo slug={a.provider_slug} size={40} />
											<span className="min-w-0">
												<b>
													{a.name}
													{a.is_default && (
														<span className="zai-default ml-2 align-middle">
															<Icon name="zap" />
															Default
														</span>
													)}
												</b>
												<small>
													{a.description || `${serviceMeta(a.provider_slug).name} · ${a.models.length} models`}
												</small>
											</span>
											<span className="zai-radio" aria-hidden>
												{a.uuid === accountUuid && <Icon name="check" />}
											</span>
										</button>
									))}
								</div>
							</section>
							{account && (
								<section>
									<SectionTitle>Default model for this app</SectionTitle>
									<ModelPicker
										single
										models={account.models}
										selected={[]}
										defaultModel={platformModel}
										onDefault={setPlatformModel}
									/>
								</section>
							)}
						</div>
					)}

					{mode === 'own' && (
						<div className="flex flex-col gap-5">
							<section>
								<SectionTitle>AI service</SectionTitle>
								<ServicePicker services={available.data ?? []} value={slug} onChange={pickService} />
							</section>
							{svc && (
								<section>
									<SectionTitle>{keyless(svc) ? 'Sign-in' : 'Key'}</SectionTitle>
									<CredentialFields
										svc={svc}
										values={values}
										onChange={(n, v) => {
											setValues((cur) => ({ ...cur, [n]: v }));
											setModels(null);
											setCheckError(null);
										}}
									/>
									{checkError && (
										<div className="mt-3 flex gap-2 rounded-[10px] bg-[var(--red-soft)] px-3 py-2.5 text-[12.5px] text-[var(--red-t)]">
											<Icon name="alert" />
											<span>{checkError}</span>
										</div>
									)}
								</section>
							)}
							{models && (
								<section>
									<SectionTitle>Models</SectionTitle>
									<ModelPicker
										models={models}
										selected={selected}
										onSelected={setSelected}
										defaultModel={ownModel}
										onDefault={setOwnModel}
									/>
								</section>
							)}
						</div>
					)}
				</>
			)}
		</Drawer>
	);
}
