import { useState } from 'react';

import { useApiMutation } from '@/api/hooks';

import { policyKeys, updatePolicyRoles, type Policy, type RoleOption } from '@/api/policies';

import {
	Badge,
	Button,
	Checkbox,
	CodeBlock,
	Drawer,
	KeyValues,
	SearchInput,
	SectionTitle,
} from '@/ui';

const ROLE_SEARCH_THRESHOLD = 8;

interface Props {
	appId: string;
	policy: Policy;
	roleOptions: RoleOption[];
	onClose: () => void;
}

export function PolicyDrawer({ appId, policy, roleOptions, onClose }: Props) {
	const initial = policy.roles.map((r) => r.id);
	const [selected, setSelected] = useState<Set<number>>(() => new Set(initial));
	const [q, setQ] = useState('');

	const save = useApiMutation({
		fn: () => updatePolicyRoles(appId, policy, [...selected]),
		invalidate: [policyKeys.all(appId)],
		success: `Roles updated for ${policy.name}`,
		onSuccess: onClose,
	});

	const dirty = selected.size !== initial.length || initial.some((id) => !selected.has(id));
	const needle = q.trim().toLowerCase();
	const visibleRoles = roleOptions.filter((r) => !needle || r.label.toLowerCase().includes(needle));

	const toggle = (id: number) =>
		setSelected((prev) => {
			const next = new Set(prev);
			if (next.has(id)) next.delete(id);
			else next.add(id);
			return next;
		});

	return (
		<Drawer
			open
			onOpenChange={(o) => !o && onClose()}
			title={policy.name}
			subtitle={policy.description ?? undefined}
			footer={
				<>
					<Button onClick={onClose}>Cancel</Button>
					<Button
						variant="primary"
						disabled={!dirty}
						loading={save.isPending}
						onClick={() => save.mutate()}
					>
						Save roles
					</Button>
				</>
			}
		>
			<KeyValues
				items={[
					[
						'Type',
						<Badge tone={policy.type === 'system' ? 'gray' : 'accent'}>
							{policy.type === 'system' ? 'System' : 'App'}
						</Badge>,
					],
					['Module', <span className="mono">{policy.path ?? '—'}</span>],
					['Policy ID', <span className="mono">{policy.id}</span>],
					['Created', policy.created_at],
				]}
			/>

			<SectionTitle
				action={<span className="text-[12px] text-t3 num">{selected.size} selected</span>}
			>
				Roles
			</SectionTitle>
			<p className="mb-2 text-[12px] text-t3">
				Users with any of these roles get this policy's permissions.
			</p>
			{roleOptions.length > ROLE_SEARCH_THRESHOLD && (
				<div className="mb-2">
					<SearchInput value={q} onChange={setQ} placeholder="Search roles" />
				</div>
			)}
			<div className="rounded-lg border border-border px-3 py-1.5">
				{visibleRoles.map((r) => (
					<Checkbox
						key={r.id}
						label={r.label}
						checked={selected.has(r.id)}
						onChange={() => toggle(r.id)}
					/>
				))}
				{!visibleRoles.length && <p className="py-2 text-t3">No roles match.</p>}
			</div>

			<SectionTitle>Statement</SectionTitle>
			<p className="mb-2 text-[12px] text-t3">
				{policy.type === 'system'
					? 'System policies are managed by Zango.'
					: "Edit the statement in the module's policies.json, then sync."}
			</p>
			<CodeBlock>{JSON.stringify(policy.statement, null, 2)}</CodeBlock>
		</Drawer>
	);
}
