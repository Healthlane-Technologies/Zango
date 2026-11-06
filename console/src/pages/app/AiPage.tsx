import { useSearchParams } from 'react-router-dom';
import { useAppId } from '@/api/hooks';
import { Page, PageHeader, Tabs } from '@/ui';
import { AgentsTab } from './ai/AgentsTab';
import { PromptsTab } from './ai/PromptsTab';
import { ProvidersTab } from './ai/ProvidersTab';
import { RunsTab } from './ai/RunsTab';
import { ToolsTab } from './ai/ToolsTab';

const TABS = [
	{ value: 'agents', label: 'Agents' },
	{ value: 'providers', label: 'Providers' },
	{ value: 'prompts', label: 'Prompts' },
	{ value: 'tools', label: 'Tools' },
	{ value: 'runs', label: 'Runs' },
] as const;

type Tab = (typeof TABS)[number]['value'];

/** The app's AI module: providers, agents, prompts, tools and invocation logs. */
export function AiPage() {
	const appId = useAppId();
	const [params, setParams] = useSearchParams();
	const raw = params.get('tab');
	const tab: Tab = TABS.some((t) => t.value === raw) ? (raw as Tab) : 'agents';

	return (
		<Page wide={tab === 'runs'}>
			<PageHeader
				title="AI"
				description="LLM providers, the agents app code runs with get_agent(), their versioned prompts and tools, and a log of every run."
			/>
			<Tabs
				className="mb-6"
				items={[...TABS]}
				value={tab}
				onChange={(t) => setParams(t === 'agents' ? {} : { tab: t }, { replace: true })}
			/>
			{tab === 'agents' && <AgentsTab appId={appId} />}
			{tab === 'providers' && <ProvidersTab appId={appId} />}
			{tab === 'prompts' && <PromptsTab appId={appId} />}
			{tab === 'tools' && <ToolsTab appId={appId} />}
			{tab === 'runs' && <RunsTab appId={appId} />}
		</Page>
	);
}
