import { useEffect, useMemo, useState, type ReactNode } from 'react';

import { appKeys } from '@/api/apps';

import {
	deleteSamlProvider,
	samlKeys,
	saveAuthConfig,
	useAuthConfig,
	useSamlProviders,
	type SamlProvider,
} from '@/api/auth';

import { useApiMutation, useAppId } from '@/api/hooks';

import {
	Badge,
	Button,
	Card,
	CardBody,
	CardHeader,
	ConfirmModal,
	EmptyState,
	ErrorState,
	Field,
	FieldGroup,
	Input,
	Page,
	PageHeader,
	RowMenu,
	SaveBar,
	Skeleton,
	SwitchRow,
	Table,
} from '@/ui';

import { applyForm, humanSeconds, toForm, validate, type AuthForm } from './auth/authForm';

import { ChipSelect } from './auth/controls';
import { SamlDrawer } from './auth/SamlDrawer';

const err = (e: string | undefined) => (e ? <span className="text-red-t">{e}</span> : undefined);

function NumberField({
	label,
	value,
	onChange,
	error,
	hint,
	placeholder,
	suffix,
}: {
	label: ReactNode;
	value: string;
	onChange: (v: string) => void;
	error?: string;
	hint?: ReactNode;
	placeholder?: string;
	suffix?: string;
}) {
	return (
		<Field label={label} error={error} hint={hint}>
			{(p) => (
				<div className="relative">
					<Input
						{...p}
						className={suffix ? '!pr-[76px]' : undefined}
						inputMode="numeric"
						placeholder={placeholder}
						value={value}
						onChange={(e) => onChange(e.target.value.replace(/[^\d]/g, ''))}
					/>
					{suffix && (
						<span className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-[12px] text-t4">
							{suffix}
						</span>
					)}
				</div>
			)}
		</Field>
	);
}

function SamlProvidersCard({ app, ssoOn }: { app: string; ssoOn: boolean }) {
	const { data, isLoading, error, refetch } = useSamlProviders(app);
	const [editing, setEditing] = useState<SamlProvider | null>(null);
	const [adding, setAdding] = useState(false);
	const [deleting, setDeleting] = useState<SamlProvider | null>(null);
	const remove = useApiMutation({
		fn: (p: SamlProvider) => deleteSamlProvider(app, p.id),
		invalidate: [samlKeys.list(app)],
		success: (_, p) => `${p.label} removed`,
		onSuccess: () => setDeleting(null),
	});

	return (
		<>
			<div className="mb-2 mt-6 flex items-end gap-3">
				<div>
					<h3 className="text-[13.5px]">SAML providers</h3>
					<p className="text-t3">
						{ssoOn
							? 'Shown on the sign-in page while SSO is on.'
							: 'Turn on SSO above to offer these on the sign-in page.'}
					</p>
				</div>
				<Button size="sm" icon="plus" className="ml-auto" onClick={() => setAdding(true)}>
					Add provider
				</Button>
			</div>
			<Table
				columns={[
					{
						key: 'label',
						header: 'Provider',
						cell: (p) => (
							<div className="nm">
								<div className="min-w-0">
									<b>{p.label}</b>
									<small className="mono max-w-[380px] truncate">{p.idp_entityId}</small>
								</div>
							</div>
						),
					},
					{
						key: 'sso',
						header: 'Sign-on URL',
						cell: (p) => (
							<span className="mono inline-block max-w-[260px] truncate align-middle text-t3">
								{p.idp_sso}
							</span>
						),
					},
					{
						key: 'status',
						header: 'Status',
						cell: (p) =>
							p.is_active ? (
								<Badge tone="green" dot>
									Active
								</Badge>
							) : (
								<Badge tone="gray">Inactive</Badge>
							),
					},
					{
						key: 'actions',
						header: '',
						align: 'right',
						cell: (p) => (
							<RowMenu
								label={`Actions for ${p.label}`}
								items={[
									{ label: 'Edit', icon: 'cog', onSelect: () => setEditing(p) },
									null,
									{ label: 'Remove', icon: 'x', danger: true, onSelect: () => setDeleting(p) },
								]}
							/>
						),
					},
				]}
				rows={data}
				rowKey={(p) => p.id}
				loading={isLoading}
				error={error}
				onRetry={() => refetch()}
				onRowClick={setEditing}
				empty={
					<EmptyState title="No SAML providers">
						Add Okta, Azure AD or another SAML 2.0 identity provider.
					</EmptyState>
				}
			/>
			<SamlDrawer
				app={app}
				open={adding || !!editing}
				onOpenChange={(o) => {
					if (!o) {
						setAdding(false);
						setEditing(null);
					}
				}}
				provider={editing}
			/>
			<ConfirmModal
				open={!!deleting}
				onOpenChange={(o) => !o && setDeleting(null)}
				title={`Remove ${deleting?.label}?`}
				confirmLabel="Remove"
				danger
				loading={remove.isPending}
				onConfirm={() => deleting && remove.mutate(deleting)}
			>
				People who sign in through this provider won't be able to until it is added again.
			</ConfirmModal>
		</>
	);
}

