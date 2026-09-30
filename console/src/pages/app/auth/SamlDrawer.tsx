import { useEffect, useState, type FormEvent, type ReactNode } from 'react';

import { useMutation, useQueryClient } from '@tanstack/react-query';

import { ApiError } from '@/api/client';

import {
	createSamlProvider,
	samlKeys,
	updateSamlProvider,
	type SamlInput,
	type SamlProvider,
} from '@/api/auth';

import { Button, Drawer, Field, Input, Select, SwitchRow, Tabs, Textarea, toast } from '@/ui';

const SIGNATURE_ALGORITHMS: Array<[string, string]> = [
	['http://www.w3.org/2000/09/xmldsig#rsa-sha1', 'RSA-SHA1'],
	['http://www.w3.org/2000/09/xmldsig#dsa-sha1', 'DSA-SHA1'],
	['http://www.w3.org/2001/04/xmldsig-more#rsa-sha256', 'RSA-SHA256'],
	['http://www.w3.org/2001/04/xmldsig-more#rsa-sha384', 'RSA-SHA384'],
	['http://www.w3.org/2001/04/xmldsig-more#rsa-sha512', 'RSA-SHA512'],
];
const DIGEST_ALGORITHMS: Array<[string, string]> = [
	['http://www.w3.org/2000/09/xmldsig#sha1', 'SHA1'],
	['http://www.w3.org/2001/04/xmlenc#sha256', 'SHA256'],
	['http://www.w3.org/2001/04/xmldsig-more#sha384', 'SHA384'],
	['http://www.w3.org/2001/04/xmlenc#sha512', 'SHA512'],
];
const COMPARISONS = ['exact', 'minimum', 'maximum', 'better'];

// SAMLModel boolean security flags, with defaults from apps/appauth/models.py.
const SECURITY_FLAGS: Array<[string, string, boolean]> = [
	['security_authnRequestsSigned', 'Sign authentication requests', false],
	['security_logoutRequestSigned', 'Sign logout requests', false],
	['security_logoutResponseSigned', 'Sign logout responses', false],
	['security_signMetadata', 'Sign metadata', false],
	['security_nameIdEncrypted', 'Encrypt NameID', false],
	['security_wantMessagesSigned', 'Require signed messages', false],
	['security_wantAssertionsSigned', 'Require signed assertions', false],
	['security_wantAssertionsEncrypted', 'Require encrypted assertions', false],
	['security_wantNameId', 'Require NameID', true],
	['security_wantNameIdEncrypted', 'Require encrypted NameID', false],
	['security_wantAttributeStatement', 'Require attribute statement', true],
	[
		'security_rejectUnsolicitedResponsesWithInResponseTo',
		'Reject unsolicited responses with InResponseTo',
		false,
	],
	['security_requestedAuthnContext', 'Request authentication context', true],
];

const REQUIRED = [
	'label',
	'idp_entityId',
	'idp_sso',
	'idp_x509cert',
	'sp_entityId',
	'sp_acsURL',
] as const;

type Form = Record<string, string | boolean>;

function initial(p: SamlProvider | null | undefined): Form {
	const f: Form = {
		label: '',
		is_active: true,
		is_strict: true,
		is_debug_true: false,
		idp_entityId: '',
		idp_sso: '',
		idp_slo: '',
		idp_x509cert: '',
		sp_entityId: '',
		sp_acsURL: '',
		sp_slo: '',
		sp_x509cert: '',
		sp_privatekey: '',
		security_signatureAlgorithm: SIGNATURE_ALGORITHMS[0][0],
		security_digestAlgorithm: DIGEST_ALGORITHMS[0][0],
		security_requestedAuthnContextComparison: 'exact',
		name_id_format: 'urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified',
	};
	for (const [k, , d] of SECURITY_FLAGS) f[k] = d;
	if (p)
		for (const k of Object.keys(f))
			if (p[k as keyof SamlProvider] != null) f[k] = p[k as keyof SamlProvider] as string | boolean;
	return f;
}

function serverErrors(err: unknown): Record<string, string> {
	if (!(err instanceof ApiError)) return {};
	const errors =
		(err.body as { response?: { errors?: Record<string, string[]> } })?.response?.errors ?? {};
	return Object.fromEntries(Object.entries(errors).map(([k, v]) => [k, v.join(' ')]));
}

