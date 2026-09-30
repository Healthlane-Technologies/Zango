import {
	useAgents,
	useProviders,
	useToggleAgent,
	useToggleProvider,
	useValidateProvider,
	type Agent,
	type Provider,
} from '@/api/ai';
import type { ReactNode } from 'react';
import { Badge, EmptyState, Icon, RowMenu, Table } from '@/ui';

const money = (v: string | number | null | undefined) => {
	const n = Number(v);
	return v == null || Number.isNaN(n) ? '—' : `$${n.toFixed(2)}`;
};

function Section({
	title,
	count,
	children,
}: {
	title: string;
	count?: number;
	children: ReactNode;
}) {
	return (
		<section>
			<h3 className="mb-2 flex items-center gap-2 text-[13.5px]">
				{title}
				{count != null && <span className="text-[12px] font-medium text-t4">{count}</span>}
			</h3>
			{children}
		</section>
	);
}

function ProviderStatus({ p }: { p: Provider }) {
	if (!p.is_enabled)
		return (
			<Badge tone="gray" dot>
				Disabled
			</Badge>
		);
	if (p.validation_error)
		return (
			<Badge tone="red" dot>
				Invalid credentials
			</Badge>
		);
	if (!p.is_validated)
		return (
			<Badge tone="amber" dot>
				Not validated
			</Badge>
		);
	return (
		<Badge tone="green" dot>
			Active
		</Badge>
	);
}

/**
 * LLM providers and agents, with enable/disable and credential checks. Creating and editing
 * providers, prompts, tools, guardrails and invocation logs stay in the classic view for now.
 */
export function AiSettings({ appId }: { appId: string }) {
	const providers = useProviders(appId);
	const agents = useAgents(appId);
	const toggleProvider = useToggleProvider(appId);
	const validate = useValidateProvider(appId);
	const toggleAgent = useToggleAgent(appId);
	const classic = `/platform/apps/${appId}/ai`;

	return (
		<div className="grid gap-4">
			<div className="banner">
				<Icon name="agent" className="text-violet" />
				<span className="text-t2">
					Add providers, and manage prompts, tools, guardrails and invocation logs in the classic
					view.
				</span>
				<a className="btn btn-s btn-sm ml-auto" href={classic}>
					<Icon name="ext" />
					Open classic AI
				</a>
			</div>
			<Section title="Providers" count={providers.data?.length}>
				<Table<Provider>
					loading={providers.isLoading}
					error={providers.error}
					onRetry={() => providers.refetch()}
					rows={providers.data}
					rowKey={(p) => p.id}
					empty={
						<EmptyState title="No providers">
							Connect an LLM provider to use AI agents in this app.
						</EmptyState>
					}
					columns={[
						{
							key: 'n',
							header: 'Provider',
							cell: (p) => (
								<div className="nm">
									<div>
										<b>{p.name}</b>
										<small className="mono">{p.provider_slug}</small>
									</div>
								</div>
							),
						},
						{ key: 's', header: 'Status', cell: (p) => <ProviderStatus p={p} /> },
						{
							key: 'm',
							header: 'Default model',
							cell: (p) => <span className="mono">{p.default_model ?? '—'}</span>,
						},
						{
							key: 'c',
							header: 'Models',
							cell: (p) => <span className="num">{p.models_count}</span>,
						},
						{
							key: 'b',
							header: 'Spend this month',
							cell: (p) => (
								<span className="num">
									{money(p.current_month_spend_usd)}
									{p.monthly_budget_usd != null && (
										<span className="text-t3"> / {money(p.monthly_budget_usd)}</span>
									)}
								</span>
							),
						},
						{
							key: 'a',
							header: '',
							align: 'right',
							cell: (p) => (
								<RowMenu
									label={`Actions for ${p.name}`}
									items={[
										{
											label: 'Validate credentials',
											icon: 'check',
											onSelect: () => validate.mutate({ id: p.id }),
										},
										p.is_enabled
											? {
													label: 'Disable',
													icon: 'x',
													danger: true,
													onSelect: () => toggleProvider.mutate({ id: p.id, is_enabled: false }),
												}
											: {
													label: 'Enable',
													icon: 'check',
													onSelect: () => toggleProvider.mutate({ id: p.id, is_enabled: true }),
												},
									]}
								/>
							),
						},
					]}
				/>
			</Section>
			<Section title="Agents" count={agents.data?.length}>
				<Table<Agent>
					loading={agents.isLoading}
					error={agents.error}
					onRetry={() => agents.refetch()}
					rows={agents.data}
					rowKey={(a) => a.id}
					empty={
						<EmptyState title="No agents">
							Agents are defined in app code or created in the classic view.
						</EmptyState>
					}
					columns={[
						{
							key: 'n',
							header: 'Agent',
							cell: (a) => (
								<div className="nm">
									<div className="min-w-0">
										<b>{a.name}</b>
										{a.description && (
											<small className="max-w-[320px] truncate">{a.description}</small>
										)}
									</div>
								</div>
							),
						},
						{
							key: 's',
							header: 'Status',
							cell: (a) =>
								a.is_enabled ? (
									<Badge tone="green" dot>
										Enabled
									</Badge>
								) : (
									<Badge tone="gray" dot>
										Disabled
									</Badge>
								),
						},
						{
							key: 'm',
							header: 'Model',
							cell: (a) => (
								<span className="mono">
									{[a.provider_name, a.model].filter(Boolean).join(' · ') || '—'}
								</span>
							),
						},
						{
							key: 'i',
							header: 'Invocations',
							cell: (a) => <span className="num">{a.total_invocations}</span>,
						},
						{
							key: 'c',
							header: 'Cost',
							cell: (a) => <span className="num">{money(a.total_cost_usd)}</span>,
						},
						{
							key: 'a',
							header: '',
							align: 'right',
							cell: (a) => (
								<RowMenu
									label={`Actions for ${a.name}`}
									items={[
										a.is_enabled
											? {
													label: 'Disable',
													icon: 'x',
													danger: true,
													onSelect: () => toggleAgent.mutate({ id: a.id, is_enabled: false }),
												}
											: {
													label: 'Enable',
													icon: 'check',
													onSelect: () => toggleAgent.mutate({ id: a.id, is_enabled: true }),
												},
									]}
								/>
							),
						},
					]}
				/>
			</Section>
		</div>
	);
}
