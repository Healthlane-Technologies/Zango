import { useSearchParams } from 'react-router-dom';
import { Page, PageHeader, Tabs } from '@/ui';
import { AgentModeTab } from './settings/AgentModeTab';
import { GeneralTab } from './settings/GeneralTab';
import { LogConnectorsTab } from './settings/LogConnectorsTab';
import { PlatformLogsTab } from './settings/PlatformLogsTab';

const TABS = [
	{
		value: 'general',
		label: 'General',
		description: 'Domains and defaults applied to every newly created app.',
	},
	{
		value: 'agent',
		label: 'Build with AI',
		description: 'Models, credentials and limits for the requirements and build agents.',
	},
	{
		value: 'connectors',
		label: 'Log connectors',
		description: 'Where platform and app logs are read from.',
	},
	{
		value: 'logs',
		label: 'Platform logs',
		description: 'Runtime logs across every app. Visible to super admins only.',
	},
] as const;

type TabKey = (typeof TABS)[number]['value'];

export function PlatformSettingsPage() {
	const [params, setParams] = useSearchParams();
	const tab = (TABS.find((t) => t.value === params.get('tab'))?.value ?? 'general') as TabKey;
	const active = TABS.find((t) => t.value === tab)!;
	const go = (next: TabKey) =>
		setParams(next === 'general' ? {} : { tab: next }, { replace: true });

	return (
		<Page wide={tab === 'logs'}>
			<PageHeader
				title="Settings"
				description="Platform-wide configuration. Changes apply to every app."
			/>
			<Tabs
				className="-mx-[10px] mb-5 !px-0"
				value={tab}
				onChange={go}
				items={TABS.map((t) => ({ value: t.value, label: t.label }))}
			/>
			<p className="mb-4 text-t3">{active.description}</p>
			{tab === 'general' && <GeneralTab />}
			{tab === 'agent' && <AgentModeTab />}
			{tab === 'connectors' && <LogConnectorsTab />}
			{tab === 'logs' && <PlatformLogsTab onConfigure={() => go('connectors')} />}
		</Page>
	);
}
