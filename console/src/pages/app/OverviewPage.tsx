import { Link } from 'react-router-dom';

import { useAppId } from '@/api/hooks';

import { useAppSettings, type AppDetail } from '@/api/appSettings';

import { useThemes } from '@/api/themes';

import { formatDateTime, timeAgo } from '@/format/time';

import { appPath } from '@/shell/nav';

import {
	AppIcon,
	Avatar,
	Badge,
	ButtonLink,
	Card,
	CardBody,
	CardHeader,
	EmptyState,
	ErrorState,
	Icon,
	KeyValues,
	Page,
	Skeleton,
	type Tone,
} from '@/ui';

import { StatusBadge } from '../AppsPage';

import { StatTile, Swatch } from './settings/parts';
import {
	useOverviewCounts,
	useRecentAudit,
	useRecentReleases,
	type ReleaseSummary,
} from './overview/queries';

const RELEASE_TONE: Record<string, Tone> = { released: 'green', failed: 'red', initiated: 'amber' };

function loginMethods(app: AppDetail): string {
	const m = app.auth_config?.login_methods ?? {};
	const on = [
		m.password?.enabled && 'Password',
		m.otp?.enabled && 'OTP',
		m.sso?.enabled && 'SSO',
		m.oidc?.enabled && 'OIDC',
	].filter(Boolean);
	return on.length ? on.join(', ') : 'None';
}

function ReleaseCard({
	appId,
	releases,
	loading,
}: {
	appId: string;
	releases?: ReleaseSummary[];
	loading: boolean;
}) {
	const latest = releases?.[0];
	return (
		<Card>
			<CardHeader
				title="Latest release"
				actions={
					<Link to={appPath(appId, 'deployments')} className="link text-[12.5px]">
						All deployments
					</Link>
				}
			/>
			<CardBody>
				{loading ? (
					<div className="grid gap-2">
						<Skeleton width="40%" />
						<Skeleton width="70%" />
					</div>
				) : latest ? (
					<KeyValues
						items={[
							['Version', <span className="mono">{latest.version}</span>],
							[
								'Status',
								<Badge tone={RELEASE_TONE[latest.status] ?? 'gray'} dot>
									{latest.status.charAt(0).toUpperCase() + latest.status.slice(1)}
								</Badge>,
							],
							['Released', latest.created_at],
							[
								'Commit',
								latest.last_git_hash ? (
									<span className="mono">{latest.last_git_hash.slice(0, 10)}</span>
								) : null,
							],
							[
								'Notes',
								latest.description && latest.description !== 'NA' ? latest.description : null,
							],
						]}
					/>
				) : (
					<EmptyState title="No releases yet">
						Releases appear here once the app is released from its repository.
					</EmptyState>
				)}
			</CardBody>
		</Card>
	);
}

