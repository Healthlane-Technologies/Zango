import { useState } from 'react';
import {
	inUseAgents,
	money,
	useDeleteProvider,
	useProviders,
	useToggleProvider,
	useValidateProvider,
	type Provider,
} from '@/api/ai';
import {
	Button,
	ConfirmModal,
	EmptyState,
	RowMenu,
	Table,
	Toolbar,
	type Column,
} from '@/ui';
import { InUseModal, ProviderStatus, serviceLabel, StatStrip } from './parts';
import { ProviderDrawer } from './ProviderDrawer';

export function ProvidersTab({ appId }: { appId: string }) {
	const { data, isLoading, error, refetch } = useProviders(appId);
	const toggle = useToggleProvider(appId);
	const validate = useValidateProvider(appId);
	const remove = useDeleteProvider(appId);

	const [drawer, setDrawer] = useState<number | 'new' | null>(null);
	const [confirm, setConfirm] = useState<{ p: Provider; action: 'disable' | 'delete' } | null>(
		null,
	);
	const [blocked, setBlocked] = useState<Array<{ id: number; name: string }> | null>(null);

	const onBlocked = (err: unknown) => setBlocked(inUseAgents(err));
	const editing = typeof drawer === 'number' ? data?.find((p) => p.id === drawer) : undefined;

	const columns: Column<Provider>[] = [
		{
			key: 'n',
			header: 'Provider',
			cell: (p) => (
				<div className="nm">
					<div className="min-w-0">
						<b>{p.name}</b>
						<small>{p.description || serviceLabel(p.provider_slug)}</small>
					</div>
				</div>
			),
		},
		{ key: 's', header: 'Status', cell: (p) => <ProviderStatus p={p} /> },
		{
			key: 'm',
			header: 'Default model',
			cell: (p) => <span className="mono">{p.default_model || '—'}</span>,
		},
		{
			key: 'c',
			header: 'Models',
			cell: (p) => (
				<span className="num">{p.enabled_models.filter((m) => m.is_enabled).length}</span>
			),
		},
		{
			key: 'spend',
			header: 'This month',
			cell: (p) => (
				<span className="num">
					{money(p.current_month_spend_usd)}
					<span className="text-t3">
						{' '}
						/ {p.monthly_budget_usd != null ? money(p.monthly_budget_usd) : 'no limit'}
					</span>
				</span>
			),
		},
		{
			key: 'i',
			header: 'Calls',
			cell: (p) => <span className="num">{p.total_invocations.toLocaleString()}</span>,
		},
		{
			key: 'a',
			header: '',
			align: 'right',
			cell: (p) => (
				<RowMenu
					label={`Actions for ${p.name}`}
					items={[
						{ label: 'Edit', icon: 'pen', onSelect: () => setDrawer(p.id) },
						{
							label: 'Check credentials',
							icon: 'check',
							onSelect: () => validate.mutate({ id: p.id }),
						},
						p.is_enabled
							? {
									label: 'Disable',
									icon: 'x',
									onSelect: () => setConfirm({ p, action: 'disable' }),
								}
							: {
									label: 'Enable',
									icon: 'check',
									onSelect: () => toggle.mutate({ id: p.id, is_enabled: true }),
								},
						null,
						{
							label: 'Delete',
							icon: 'x',
							danger: true,
							onSelect: () => setConfirm({ p, action: 'delete' }),
						},
					]}
				/>
			),
		},
	];

	const active = data?.filter((p) => p.is_enabled).length;
	const spend = data?.reduce((s, p) => s + Number(p.current_month_spend_usd ?? 0), 0);

	return (
		<>
			<StatStrip
				items={[
					['Providers', data?.length],
					['Active', active],
					['Models on', data?.reduce((s, p) => s + p.enabled_models.filter((m) => m.is_enabled).length, 0)],
					['Spend this month', data ? money(spend) : undefined],
				]}
			/>
			<Toolbar>
				<span className="text-[12.5px] text-t3">
					Connections to AI services. Agents pick a provider and one of its models.
				</span>
				<Button variant="primary" icon="plus" className="ml-auto" onClick={() => setDrawer('new')}>
					Add provider
				</Button>
			</Toolbar>
			<Table
				columns={columns}
				rows={data}
				rowKey={(p) => p.id}
				loading={isLoading}
				error={error}
				onRetry={() => refetch()}
				onRowClick={(p) => setDrawer(p.id)}
				empty={
					<EmptyState
						title="No providers yet"
						action={
							<Button variant="primary" icon="plus" onClick={() => setDrawer('new')}>
								Add provider
							</Button>
						}
					>
						Connect an AI service such as Anthropic or OpenAI. Agents need one to run.
					</EmptyState>
				}
			/>

			{drawer === 'new' && <ProviderDrawer appId={appId} onClose={() => setDrawer(null)} />}
			{editing && (
				<ProviderDrawer
					key={editing.id}
					appId={appId}
					provider={editing}
					onClose={() => setDrawer(null)}
				/>
			)}

			<ConfirmModal
				open={confirm != null}
				onOpenChange={(o) => !o && setConfirm(null)}
				title={confirm?.action === 'delete' ? 'Delete provider' : 'Disable provider'}
				confirmLabel={confirm?.action === 'delete' ? 'Delete' : 'Disable'}
				danger
				loading={toggle.isPending || remove.isPending}
				onConfirm={() => {
					if (!confirm) return;
					const done = { onSettled: () => setConfirm(null), onError: onBlocked };
					if (confirm.action === 'delete') remove.mutate({ id: confirm.p.id }, done);
					else toggle.mutate({ id: confirm.p.id, is_enabled: false }, done);
				}}
			>
				{confirm?.action === 'delete' ? (
					confirm.p.total_invocations > 0 ? (
						<p className="text-t2">
							<b>{confirm.p.name}</b> has run history, so it will be disabled and kept for the
							logs rather than removed.
						</p>
					) : (
						<p className="text-t2">
							Delete <b>{confirm?.p.name}</b> and its saved credentials? This can't be undone.
						</p>
					)
				) : (
					<p className="text-t2">
						Agents can't use <b>{confirm?.p.name}</b> while it's disabled.
					</p>
				)}
			</ConfirmModal>

			<InUseModal what="This provider" agents={blocked} onClose={() => setBlocked(null)} />
		</>
	);
}
