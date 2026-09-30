import { useEffect, useState, type FormEvent } from 'react';

import { useApiMutation } from '@/api/hooks';

import { createUser, updateUser, userKeys, type AppUser, type UserInput } from '@/api/users';

import { Button, Drawer, Field, FieldGroup, Input, Switch } from '@/ui';

import { ChipSelect } from '../auth/controls';

const TWO_FA_METHODS = [
	{ value: 'email', label: 'Email' },
	{ value: 'sms', label: 'SMS' },
	{ value: 'totp', label: 'Authenticator app' },
];

interface Props {
	app: string;
	open: boolean;
	onOpenChange: (o: boolean) => void;
	/** Omit to invite a new user. */
	user?: AppUser | null;
	roleOptions: Array<{ id: number; label: string }>;
	/** Dial code for new numbers, e.g. "+91" (the app's default country). */
	defaultDialCode: string;
}

interface FormState {
	name: string;
	email: string;
	dialCode: string;
	phone: string;
	password: string;
	roles: number[];
	twoFaRequired: boolean;
	twoFaMethods: string[];
}

function initial(user: AppUser | null | undefined, dial: string): FormState {
	const code = user?.pn_country_code || dial;
	const mobile = user?.mobile ?? '';
	const tfa = user?.auth_config?.two_factor_auth;
	return {
		name: user?.name ?? '',
		email: user?.email ?? '',
		dialCode: code,
		phone: mobile.startsWith(code) ? mobile.slice(code.length) : mobile,
		password: '',
		roles: user?.roles.map((r) => r.id) ?? [],
		twoFaRequired: tfa?.required ?? false,
		twoFaMethods: tfa?.allowed_methods ?? tfa?.allowedMethods ?? [],
	};
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function validate(f: FormState): Partial<Record<keyof FormState, string>> {
	const e: Partial<Record<keyof FormState, string>> = {};
	if (!f.name.trim()) e.name = 'Enter a name';
	if (!f.email.trim() && !f.phone.trim()) e.email = 'Enter an email or a mobile number';
	if (f.email.trim() && !EMAIL_RE.test(f.email.trim())) e.email = 'Enter a valid email';
	if (f.phone.trim() && !/^\d{6,14}$/.test(f.phone.trim()))
		e.phone = 'Digits only, without the country code';
	if (!/^\+\d{1,4}$/.test(f.dialCode.trim())) e.dialCode = 'e.g. +91';
	if (f.roles.length === 0) e.roles = 'Pick at least one role';
	if (f.twoFaRequired && f.twoFaMethods.length === 0) e.twoFaMethods = 'Pick at least one method';
	return e;
}

export function UserDrawer({ app, open, onOpenChange, user, roleOptions, defaultDialCode }: Props) {
	const editing = !!user;
	const [form, setForm] = useState(() => initial(user, defaultDialCode));
	const [submitted, setSubmitted] = useState(false);

	useEffect(() => {
		if (open) {
			setForm(initial(user, defaultDialCode));
			setSubmitted(false);
		}
	}, [open, user, defaultDialCode]);

	const set = <K extends keyof FormState>(k: K, v: FormState[K]) =>
		setForm((f) => ({ ...f, [k]: v }));
	const errors = submitted ? validate(form) : {};

	const mutation = useApiMutation({
		fn: (input: UserInput) => (user ? updateUser(app, user.id, input) : createUser(app, input)),
		invalidate: [userKeys.all(app)],
		success: (r) => r.message,
		onSuccess: () => onOpenChange(false),
	});

	const submit = (e: FormEvent) => {
		e.preventDefault();
		setSubmitted(true);
		if (Object.keys(validate(form)).length) return;
		const phone = form.phone.trim();
		const input: UserInput = {
			name: form.name.trim(),
			email: form.email.trim(),
			mobile: phone ? `${form.dialCode.trim()}${phone}` : '',
			roles: form.roles,
		};
		if (!editing) input.password = form.password;
		if (editing) {
			const before = initial(user, defaultDialCode);
			// The listed auth_config is the effective one; only write it when changed, so an
			// untouched user keeps inheriting from their roles and the app.
			const changed =
				before.twoFaRequired !== form.twoFaRequired ||
				before.twoFaMethods.slice().sort().join() !== form.twoFaMethods.slice().sort().join();
			if (changed)
				input.auth_config = {
					two_factor_auth: { required: form.twoFaRequired, allowed_methods: form.twoFaMethods },
				};
		}
		mutation.mutate(input);
	};

	return (
		<Drawer
			open={open}
			onOpenChange={onOpenChange}
			title={editing ? 'Edit user' : 'Invite user'}
			subtitle={editing ? user?.email || user?.mobile : 'They can sign in once you add them.'}
			footer={
				<>
					<Button onClick={() => onOpenChange(false)}>Cancel</Button>
					<Button variant="primary" type="submit" form="user-form" loading={mutation.isPending}>
						{editing ? 'Save changes' : 'Add user'}
					</Button>
				</>
			}
		>
			<form id="user-form" className="grid gap-4" onSubmit={submit} noValidate>
				<Field label="Name" error={errors.name}>
					{(p) => (
						<Input
							{...p}
							value={form.name}
							onChange={(e) => set('name', e.target.value)}
							autoFocus
						/>
					)}
				</Field>
				<Field label="Email" error={errors.email} hint="An email or a mobile number is required.">
					{(p) => (
						<Input
							{...p}
							type="email"
							value={form.email}
							onChange={(e) => set('email', e.target.value)}
						/>
					)}
				</Field>
				<Field label="Mobile" error={errors.phone ?? errors.dialCode}>
					{(p) => (
						<div className="flex gap-2">
							<Input
								className="!w-[72px] mono"
								aria-label="Country code"
								value={form.dialCode}
								onChange={(e) => set('dialCode', e.target.value)}
							/>
							<Input
								{...p}
								inputMode="numeric"
								value={form.phone}
								onChange={(e) => set('phone', e.target.value.replace(/[^\d]/g, ''))}
							/>
						</div>
					)}
				</Field>
				{!editing && (
					<Field
						label="Password"
						hint="Optional. Needed if users sign in with a password; it must meet the app's password policy."
					>
						{(p) => (
							<Input
								{...p}
								type="password"
								autoComplete="new-password"
								value={form.password}
								onChange={(e) => set('password', e.target.value)}
							/>
						)}
					</Field>
				)}
				<FieldGroup
					label="Roles"
					hint={errors.roles ? <span className="text-red-t">{errors.roles}</span> : undefined}
				>
					{roleOptions.length ? (
						<ChipSelect
							label="Roles"
							options={roleOptions.map((r) => ({ value: r.id, label: r.label }))}
							value={form.roles}
							onChange={(v) => set('roles', v)}
						/>
					) : (
						<span className="text-t3">No roles yet. Create one on the Roles tab first.</span>
					)}
				</FieldGroup>
				{editing && (
					<>
						<div className="divider !my-1" />
						<div className="flex items-start gap-3">
							<div className="flex-1">
								<b className="block font-[550] text-t1">Require two-factor authentication</b>
								<small className="text-[12px] text-t3">
									Overrides the app and role setting for this user.
								</small>
							</div>
							<Switch
								label="Require two-factor authentication"
								checked={form.twoFaRequired}
								onChange={(v) => set('twoFaRequired', v)}
							/>
						</div>
						{form.twoFaRequired && (
							<FieldGroup
								label="Allowed methods"
								hint={
									errors.twoFaMethods ? (
										<span className="text-red-t">{errors.twoFaMethods}</span>
									) : undefined
								}
							>
								<ChipSelect
									label="Allowed 2FA methods"
									options={TWO_FA_METHODS}
									value={form.twoFaMethods}
									onChange={(v) => set('twoFaMethods', v)}
								/>
							</FieldGroup>
						)}
					</>
				)}
			</form>
		</Drawer>
	);
}
