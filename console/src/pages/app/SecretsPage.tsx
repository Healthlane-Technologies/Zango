import { useEffect, useState } from 'react';
import { useAppId } from '@/api/hooks';
import {
	fetchSecretValue,
	SECRET_KEY_RE,
	SECRETS_PAGE_SIZE,
	useCreateSecret,
	useDeleteSecret,
	useSecrets,
	useUpdateSecret,
	type Secret,
} from '@/api/secrets';
import {
	Badge,
	Button,
	Drawer,
	EmptyState,
	Field,
	Icon,
	Input,
	Modal,
	Page,
	PageHeader,
	Pagination,
	RowMenu,
	SearchInput,
	Table,
	toast,
	Toolbar,
	useDebounced,
	type Column,
} from '@/ui';

/** Masked value with on-demand reveal and copy. The decrypted value lives only in this cell. */
function SecretValue({ appId, secret }: { appId: string; secret: Secret }) {
	const [value, setValue] = useState<string | null>(null);
	const [loading, setLoading] = useState(false);

	const reveal = async () => {
		if (value !== null) return setValue(null);
		setLoading(true);
		try {
			setValue(await fetchSecretValue(appId, secret.id));
		} catch (e) {
			toast.error((e as Error).message);
		} finally {
			setLoading(false);
		}
	};

	const copy = async () => {
		try {
			const v = value ?? (await fetchSecretValue(appId, secret.id));
			await navigator.clipboard.writeText(v);
			toast.success(`Copied ${secret.key}`);
		} catch (e) {
			toast.error((e as Error).message);
		}
	};

	return (
		<span className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
			<span className="mono max-w-[260px] truncate text-t1">{value ?? '••••••••••••'}</span>
			<button
				type="button"
				className="ib"
				aria-label={value === null ? `Show ${secret.key}` : `Hide ${secret.key}`}
				onClick={reveal}
			>
				{loading ? <span className="spin" /> : <Icon name={value === null ? 'eye' : 'x'} />}
			</button>
			<button type="button" className="ib" aria-label={`Copy ${secret.key}`} onClick={copy}>
				<Icon name="copy" />
			</button>
		</span>
	);
}

function SecretDrawer({
	appId,
	secret,
	onClose,
}: {
	appId: string;
	secret: Secret | null;
	onClose: () => void;
}) {
	const create = useCreateSecret(appId);
	const update = useUpdateSecret(appId);
	const [key, setKey] = useState(secret?.key ?? '');
	const [value, setValue] = useState('');
	const [touched, setTouched] = useState(false);
	const editing = !!secret;

	const keyError = !touched
		? undefined
		: !key
			? 'Required'
			: !SECRET_KEY_RE.test(key)
				? 'Start with a capital letter; then lowercase letters, digits or _'
				: undefined;
	const valueError = touched && !editing && !value ? 'Required' : undefined;

	const submit = () => {
		setTouched(true);
		if (!key || !SECRET_KEY_RE.test(key) || (!editing && !value)) return;
		if (secret)
			update.mutate({ id: secret.id, key, ...(value ? { value } : {}) }, { onSuccess: onClose });
		else create.mutate({ key, value }, { onSuccess: onClose });
	};

	return (
		<Drawer
			open
			onOpenChange={(o) => !o && onClose()}
			title={editing ? `Edit ${secret.key}` : 'Add secret'}
			subtitle="Values are encrypted at rest and readable by app code."
			footer={
				<>
					<Button onClick={onClose}>Cancel</Button>
					<Button variant="primary" loading={create.isPending || update.isPending} onClick={submit}>
						{editing ? 'Save' : 'Add secret'}
					</Button>
				</>
			}
		>
			<form
				className="grid gap-4"
				onSubmit={(e) => {
					e.preventDefault();
					submit();
				}}
			>
				<Field label="Key" error={keyError} hint="For example Stripe_api_key">
					{(p) => (
						<Input
							{...p}
							className="mono"
							value={key}
							onChange={(e) => setKey(e.target.value)}
							autoFocus={!editing}
							autoComplete="off"
						/>
					)}
				</Field>
				<Field
					label="Value"
					error={valueError}
					hint={editing ? 'Leave blank to keep the current value.' : undefined}
				>
					{(p) => (
						<Input
							{...p}
							type="password"
							className="mono"
							value={value}
							onChange={(e) => setValue(e.target.value)}
							autoFocus={editing}
							autoComplete="new-password"
						/>
					)}
				</Field>
				<button type="submit" hidden />
			</form>
		</Drawer>
	);
}

