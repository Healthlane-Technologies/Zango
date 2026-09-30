import { NavLink } from 'react-router-dom';
import { useApp, useApps } from '@/api/apps';
import { useMe } from '@/api/me';
import { AppIcon, Avatar, Icon, Menu, Skeleton, cx } from '@/ui';
import { appNav, appPath, DOCS_URL, useCurrentAppId, workspaceNav, type NavGroup } from './nav';

function Logo() {
	return (
		<div className="brandrow">
			<svg viewBox="0 0 40 40" aria-hidden>
				<rect width="40" height="40" rx="9" fill="#4F46E5" />
				<path
					d="M8 8 L32 8 L8 32 L32 32"
					stroke="#fff"
					strokeWidth="5"
					strokeLinecap="round"
					strokeLinejoin="round"
					fill="none"
				/>
			</svg>
			<b>Zango</b>
		</div>
	);
}

function NavGroups({
	groups,
	base,
	counts,
}: {
	groups: NavGroup[];
	base: string;
	counts?: Record<string, number | undefined>;
}) {
	return (
		<nav className="side-nav">
			{groups.map((g, gi) => (
				<div key={gi}>
					{g.title ? <div className="ng">{g.title}</div> : <div style={{ height: gi ? 10 : 6 }} />}
					{g.items.map((it) => (
						<NavLink
							key={it.to}
							to={it.to ? `${base}/${it.to}` : base}
							end={!it.to}
							className={({ isActive }) => cx('ni', isActive && 'on')}
						>
							<Icon name={it.icon} />
							{it.label}
							{counts?.[it.to] != null && <span className="ct">{counts[it.to]}</span>}
						</NavLink>
					))}
				</div>
			))}
		</nav>
	);
}

function UserMenu() {
	const { data: me } = useMe();
	return (
		<Menu
			align="start"
			items={[
				{
					label: 'Classic view',
					icon: 'ext',
					onSelect: () => window.location.assign('/platform/apps/'),
				},
				{
					label: 'Documentation',
					icon: 'book',
					onSelect: () => window.open(DOCS_URL, '_blank', 'noopener'),
				},
				null,
				{
					label: 'Sign out',
					icon: 'back',
					onSelect: () => window.location.assign('/auth/logout/'),
				},
			]}
			trigger={
				<button type="button" className="me">
					{me ? <Avatar name={me.name || me.email} /> : <span className="av bg-subtle" />}
					<span className="min-w-0">
						<b className="truncate">{me?.name || me?.email || <Skeleton width={90} />}</b>
						<small>{me ? (me.is_superadmin ? 'Super admin' : 'Platform user') : ' '}</small>
					</span>
				</button>
			}
		/>
	);
}

function Footer() {
	return (
		<div className="side-bot">
			<UserMenu />
		</div>
	);
}

function AppSidebar({ uuid }: { uuid: string }) {
	const { data: app } = useApp(uuid);
	return (
		<>
			<div className="side-top">
				<Logo />
				<NavLink to="/apps" className="back">
					<Icon name="back" />
					All apps
				</NavLink>
				<div className="appsel">
					{app ? <AppIcon name={app.name} /> : <span className="appic bg-subtle" />}
					<div className="min-w-0">
						<b>{app?.name ?? <Skeleton width={110} />}</b>
						<small className="mono">{app?.domain_url ?? app?.schema_name ?? ' '}</small>
					</div>
				</div>
			</div>
			<NavGroups groups={appNav} base={appPath(uuid)} />
			<Footer />
		</>
	);
}

function WorkspaceSidebar() {
	const { data: apps } = useApps();
	return (
		<>
			<div className="side-top">
				<Logo />
			</div>
			<NavGroups groups={workspaceNav} base="" counts={{ apps: apps?.length }} />
			<Footer />
		</>
	);
}

export function Sidebar() {
	const appId = useCurrentAppId();
	return (
		<aside className="side">{appId ? <AppSidebar uuid={appId} /> : <WorkspaceSidebar />}</aside>
	);
}
