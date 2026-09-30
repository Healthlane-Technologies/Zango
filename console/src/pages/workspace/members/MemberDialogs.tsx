import { useState, type FormEvent } from 'react';
import {
	memberKeys,
	createMember,
	updateMember,
	PASSWORD_HINT,
	PASSWORD_RULE,
	type Member,
} from '@/api/members';
import { useApiMutation } from '@/api/hooks';
import { Badge, Button, Drawer, Field, Input, Modal } from '@/ui';
import { AppsPicker } from './AppsPicker';

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

type Errors = Partial<Record<'name' | 'email' | 'password' | 'apps', string>>;

/** Add or edit a member. `member` absent means add. */
export function MemberDrawer({
	open,
	onOpenChange,
	member,
	appOptions,
}: {
	open: boolean;
	onOpenChange: (o: boolean) => void;
	member?: Member;
	appOptions: Array<{ id: string; label: string }>;
}) {
	const editing = !!member;
	const [name, setName] = useState(member?.name ?? '');
	const [email, setEmail] = useState(member?.email ?? '');
	const [password, setPassword] = useState('');
	const [apps, setApps] = useState<string[]>(member?.apps.map((a) => a.uuid) ?? []);
	const [errors, setErrors] = useState<Errors>({});

	const save = useApiMutation({
		fn: () =>
			editing
				? updateMember(member.id, { name: name.trim(), email: email.trim(), apps })
				: createMember({ name: name.trim(), email: email.trim(), password, apps }),
		invalidate: [memberKeys.all],
		success: (r) => r.message || (editing ? 'Member updated' : 'Member added'),
		onSuccess: () => onOpenChange(false),
	});

	const validate = (): Errors => {
		const e: Errors = {};
		if (!name.trim()) e.name = 'Enter a name';
		if (!EMAIL.test(email.trim())) e.email = 'Enter a valid email address';
		if (!editing && !PASSWORD_RULE.test(password)) e.password = PASSWORD_HINT;
		// The API ignores an empty list, so an existing member can't be left with none.
		if (!member?.is_superadmin && apps.length === 0) e.apps = 'Pick at least one app';
		return e;
	};

	const submit = (ev: FormEvent) => {
		ev.preventDefault();
		const e = validate();
		setErrors(e);
		if (Object.keys(e).length === 0) save.mutate();
	};

	return (
		<Drawer
			open={open}
			onOpenChange={onOpenChange}
			title={editing ? `Edit ${member.name || member.email}` : 'Add member'}
			subtitle={
				editing ? 'Name, email and app access.' : 'They sign in with this email and password.'
			}
			footer={
				<>
					<Button onClick={() => onOpenChange(false)}>Cancel</Button>
					<Button variant="primary" type="submit" form="member-form" loading={save.isPending}>
						{editing ? 'Save changes' : 'Add member'}
					</Button>
				</>
			}
		>
			<form id="member-form" className="grid gap-4" onSubmit={submit} noValidate>
				<Field label="Name" error={errors.name}>
					{(p) => (
						<Input
							{...p}
							value={name}
							onChange={(e) => setName(e.target.value)}
							autoFocus
							autoComplete="off"
						/>
					)}
				</Field>
				<Field label="Email" error={errors.email}>
					{(p) => (
						<Input
							{...p}
							type="email"
							value={email}
							onChange={(e) => setEmail(e.target.value)}
							autoComplete="off"
						/>
					)}
				</Field>
				{!editing && (
					<Field label="Password" hint={PASSWORD_HINT} error={errors.password}>
						{(p) => (
							<Input
								{...p}
								type="password"
								value={password}
								onChange={(e) => setPassword(e.target.value)}
								autoComplete="new-password"
							/>
						)}
					</Field>
				)}
				<Field
					label="App access"
					hint={
						member?.is_superadmin
							? 'Super admins can open every app regardless.'
							: 'Apps this member can open and manage.'
					}
					error={errors.apps}
				>
					{(p) => (
						<AppsPicker
							options={appOptions}
							value={apps}
							onChange={setApps}
							invalid={!!errors.apps}
							describedBy={p['aria-describedby']}
						/>
					)}
				</Field>
				{member?.is_superadmin && (
					<div className="flex items-center gap-2 text-[12px] text-t3">
						<Badge tone="accent">Super admin</Badge>
						Super admin access is set from the command line, not here.
					</div>
				)}
			</form>
		</Drawer>
	);
}

export function ResetPasswordModal({ member, onClose }: { member: Member; onClose: () => void }) {
	const [password, setPassword] = useState('');
	const [error, setError] = useState<string>();
	const reset = useApiMutation({
		fn: () => updateMember(member.id, { password }),
		invalidate: [memberKeys.all],
		success: 'Password reset',
		onSuccess: onClose,
	});
	const submit = (ev: FormEvent) => {
		ev.preventDefault();
		if (!PASSWORD_RULE.test(password)) return setError(PASSWORD_HINT);
		setError(undefined);
		reset.mutate();
	};
	return (
		<Modal
			open
			onOpenChange={(o) => !o && onClose()}
			title="Reset password"
			subtitle={member.email}
			footer={
				<>
					<Button onClick={onClose}>Cancel</Button>
					<Button variant="primary" type="submit" form="reset-form" loading={reset.isPending}>
						Reset password
					</Button>
				</>
			}
		>
			<form id="reset-form" onSubmit={submit} noValidate>
				<Field label="New password" hint={PASSWORD_HINT} error={error}>
					{(p) => (
						<Input
							{...p}
							type="password"
							value={password}
							onChange={(e) => setPassword(e.target.value)}
							autoFocus
							autoComplete="new-password"
						/>
					)}
				</Field>
			</form>
		</Modal>
	);
}

export function StatusModal({ member, onClose }: { member: Member; onClose: () => void }) {
	const activate = !member.is_active;
	const change = useApiMutation({
		fn: () => updateMember(member.id, { is_active: activate }),
		invalidate: [memberKeys.all],
		success: activate ? 'Member activated' : 'Member deactivated',
		onSuccess: onClose,
	});
	return (
		<Modal
			open
			onOpenChange={(o) => !o && onClose()}
			title={activate ? 'Activate member' : 'Deactivate member'}
			subtitle={member.email}
			footer={
				<>
					<Button onClick={onClose}>Cancel</Button>
					<Button
						variant={activate ? 'primary' : 'danger'}
						loading={change.isPending}
						onClick={() => change.mutate()}
					>
						{activate ? 'Activate' : 'Deactivate'}
					</Button>
				</>
			}
		>
			{activate
				? `${member.name || member.email} will be able to sign in again.`
				: `${member.name || member.email} won't be able to sign in. Their profile and app access are kept, and you can activate them again later.`}
		</Modal>
	);
}