export function SecretsPage() {
	const appId = useAppId();
	const [page, setPage] = useState(1);
	const [q, setQ] = useState('');
	const search = useDebounced(q.trim());
	const { data, isLoading, isFetching, error, refetch } = useSecrets(appId, page, search);
	const update = useUpdateSecret(appId);
	const remove = useDeleteSecret(appId);
	const [editing, setEditing] = useState<Secret | null | undefined>(undefined);
	const [deleting, setDeleting] = useState<Secret | null>(null);

	useEffect(() => setPage(1), [search]);

	const columns: Column<Secret>[] = [
		{
			key: 'k',
			header: 'Key',
			cell: (s) => <span className="mono font-medium text-t1">{s.key}</span>,
		},
		{ key: 'v', header: 'Value', cell: (s) => <SecretValue appId={appId} secret={s} /> },
		{
			key: 's',
			header: 'Status',
			cell: (s) =>
				s.is_active ? (
					<Badge tone="green" dot>
						Active
					</Badge>
				) : (
					<Badge tone="gray" dot>
						Inactive
					</Badge>
				),
		},
		{ key: 'm', header: 'Updated', cell: (s) => <span className="text-t3">{s.modified_at}</span> },
		{
			key: 'a',
			header: '',
			align: 'right',
			cell: (s) => (
				<RowMenu
					label={`Actions for ${s.key}`}
					items={[
						{ label: 'Edit', icon: 'cog', onSelect: () => setEditing(s) },
						s.is_active
							? {
									label: 'Deactivate',
									icon: 'lock',
									onSelect: () => update.mutate({ id: s.id, is_active: false }),
								}
							: {
									label: 'Activate',
									icon: 'check',
									onSelect: () => update.mutate({ id: s.id, is_active: true }),
								},
						null,
						{
							label: s.is_active ? 'Delete (deactivate first)' : 'Delete',
							icon: 'x',
							danger: true,
							disabled: s.is_active,
							onSelect: () => setDeleting(s),
						},
					]}
				/>
			),
		},
	];

	const total = data?.total_records ?? 0;
	const pages = data?.total_pages ?? 1;

	return (
		<Page>
			<PageHeader
				title="Secrets"
				description="Encrypted values, such as API keys, available to app code."
				actions={
					<Button variant="primary" icon="plus" onClick={() => setEditing(null)}>
						Add secret
					</Button>
				}
			/>
			<Toolbar>
				<SearchInput value={q} onChange={setQ} placeholder="Search secrets" />
				{isFetching && !isLoading && <span className="spin text-t4" />}
			</Toolbar>
			<Table
				columns={columns}
				rows={data?.records}
				rowKey={(s) => s.id}
				loading={isLoading}
				error={error}
				onRetry={() => refetch()}
				empty={
					search ? (
						<EmptyState title="No secrets match">Try another search.</EmptyState>
					) : (
						<EmptyState
							title="No secrets yet"
							action={
								<Button size="sm" onClick={() => setEditing(null)}>
									Add a secret
								</Button>
							}
						>
							Store API keys and credentials here instead of in code.
						</EmptyState>
					)
				}
				footer={
					total > SECRETS_PAGE_SIZE ? (
						<Pagination
							page={page}
							pageSize={SECRETS_PAGE_SIZE}
							totalRecords={total}
							totalPages={pages}
							onPage={setPage}
							noun="secrets"
						/>
					) : undefined
				}
			/>
			{editing !== undefined && (
				<SecretDrawer
					key={editing?.id ?? 'new'}
					appId={appId}
					secret={editing}
					onClose={() => setEditing(undefined)}
				/>
			)}
			<Modal
				open={!!deleting}
				onOpenChange={(o) => !o && setDeleting(null)}
				title={`Delete ${deleting?.key ?? ''}?`}
				subtitle="App code reading this secret will stop working."
				footer={
					<>
						<Button onClick={() => setDeleting(null)}>Cancel</Button>
						<Button
							variant="danger"
							loading={remove.isPending}
							onClick={() =>
								deleting && remove.mutate(deleting, { onSuccess: () => setDeleting(null) })
							}
						>
							Delete secret
						</Button>
					</>
				}
			>
				This can't be undone.
			</Modal>
		</Page>
	);
}
