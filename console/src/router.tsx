import type { ComponentType } from 'react';
import { createBrowserRouter, Navigate, Outlet, type RouteObject } from 'react-router-dom';
import { Shell } from './shell/Shell';
import { AppCrumb, type CrumbHandle } from './shell/crumbs';
import { AppsPage } from './pages/AppsPage';
import { Placeholder } from './pages/Placeholder';

const crumb = (label: string): CrumbHandle => ({ crumb: () => label });

/**
 * Load a page's module when its route is first visited, so each screen ships in its own
 * chunk. `name` is the page component's export name.
 */
function page<M extends Record<string, unknown>>(
	load: () => Promise<M>,
	name: keyof M & string,
): Pick<RouteObject, 'lazy'> {
	return { lazy: async () => ({ Component: (await load())[name] as ComponentType }) };
}

// Each page owns its sub-tabs (e.g. Users & roles, Settings) via a `?tab=` search param,
// so routes stay one per sidebar item.
const appPages: Array<{ path: string; title: string } & Pick<RouteObject, 'lazy'>> = [
	{ path: 'agent', title: 'Agent', ...page(() => import('./pages/app/AgentPage'), 'AgentPage') },
	{
		path: 'deployments',
		title: 'Deployments',
		...page(() => import('./pages/app/DeploymentsPage'), 'DeploymentsPage'),
	},
	{
		path: 'packages',
		title: 'Packages',
		...page(() => import('./pages/app/PackagesPage'), 'PackagesPage'),
	},
	{ path: 'logs', title: 'Logs', ...page(() => import('./pages/app/LogsPage'), 'LogsPage') },
	{ path: 'tasks', title: 'Tasks', ...page(() => import('./pages/app/TasksPage'), 'TasksPage') },
	{
		path: 'users',
		title: 'Users & roles',
		...page(() => import('./pages/app/UsersPage'), 'UsersPage'),
	},
	{
		path: 'policies',
		title: 'Policies',
		...page(() => import('./pages/app/PoliciesPage'), 'PoliciesPage'),
	},
	{
		path: 'auth',
		title: 'Authentication',
		...page(() => import('./pages/app/AuthPage'), 'AuthPage'),
	},
	{
		path: 'secrets',
		title: 'Secrets',
		...page(() => import('./pages/app/SecretsPage'), 'SecretsPage'),
	},
	{
		path: 'settings',
		title: 'Settings',
		...page(() => import('./pages/app/SettingsPage'), 'SettingsPage'),
	},
];

export const router = createBrowserRouter(
	[
		{
			element: <Shell />,
			children: [
				{ index: true, element: <Navigate to="apps" replace /> },
				{
					path: 'apps',
					handle: crumb('Apps'),
					children: [
						{ index: true, element: <AppsPage /> },
						{
							path: 'new',
							handle: crumb('New app'),
							...page(() => import('./pages/new/NewAppPage'), 'NewAppPage'),
						},
						{
							path: ':appId',
							element: <Outlet />,
							handle: { crumb: (m) => <AppCrumb uuid={m.params.appId!} /> } satisfies CrumbHandle,
							children: [
								{
									index: true,
									handle: crumb('Overview'),
									...page(() => import('./pages/app/OverviewPage'), 'OverviewPage'),
								},
								...appPages.map(({ path, title, lazy }) => ({ path, handle: crumb(title), lazy })),
								{ path: '*', element: <Navigate to="." replace /> },
							],
						},
					],
				},
				{
					path: 'templates',
					handle: crumb('Templates'),
					element: (
						<Placeholder
							title="Templates"
							description="Start a new app from a proven program."
							classicHref="/platform/build-with-agent"
						/>
					),
				},
				{
					path: 'packages',
					handle: crumb('Package catalog'),
					...page(() => import('./pages/workspace/PackageCatalogPage'), 'PackageCatalogPage'),
				},
				{
					path: 'members',
					handle: crumb('Members'),
					...page(() => import('./pages/workspace/MembersPage'), 'MembersPage'),
				},
				{
					path: 'settings',
					handle: crumb('Settings'),
					...page(() => import('./pages/workspace/PlatformSettingsPage'), 'PlatformSettingsPage'),
				},
				{
					path: '_ui',
					handle: crumb('UI kit'),
					...page(() => import('./pages/UiKitPage'), 'UiKitPage'),
				},
				{ path: '*', element: <Navigate to="apps" replace /> },
			],
		},
	],
	{ basename: '/console' },
);
