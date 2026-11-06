import { Navigate, useSearchParams } from 'react-router-dom';
import { useAppId } from '@/api/hooks';
import { Page, PageHeader, Tabs } from '@/ui';
import { GeneralSettings } from './settings/GeneralSettings';
import { ThemeSettings } from './settings/ThemeSettings';
import { CodeSettings } from './settings/CodeSettings';

const TABS = [
	{ value: 'general', label: 'General' },
	{ value: 'theme', label: 'Theme' },
	{ value: 'code', label: 'Code' },
] as const;

type Tab = (typeof TABS)[number]['value'];

export function SettingsPage() {
	const appId = useAppId();
	const [params, setParams] = useSearchParams();
	const raw = params.get('tab');
	// AI moved to its own page; keep old links working.
	if (raw === 'ai') return <Navigate to="../ai" replace />;
	const tab: Tab = TABS.some((t) => t.value === raw) ? (raw as Tab) : 'general';

	return (
		<Page>
			<PageHeader
				title="Settings"
				description="General details, branding, theme and code for this app."
			/>
			<Tabs
				className="-mx-0 mb-6 px-0"
				items={[...TABS]}
				value={tab}
				onChange={(t) => setParams(t === 'general' ? {} : { tab: t }, { replace: true })}
			/>
			{tab === 'general' && <GeneralSettings appId={appId} />}
			{tab === 'theme' && <ThemeSettings appId={appId} />}
			{tab === 'code' && <CodeSettings appId={appId} />}
		</Page>
	);
}
