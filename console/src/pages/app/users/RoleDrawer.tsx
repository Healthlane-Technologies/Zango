import { useEffect, useMemo, useState, type FormEvent } from 'react';

import { useApiMutation } from '@/api/hooks';

import {
	createRole,
	RESERVED_ROLES,
	roleKeys,
	stripPlatformHints,
	updateRole,
	type PolicyOption,
	type Role,
	type RoleInput,
} from '@/api/roles';

import { Badge, Button, cx, Drawer, Field, FieldGroup, Input, SearchInput, Switch } from '@/ui';

import { ChipSelect } from '../auth/controls';

const TWO_FA_METHODS = [
	{ value: 'email', label: 'Email' },
	{ value: 'sms', label: 'SMS' },
	{ value: 'totp', label: 'Authenticator app' },
];
const DEFAULT_REDIRECT = '/frame/router';

interface Props {
	app: string;
	open: boolean;
	onOpenChange: (o: boolean) => void;
	/** Omit to create a role. */
	role?: Role | null;
	policies: PolicyOption[];
}

interface FormState {
	name: string;
	redirectUrl: string;
	policies: number[];
	twoFaRequired: boolean;
	twoFaMethods: string[];
}

function initial(role: Role | null | undefined): FormState {
	const tfa = role?.auth_config?.two_factor_auth;
	return {
		name: role?.name ?? '',
		redirectUrl: role?.auth_config?.redirect_url ?? DEFAULT_REDIRECT,
		policies: role?.policies ?? [],
		twoFaRequired: tfa?.required ?? false,
		twoFaMethods: tfa?.allowed_methods ?? [],
	};
}

function PolicyPicker({
	policies,
	value,
	onChange,
}: {
	policies: PolicyOption[];
	value: number[];
	onChange: (v: number[]) => void;
}) {
	const [q, setQ] = useState('');
	const list = useMemo(() => {
		const needle = q.trim().toLowerCase();
		return policies.filter(
			(p) => !needle || `${p.label} ${p.path ?? ''}`.toLowerCase().includes(needle),
		);
	}, [policies, q]);
	const toggle = (id: number) =>
		onChange(value.includes(id) ? value.filter((v) => v !== id) : [...value, id]);
	return (
		<div className="grid gap-2">
			<SearchInput value={q} onChange={setQ} placeholder="Search policies" />
			<div className="max-h-[280px] overflow-y-auto rounded-[7px] border border-border">
				{list.length === 0 && (
					<div className="px-3 py-4 text-center text-t3">No policies match</div>
				)}
				{list.map((p) => {
					const on = value.includes(p.id);
					return (
						<label
							key={p.id}
							className={cx(
								'flex h-9 cursor-pointer items-center gap-2.5 border-b border-border-soft px-3 last:border-0 hover:bg-hover',
								on && 'bg-accent-soft',
							)}
						>
							<input
								type="checkbox"
								className="accent-[var(--accent)]"
								checked={on}
								onChange={() => toggle(p.id)}
							/>
							<span className="min-w-0 flex-1 truncate text-t1">{p.label}</span>
							{p.path && <span className="mono truncate text-t4">{p.path}</span>}
							<Badge tone={p.type === 'system' ? 'gray' : 'line'}>{p.type}</Badge>
						</label>
					);
				})}
			</div>
		</div>
	);
}

export function RoleDrawer({ app, open, onOpenChange, role, policies }: Props) {
	const editing = !!role;
	const reserved = !!role && RESERVED_ROLES.includes(role.name);
	const [form, setForm] = useState(() => initial(role));
	const [submitted, setSubmitted] = useState(false);

	useEffect(() => {
		if (open) {
			setForm(initial(role));
			setSubmitted(false);
		}
	}, [open, role]);

	const set = <K extends keyof FormState>(k: K, v: FormState[K]) =>
		setForm((f) => ({ ...f, [k]: v }));
	const errors: Partial<Record<keyof FormState, string>> = {};
	if (submitted) {
		if (!form.name.trim()) errors.name = 'Enter a role name';
		if (!reserved && !form.redirectUrl.trim())
			errors.redirectUrl = 'Enter the page users land on after sign-in';
		if (form.twoFaRequired && form.twoFaMethods.length === 0)
			errors.twoFaMethods = 'Pick at least one method';
	}

	const mutation = useApiMutation({
		fn: (input: RoleInput) => (role ? updateRole(app, role.id, input) : createRole(app, input)),
		invalidate: [roleKeys.all(app)],
		success: (r) => r.message,
		onSuccess: () => onOpenChange(false),
	});

	const submit = (e: FormEvent) => {
		e.preventDefault();
		setSubmitted(true);
		if (
			!form.name.trim() ||
			(!reserved && !form.redirectUrl.trim()) ||
			(form.twoFaRequired && form.twoFaMethods.length === 0)
		)
			return;
		// auth_config is replaced on save: start from the stored one so other keys (enforce_sso,
		// password_policy, session_policy.token_ttl) survive.
		const auth = stripPlatformHints(role?.auth_config ?? {});
		if (!reserved) auth.redirect_url = form.redirectUrl.trim();
		if (form.twoFaRequired || auth.two_factor_auth) {
			auth.two_factor_auth = {
				...auth.two_factor_auth,
				required: form.twoFaRequired,
				allowed_methods: form.twoFaMethods,
			};
		}
		const input: RoleInput = { policies: form.policies, auth_config: auth };
		if (!reserved) input.name = form.name.trim();
		mutation.mutate(input);
	};

	return (
		<Drawer
			open={open}
			onOpenChange={onOpenChange}
			title={editing ? `Edit ${role?.name}` : 'New role'}
			subtitle={
				reserved
					? 'Built-in role. Its name and landing page are fixed.'
					: 'Roles group permissions for sets of users.'
			}
			footer={
				<>
					<Button onClick={() => onOpenChange(false)}>Cancel</Button>
					<Button variant="primary" type="submit" form="role-form" loading={mutation.isPending}>
						{editing ? 'Save changes' : 'Create role'}
					</Button>
				</>
			}
		>
			<form id="role-form" className="grid gap-4" onSubmit={submit} noValidate>
				<Field label="Name" error={errors.name}>
					{(p) => (
						<Input
							{...p}
							value={form.name}
							disabled={reserved}
							onChange={(e) => set('name', e.target.value)}
							autoFocus={!editing}
						/>
					)}
				</Field>
				{!reserved && (
					<Field
						label="Landing page"
						error={errors.redirectUrl}
						hint="Where users with this role go after signing in."
					>
						{(p) => (
							<Input
								{...p}
								className="mono"
								value={form.redirectUrl}
								onChange={(e) => set('redirectUrl', e.target.value)}
							/>
						)}
					</Field>
				)}
				<FieldGroup label={`Policies · ${form.policies.length} selected`}>
					<PolicyPicker
						policies={policies}
						value={form.policies}
						onChange={(v) => set('policies', v)}
					/>
				</FieldGroup>
				<div className="divider !my-1" />
				<div className="flex items-start gap-3">
					<div className="flex-1">
						<b className="block font-[550] text-t1">Require two-factor authentication</b>
						<small className="text-[12px] text-t3">Applies to every user with this role.</small>
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
			</form>
		</Drawer>
	);
}