function Activity({ appId }: { appId: string }) {
	const { data, isLoading, error } = useRecentAudit(appId);
	return (
		<Card>
			<CardHeader
				title="Recent activity"
				actions={
					<Link to={appPath(appId, 'logs')} className="link text-[12.5px]">
						View logs
					</Link>
				}
			/>
			{isLoading ? (
				<CardBody className="grid gap-3">
					{[0, 1, 2].map((i) => (
						<Skeleton key={i} width={`${60 + i * 10}%`} />
					))}
				</CardBody>
			) : error ? (
				<ErrorState error={error} />
			) : !data?.length ? (
				<EmptyState title="No activity yet" />
			) : (
				<ul>
					{data.map((e) => (
						<li
							key={e.id}
							className="flex items-center gap-2.5 border-b border-border-soft px-4 py-2.5 last:border-0"
						>
							{e.actor ? (
								<Avatar name={e.actor} small />
							) : (
								<span className="av sm bg-subtle text-t3">·</span>
							)}
							<span className="min-w-0 flex-1 truncate">
								<b className="font-[550] text-t1">{e.actor ?? 'System'}</b>{' '}
								<span className="text-t2">
									{e.action.toLowerCase()}d {e.object_type}
									{e.object_id != null && <span className="mono text-t3"> #{e.object_id}</span>}
								</span>
							</span>
							<span className="shrink-0 text-[12px] text-t3">{e.timestamp}</span>
						</li>
					))}
				</ul>
			)}
		</Card>
	);
}

export function OverviewPage() {
	const appId = useAppId();
	const { data, isLoading, error, refetch } = useAppSettings(appId);
	const releases = useRecentReleases(appId);
	const { users, roles } = useOverviewCounts(appId);
	const themes = useThemes(appId);
	const app = data?.app;
	const activeTheme = themes.data?.find((t) => t.is_active);

	if (error) {
		return (
			<Page>
				<div className="card">
					<ErrorState error={error} onRetry={() => refetch()} />
				</div>
			</Page>
		);
	}

	return (
		<Page>
			<div className="ph items-center">
				{app ? (
					<AppIcon name={app.name} size={40} />
				) : (
					<span className="appic bg-subtle" style={{ width: 40, height: 40 }} />
				)}
				<div className="min-w-0">
					<div className="flex items-center gap-2.5">
						<h1 className="truncate">{app?.name ?? <Skeleton width={180} height={20} />}</h1>
						{app && <StatusBadge status={app.status} />}
					</div>
					<p className="truncate">
						{app ? app.description || 'No description' : <Skeleton width={260} />}
					</p>
				</div>
				<div className="r">
					<ButtonLink to={appPath(appId, 'agent')} icon="agent">
						Change with agent
					</ButtonLink>
					{app?.domain_url && (
						<a
							className="btn btn-p"
							href={`//${app.domain_url}`}
							target="_blank"
							rel="noopener noreferrer"
						>
							<Icon name="ext" />
							Visit
						</a>
					)}
				</div>
			</div>

			<div className="mb-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
				<StatTile
					label="Users"
					value={users.data ?? '—'}
					loading={users.isLoading}
					sub={
						<Link className="link" to={appPath(appId, 'users')}>
							Manage
						</Link>
					}
				/>
				<StatTile label="Roles" value={roles.data ?? '—'} loading={roles.isLoading} />
				<StatTile
					label="Last release"
					value={<span className="mono text-[18px]">{app?.last_released_version ?? '—'}</span>}
					loading={isLoading}
				/>
				<StatTile
					label="Theme"
					loading={themes.isLoading}
					value={
						activeTheme ? (
							<span className="flex items-center gap-2 text-[15px]">
								<Swatch color={activeTheme.config?.color?.primary} />
								<span className="truncate">{activeTheme.name}</span>
							</span>
						) : (
							'—'
						)
					}
					sub={
						<Link className="link" to={`${appPath(appId, 'settings')}?tab=theme`}>
							Change
						</Link>
					}
				/>
			</div>

			<div className="grid gap-4 lg:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)]">
				<div className="grid content-start gap-4">
					<ReleaseCard
						appId={appId}
						releases={releases.data?.records}
						loading={releases.isLoading}
					/>
					<Activity appId={appId} />
				</div>
				<div className="grid content-start gap-4">
					<Card>
						<CardHeader
							title="Details"
							actions={
								<Link to={appPath(appId, 'settings')} className="link text-[12.5px]">
									Edit
								</Link>
							}
						/>
						<CardBody>
							{app ? (
								<KeyValues
									items={[
										['Tenant', <span className="mono">{app.schema_name}</span>],
										['Timezone', app.timezone],
										['Date format', app.date_format_display],
										['Date & time', app.datetime_format_display],
										['Sign-in', loginMethods(app)],
										[
											'Created',
											<span title={formatDateTime(app.created_at)}>{timeAgo(app.created_at)}</span>,
										],
										[
											'Deployed',
											app.deployed_on ? (
												<span title={formatDateTime(app.deployed_on)}>
													{timeAgo(app.deployed_on)}
												</span>
											) : null,
										],
									]}
								/>
							) : (
								<div className="grid gap-3">
									{[0, 1, 2, 3].map((i) => (
										<Skeleton key={i} />
									))}
								</div>
							)}
						</CardBody>
					</Card>
					<Card>
						<CardHeader title="Domains" count={app?.domains.length} />
						{app && app.domains.length === 0 && <EmptyState title="No domains" />}
						<ul>
							{app?.domains.map((d) => (
								<li
									key={d.domain}
									className="flex items-center gap-2 border-b border-border-soft px-4 py-2.5 last:border-0"
								>
									<a
										className="mono truncate text-t1 hover:underline"
										href={`//${d.domain}`}
										target="_blank"
										rel="noopener noreferrer"
									>
										{d.domain}
									</a>
									{d.is_primary && (
										<Badge tone="accent" className="ml-auto">
											Primary
										</Badge>
									)}
								</li>
							))}
						</ul>
					</Card>
				</div>
			</div>
		</Page>
	);
}