export function AuthPage() {
	const appId = useAppId();
	const { data, isLoading, error, refetch } = useAuthConfig(appId);
	const stored = data?.authConfig;
	const original = useMemo(() => (stored ? toForm(stored) : null), [stored]);
	const [form, setForm] = useState<AuthForm | null>(null);
	const [submitted, setSubmitted] = useState(false);

	useEffect(() => {
		if (original) setForm(original);
	}, [original]);

	const platform = {
		ttl: stored?.session_policy?.platform_token_ttl,
		warn: stored?.session_policy?.platform_session_warn_after,
		expire: stored?.session_policy?.platform_session_expire_after,
	};

	const save = useApiMutation({
		fn: (f: AuthForm) => saveAuthConfig(appId, applyForm(stored!, f)),
		invalidate: [appKeys.detail(appId)],
		success: 'Authentication settings saved',
		onSuccess: () => setSubmitted(false),
	});

	if (error) {
		return (
			<Page>
				<PageHeader title="Authentication" />
				<Card>
					<ErrorState error={error} onRetry={() => refetch()} />
				</Card>
			</Page>
		);
	}

	if (isLoading || !form || !original) {
		return (
			<Page>
				<PageHeader title="Authentication" description="How people sign in to this app." />
				<Card>
					<CardBody className="grid gap-3">
						<Skeleton width="40%" />
						<Skeleton width="70%" />
						<Skeleton width="55%" />
					</CardBody>
				</Card>
			</Page>
		);
	}

	const set = <K extends keyof AuthForm>(k: K, v: AuthForm[K]) =>
		setForm((f) => (f ? { ...f, [k]: v } : f));
	const dirty = JSON.stringify(form) !== JSON.stringify(original);
	const errors = submitted ? validate(form, platform) : {};
	const inherit = (s: number | undefined) =>
		s === undefined ? 'Platform default' : `Platform default · ${humanSeconds(s)}`;

	const onSave = () => {
		setSubmitted(true);
		if (Object.keys(validate(form, platform)).length === 0) save.mutate(form);
	};

	return (
		<div className="page fi" style={{ maxWidth: 860 }}>
			<PageHeader
				title="Authentication"
				description={`How people sign in to ${data?.name ?? 'this app'}.`}
			/>

			<Card className="mb-4">
				<CardHeader title="Sign-in methods" />
				<div className="card-b" style={{ padding: '4px 16px' }}>
					{errors.methods && <p className="pt-2.5 text-[12px] text-red-t">{errors.methods}</p>}
					<SwitchRow
						title="Password"
						description="Users sign in with a username and password."
						checked={form.password}
						onChange={(v) => set('password', v)}
					>
						<FieldGroup
							label="Username"
							hint={err(errors.usernames) ?? 'What people can type as their username.'}
						>
							<ChipSelect
								label="Allowed usernames"
								options={[
									{ value: 'email', label: 'Email' },
									{ value: 'phone', label: 'Mobile number' },
								]}
								value={form.usernames}
								onChange={(v) => set('usernames', v)}
							/>
						</FieldGroup>
						<div className="grid grid-cols-2 items-end gap-[14px]">
							<SwitchRow
								title="Forgot password"
								description="Let people reset it themselves."
								checked={form.forgotPassword}
								onChange={(v) => set('forgotPassword', v)}
							/>
							{form.forgotPassword && (
								<NumberField
									label="Reset link expiry"
									suffix="hours"
									value={form.resetLinkHours}
									onChange={(v) => set('resetLinkHours', v)}
									error={errors.resetLinkHours}
								/>
							)}
						</div>
					</SwitchRow>
					<SwitchRow
						title="One-time password"
						description="A code sent by email or SMS; no password needed."
						checked={form.otp}
						onChange={(v) => set('otp', v)}
					>
						<div className="grid grid-cols-2 gap-[14px]">
							<FieldGroup label="Send codes by" hint={err(errors.otpMethods)}>
								<ChipSelect
									label="OTP delivery"
									options={[
										{ value: 'email', label: 'Email' },
										{ value: 'sms', label: 'SMS' },
									]}
									value={form.otpMethods}
									onChange={(v) => set('otpMethods', v)}
								/>
							</FieldGroup>
							<NumberField
								label="Code expiry"
								suffix="seconds"
								value={form.otpExpiry}
								onChange={(v) => set('otpExpiry', v)}
								error={errors.otpExpiry}
							/>
						</div>
					</SwitchRow>
					<SwitchRow
						title="SSO · SAML 2.0"
						description="Sign in through an identity provider configured below."
						checked={form.sso}
						onChange={(v) => set('sso', v)}
					/>
					<SwitchRow
						title="OpenID Connect"
						description="Sign in with Google or Microsoft accounts."
						checked={form.oidc}
						onChange={(v) => set('oidc', v)}
					/>
				</div>
			</Card>

			<Card className="mb-4">
				<CardHeader title="Two-factor authentication" />
				<div className="card-b" style={{ padding: '4px 16px' }}>
					<SwitchRow
						title="Require for everyone"
						description="Roles and individual users can also require it on their own."
						checked={form.twoFa}
						onChange={(v) => set('twoFa', v)}
					>
						<FieldGroup label="Allowed methods" hint={err(errors.twoFaMethods)}>
							<ChipSelect
								label="Allowed 2FA methods"
								options={[
									{ value: 'email', label: 'Email' },
									{ value: 'sms', label: 'SMS' },
									{ value: 'totp', label: 'Authenticator app' },
								]}
								value={form.twoFaMethods}
								onChange={(v) => set('twoFaMethods', v)}
							/>
						</FieldGroup>
					</SwitchRow>
				</div>
			</Card>

			<Card className="mb-4">
				<CardHeader title="Session policy" />
				<CardBody className="grid grid-cols-2 gap-[14px]">
					<NumberField
						label="Sign out after inactivity"
						suffix="seconds"
						placeholder={inherit(platform.expire)}
						value={form.expireAfter}
						onChange={(v) => set('expireAfter', v)}
						error={errors.expireAfter}
						hint={
							form.expireAfter
								? humanSeconds(Number(form.expireAfter))
								: 'Leave blank to use the platform default.'
						}
					/>
					<NumberField
						label="Warn after inactivity"
						suffix="seconds"
						placeholder={inherit(platform.warn)}
						value={form.warnAfter}
						onChange={(v) => set('warnAfter', v)}
						error={errors.warnAfter}
						hint={
							form.warnAfter
								? humanSeconds(Number(form.warnAfter))
								: 'Must be shorter than the sign-out time.'
						}
					/>
					<NumberField
						label="API token lifetime"
						suffix="seconds"
						placeholder={inherit(platform.ttl)}
						value={form.tokenTtl}
						onChange={(v) => set('tokenTtl', v)}
						error={errors.tokenTtl}
						hint={
							form.tokenTtl ? humanSeconds(Number(form.tokenTtl)) : '0 means tokens never expire.'
						}
					/>
					<NumberField
						label="Concurrent sessions per user"
						value={form.maxSessions}
						onChange={(v) => set('maxSessions', v)}
						error={errors.maxSessions}
						hint="0 means unlimited."
					/>
					<div className="col-span-2 -my-1">
						<SwitchRow
							title="Sign out everywhere on password change"
							description="End a user's other sessions when their password changes."
							checked={form.logoutOnPasswordChange}
							onChange={(v) => set('logoutOnPasswordChange', v)}
						/>
					</div>
				</CardBody>
			</Card>

			<Card className="mb-4">
				<CardHeader title="Password policy" />
				<CardBody className="grid grid-cols-2 gap-[14px]">
					<NumberField
						label="Minimum length"
						suffix="characters"
						value={form.minLength}
						onChange={(v) => set('minLength', v)}
						error={errors.minLength}
					/>
					<FieldGroup label="Must include">
						<ChipSelect
							label="Password requirements"
							options={[
								{ value: 'requireUppercase', label: 'Uppercase' },
								{ value: 'requireLowercase', label: 'Lowercase' },
								{ value: 'requireNumbers', label: 'Numbers' },
								{ value: 'requireSpecial', label: 'Symbols' },
							]}
							value={(
								[
									'requireUppercase',
									'requireLowercase',
									'requireNumbers',
									'requireSpecial',
								] as const
							).filter((k) => form[k])}
							onChange={(v) =>
								setForm((f) =>
									f
										? {
												...f,
												requireUppercase: v.includes('requireUppercase'),
												requireLowercase: v.includes('requireLowercase'),
												requireNumbers: v.includes('requireNumbers'),
												requireSpecial: v.includes('requireSpecial'),
											}
										: f,
								)
							}
						/>
					</FieldGroup>
					<NumberField
						label="Expires after"
						suffix="days"
						value={form.expiryDays}
						onChange={(v) => set('expiryDays', v)}
						error={errors.expiryDays}
					/>
					<NumberField
						label="Can't reuse the last"
						suffix="passwords"
						value={form.historyCount}
						onChange={(v) => set('historyCount', v)}
						error={errors.historyCount}
						hint="0 allows reuse."
					/>
					<div className="col-span-2 -my-1">
						<SwitchRow
							title="Users can change their password"
							checked={form.allowChange}
							onChange={(v) => set('allowChange', v)}
						/>
					</div>
				</CardBody>
			</Card>

			<SamlProvidersCard app={appId} ssoOn={form.sso} />

			<SaveBar
				dirty={dirty}
				saving={save.isPending}
				onSave={onSave}
				onDiscard={() => {
					setForm(original);
					setSubmitted(false);
				}}
			/>
		</div>
	);
}