export function SamlDrawer({
	app,
	open,
	onOpenChange,
	provider,
}: {
	app: string;
	open: boolean;
	onOpenChange: (o: boolean) => void;
	provider?: SamlProvider | null;
}) {
	const qc = useQueryClient();
	const [form, setForm] = useState<Form>(() => initial(provider));
	const [tab, setTab] = useState<'basic' | 'security'>('basic');
	const [errors, setErrors] = useState<Record<string, string>>({});

	useEffect(() => {
		if (open) {
			setForm(initial(provider));
			setTab('basic');
			setErrors({});
		}
	}, [open, provider]);

	const mutation = useMutation({
		mutationFn: (body: Partial<SamlInput>) =>
			provider ? updateSamlProvider(app, provider.id, body) : createSamlProvider(app, body),
		onSuccess: async () => {
			await qc.invalidateQueries({ queryKey: samlKeys.list(app) });
			toast.success(provider ? 'SAML provider updated' : 'SAML provider added');
			onOpenChange(false);
		},
		onError: (err) => {
			const fieldErrors = serverErrors(err);
			setErrors(fieldErrors);
			if (
				Object.keys(fieldErrors).some(
					(k) =>
						!REQUIRED.includes(k as (typeof REQUIRED)[number]) &&
						!k.startsWith('idp_') &&
						!k.startsWith('sp_'),
				)
			) {
				setTab('security');
			}
			toast.error(err.message);
		},
	});

	const set = (k: string, v: string | boolean) => setForm((f) => ({ ...f, [k]: v }));
	const text = (
		k: string,
		label: ReactNode,
		opts: { hint?: string; multiline?: boolean; mono?: boolean } = {},
	) => (
		<Field key={k} label={label} error={errors[k]} hint={opts.hint}>
			{(p) =>
				opts.multiline ? (
					<Textarea
						{...p}
						rows={4}
						className="mono !text-[11.5px]"
						value={String(form[k])}
						onChange={(e) => set(k, e.target.value)}
					/>
				) : (
					<Input
						{...p}
						className={opts.mono ? 'mono' : undefined}
						value={String(form[k])}
						onChange={(e) => set(k, e.target.value)}
					/>
				)
			}
		</Field>
	);

	const submit = (e: FormEvent) => {
		e.preventDefault();
		const missing = Object.fromEntries(
			REQUIRED.filter((k) => !String(form[k]).trim()).map((k) => [k, 'Required']),
		);
		setErrors(missing);
		if (Object.keys(missing).length) {
			setTab('basic');
			return;
		}
		mutation.mutate(form as Partial<SamlInput>);
	};

	return (
		<Drawer
			open={open}
			onOpenChange={onOpenChange}
			title={provider ? `Edit ${provider.label}` : 'Add SAML provider'}
			subtitle="Connect an identity provider such as Okta, Azure AD or OneLogin."
			footer={
				<>
					<Button onClick={() => onOpenChange(false)}>Cancel</Button>
					<Button variant="primary" type="submit" form="saml-form" loading={mutation.isPending}>
						{provider ? 'Save changes' : 'Add provider'}
					</Button>
				</>
			}
		>
			<Tabs
				className="-mx-5 -mt-5 mb-5"
				value={tab}
				onChange={setTab}
				items={[
					{ value: 'basic', label: 'Connection' },
					{ value: 'security', label: 'Security' },
				]}
			/>
			<form id="saml-form" className="grid gap-4" onSubmit={submit} noValidate>
				{tab === 'basic' ? (
					<>
						{text('label', 'Label', { hint: 'Shown on the sign-in button.' })}
						<div className="-my-2">
							<SwitchRow
								title="Active"
								description="Inactive providers are hidden from the sign-in page."
								checked={!!form.is_active}
								onChange={(v) => set('is_active', v)}
							/>
						</div>
						<h4 className="mt-2 text-[12.5px] text-t3">Identity provider</h4>
						{text('idp_entityId', 'Entity ID', { mono: true })}
						{text('idp_sso', 'Single sign-on URL', { mono: true })}
						{text('idp_slo', 'Single logout URL', { mono: true, hint: 'Optional.' })}
						{text('idp_x509cert', 'x509 certificate', { multiline: true, hint: 'PEM format.' })}
						<h4 className="mt-2 text-[12.5px] text-t3">Service provider (this app)</h4>
						{text('sp_entityId', 'Entity ID', { mono: true })}
						{text('sp_acsURL', 'ACS URL', { mono: true })}
						{text('sp_slo', 'Single logout URL', { mono: true, hint: 'Optional.' })}
						{text('sp_x509cert', 'x509 certificate', {
							multiline: true,
							hint: 'Optional. Needed to sign requests.',
						})}
						{text('sp_privatekey', 'Private key', {
							multiline: true,
							hint: 'Optional. Needed to sign requests.',
						})}
					</>
				) : (
					<>
						<div className="grid grid-cols-2 gap-[14px]">
							<Field label="Signature algorithm" error={errors.security_signatureAlgorithm}>
								{(p) => (
									<Select
										{...p}
										value={String(form.security_signatureAlgorithm)}
										onChange={(e) => set('security_signatureAlgorithm', e.target.value)}
									>
										{SIGNATURE_ALGORITHMS.map(([v, l]) => (
											<option key={v} value={v}>
												{l}
											</option>
										))}
									</Select>
								)}
							</Field>
							<Field label="Digest algorithm" error={errors.security_digestAlgorithm}>
								{(p) => (
									<Select
										{...p}
										value={String(form.security_digestAlgorithm)}
										onChange={(e) => set('security_digestAlgorithm', e.target.value)}
									>
										{DIGEST_ALGORITHMS.map(([v, l]) => (
											<option key={v} value={v}>
												{l}
											</option>
										))}
									</Select>
								)}
							</Field>
							<Field label="Authentication context comparison">
								{(p) => (
									<Select
										{...p}
										value={String(form.security_requestedAuthnContextComparison)}
										onChange={(e) =>
											set('security_requestedAuthnContextComparison', e.target.value)
										}
									>
										{COMPARISONS.map((c) => (
											<option key={c} value={c}>
												{c[0].toUpperCase() + c.slice(1)}
											</option>
										))}
									</Select>
								)}
							</Field>
						</div>
						{text('name_id_format', 'NameID format', { mono: true })}
						<div>
							<SwitchRow
								title="Strict mode"
								description="Reject unsigned or unencrypted messages that should be."
								checked={!!form.is_strict}
								onChange={(v) => set('is_strict', v)}
							/>
							<SwitchRow
								title="Debug mode"
								description="Log SAML errors. Turn off in production."
								checked={!!form.is_debug_true}
								onChange={(v) => set('is_debug_true', v)}
							/>
							{SECURITY_FLAGS.map(([k, label]) => (
								<SwitchRow key={k} title={label} checked={!!form[k]} onChange={(v) => set(k, v)} />
							))}
						</div>
					</>
				)}
			</form>
		</Drawer>
	);
}
