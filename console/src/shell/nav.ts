import { useMatch } from 'react-router-dom';
import type { IconName } from '@/ui';

export interface NavItem {
	/** Path relative to its scope: the console root, or the app root. */
	to: string;
	label: string;
	icon: IconName;
}

export interface NavGroup {
	title?: string;
	items: NavItem[];
}

export const DOCS_URL = 'https://zango.dev/docs';

export const workspaceNav: NavGroup[] = [
	{
		items: [
			{ to: 'apps', label: 'Apps', icon: 'apps' },
			{ to: 'templates', label: 'Templates', icon: 'tpl' },
			{ to: 'packages', label: 'Package catalog', icon: 'pkg' },
		],
	},
	{
		title: 'Workspace',
		items: [
			{ to: 'members', label: 'Members', icon: 'users' },
			{ to: 'settings', label: 'Settings', icon: 'cog' },
		],
	},
];

// Scope: screens backed by existing APIs only. Policies and Secrets sit under Govern and
// Tasks under Operate; Theme, Code and AI are Settings sub-tabs.
export const appNav: NavGroup[] = [
	{
		items: [
			{ to: '', label: 'Overview', icon: 'home' },
			{ to: 'agent', label: 'Agent', icon: 'agent' },
		],
	},
	{
		title: 'Build',
		items: [
			{ to: 'deployments', label: 'Deployments', icon: 'rocket' },
			{ to: 'packages', label: 'Packages', icon: 'pkg' },
		],
	},
	{
		title: 'Operate',
		items: [
			{ to: 'logs', label: 'Logs', icon: 'logs' },
			{ to: 'tasks', label: 'Tasks', icon: 'zap' },
		],
	},
	{
		title: 'Govern',
		items: [
			{ to: 'users', label: 'Users & roles', icon: 'users' },
			{ to: 'policies', label: 'Policies', icon: 'shield' },
			{ to: 'auth', label: 'Authentication', icon: 'key' },
			{ to: 'secrets', label: 'Secrets', icon: 'lock' },
		],
	},
	{ items: [{ to: 'settings', label: 'Settings', icon: 'cog' }] },
];

export const appPath = (uuid: string, to = '') => `/apps/${uuid}${to ? `/${to}` : ''}`;

/** Routes under /apps/ that aren't an app. */
const RESERVED_APP_SEGMENTS = new Set(['new']);

/** The uuid of the app the URL is inside, or undefined on workspace pages (including /apps/new). */
export function useCurrentAppId(): string | undefined {
	const id = useMatch('/apps/:appId/*')?.params.appId;
	return id && !RESERVED_APP_SEGMENTS.has(id) ? id : undefined;
}
