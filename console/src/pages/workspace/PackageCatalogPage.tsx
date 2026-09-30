import { useMemo, useState } from 'react';
import { useApps } from '@/api/apps';
import { usePackageCatalog, type Package } from '@/api/packages';
import {
	Button,
	EmptyState,
	Page,
	PageHeader,
	SearchInput,
	Table,
	Toolbar,
	type Column,
} from '@/ui';
import { InstallPackageModal } from '../app/packages/InstallPackageModal';

export function PackageCatalogPage() {
	const { data: apps } = useApps();
	const { data, isLoading, error, refetch } = usePackageCatalog(apps);
	const [q, setQ] = useState('');
	const [installing, setInstalling] = useState<string | null>(null);

	const packages = useMemo(() => (data?.packages ?? []).filter((p) => p.versions?.length), [data]);
	const rows = useMemo(() => {
		const needle = q.trim().toLowerCase();
		return packages
			.filter((p) => !needle || p.name.toLowerCase().includes(needle))
			.sort((a, b) => a.name.localeCompare(b.name));
	}, [packages, q]);

	const columns: Column<Package>[] = [
		{
			key: 'name',
			header: 'Package',
			cell: (p) => <span className="mono font-medium text-t1">{p.name}</span>,
		},
		{
			key: 'latest',
			header: 'Latest',
			cell: (p) => <span className="mono">{p.versions?.[0]}</span>,
		},
		{
			key: 'versions',
			header: 'Versions',
			cell: (p) => (
				<span className="text-t3" title={p.versions?.join(', ')}>
					{p.versions?.length} released
				</span>
			),
		},
		{
			key: 'action',
			header: '',
			align: 'right',
			className: 'w-[140px]',
			cell: (p) => (
				<Button size="xs" onClick={() => setInstalling(p.name)}>
					Install in app…
				</Button>
			),
		},
	];

	return (
		<Page>
			<PageHeader
				title="Package catalog"
				description="Building blocks apps are composed from, published to the Zango package registry."
			/>
			<Toolbar>
				<SearchInput value={q} onChange={setQ} placeholder="Search packages" />
				{data && (
					<span className="ml-auto text-[12px] text-t3">
						Read through <b className="font-medium text-t2">{data.source.name}</b>; versions shown
						are the ones compatible with it.
					</span>
				)}
			</Toolbar>
			<Table
				columns={columns}
				rows={rows}
				rowKey={(p) => p.name}
				loading={isLoading || !apps}
				error={error}
				onRetry={() => refetch()}
				empty={
					q ? (
						<EmptyState title="No packages match">Try another search.</EmptyState>
					) : (
						<EmptyState title="Registry is empty">No packages are published yet.</EmptyState>
					)
				}
			/>
			{installing && apps && (
				<InstallPackageModal
					apps={apps}
					packages={packages}
					initial={installing}
					onClose={() => setInstalling(null)}
				/>
			)}
		</Page>
	);
}
