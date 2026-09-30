import { useMemo, useState } from 'react';
import { useApp } from '@/api/apps';
import { useAppId } from '@/api/hooks';
import { updateAvailable, usePackages, type Package } from '@/api/packages';
import {
	Badge,
	Button,
	EmptyState,
	Icon,
	Page,
	PageHeader,
	SearchInput,
	Segmented,
	Table,
	Toolbar,
	type Column,
} from '@/ui';
import { InstallPackageModal } from './packages/InstallPackageModal';

type Filter = 'installed' | 'available' | 'all';

function openConfig(p: Package) {
	if (p.config_url) window.open(p.config_url, '_blank', 'noopener');
}

export function PackageStatus({ pkg }: { pkg: Package }) {
	if (pkg.status !== 'Installed') return <Badge tone="gray">Not installed</Badge>;
	const update = updateAvailable(pkg);
	return update ? (
		<Badge tone="amber" dot>
			Update available · {update}
		</Badge>
	) : (
		<Badge tone="green" dot>
			Current
		</Badge>
	);
}

export function PackagesPage() {
	const appId = useAppId();
	const { data: app } = useApp(appId);
	const { data: packages, isLoading, error, refetch } = usePackages(appId);
	// The backend reads the app's manifest from disk; without a checkout it 500s with ENOENT.
	const noWorkspace = !!error && /No such file or directory/.test(error.message);
	const [q, setQ] = useState('');
	const [filter, setFilter] = useState<Filter>('installed');
	const [installing, setInstalling] = useState<string | null>(null);

	const available = useMemo(
		() => (packages ?? []).filter((p) => p.status !== 'Installed' && p.versions?.length),
		[packages],
	);
	const installedCount = packages?.filter((p) => p.status === 'Installed').length ?? 0;

	const rows = useMemo(() => {
		const needle = q.trim().toLowerCase();
		return (packages ?? [])
			.filter((p) => filter === 'all' || (filter === 'installed') === (p.status === 'Installed'))
			.filter((p) => !needle || p.name.toLowerCase().includes(needle))
			.sort((a, b) => a.name.localeCompare(b.name));
	}, [packages, q, filter]);

	const columns: Column<Package>[] = [
		{
			key: 'name',
			header: 'Package',
			cell: (p) => <span className="mono font-medium text-t1">{p.name}</span>,
		},
		{
			key: 'version',
			header: 'Version',
			cell: (p) => <span className="mono">{p.installed_version ?? '—'}</span>,
		},
		{
			key: 'latest',
			header: 'Latest',
			cell: (p) => <span className="mono text-t3">{p.versions?.[0] ?? '—'}</span>,
		},
		{ key: 'status', header: 'Status', cell: (p) => <PackageStatus pkg={p} /> },
		{
			key: 'action',
			header: '',
			align: 'right',
			className: 'w-[120px]',
			cell: (p) =>
				p.status === 'Installed'
					? p.config_url && (
							<button
								type="button"
								className="link inline-flex items-center gap-1"
								onClick={() => openConfig(p)}
							>
								Configure
								<Icon name="ext" size={13} />
							</button>
						)
					: !!p.versions?.length && (
							<Button size="xs" onClick={() => setInstalling(p.name)}>
								Install
							</Button>
						),
		},
	];

	return (
		<Page>
			<PageHeader
				title="Packages"
				description="Installed Zango packages. Custom logic lives in app code, so these stay upgradeable."
				actions={
					<Button
						variant="primary"
						icon="plus"
						disabled={!available.length}
						onClick={() => setInstalling(available[0]?.name ?? null)}
					>
						Install package
					</Button>
				}
			/>
			<Toolbar>
				<SearchInput value={q} onChange={setQ} placeholder="Search packages" />
				<Segmented
					label="Filter packages"
					value={filter}
					onChange={setFilter}
					options={[
						{ value: 'installed', label: `Installed${packages ? ` · ${installedCount}` : ''}` },
						{ value: 'available', label: 'Available' },
						{ value: 'all', label: 'All' },
					]}
				/>
			</Toolbar>
			{noWorkspace ? (
				<div className="card">
					<EmptyState title="No workspace on this server">
						This app's code isn't checked out here, so its installed packages can't be read.
					</EmptyState>
				</div>
			) : (
				<Table
					columns={columns}
					rows={rows}
					rowKey={(p) => p.name}
					loading={isLoading}
					error={error}
					onRetry={() => refetch()}
					empty={
						q ? (
							<EmptyState title="No packages match">Try another search.</EmptyState>
						) : filter === 'installed' ? (
							<EmptyState
								title="No packages installed"
								action={
									available.length ? (
										<Button size="sm" onClick={() => setFilter('available')}>
											See available packages
										</Button>
									) : undefined
								}
							>
								Install packages from the Zango registry.
							</EmptyState>
						) : (
							<EmptyState title="Nothing to install">
								Every compatible package is already installed.
							</EmptyState>
						)
					}
				/>
			)}
			<p className="mt-3 text-[12px] text-t3">
				Updating and uninstalling packages aren't supported yet. Only versions compatible with this
				app's Zango release and installed dependencies are listed.
			</p>
			{installing && app && (
				<InstallPackageModal
					app={app}
					packages={available}
					initial={installing}
					onClose={() => setInstalling(null)}
				/>
			)}
		</Page>
	);
}
