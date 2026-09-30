import { useQuery } from '@tanstack/react-query';
import { api } from './client';
import { appKeys, type App } from './apps';
import { MAX_PAGE_SIZE, type Paginated } from './policies';

// Built by zango.core.package_utils.get_all_packages from the S3 registry plus the app's
// manifest.json. `versions` only lists versions compatible with the app's Zango version and
// installed dependencies, newest first.
export interface Package {
	name: string;
	versions?: string[];
	status: 'Installed' | 'Not Installed';
	installed_version?: string;
	/** Signed link to the package's configuration page, when it has one. */
	config_url: string | null;
}

interface PackagesResponse {
	packages: Paginated<Package> & { installed_count: number };
}

export const packageKeys = {
	all: (appId: string) => [...appKeys.detail(appId), 'packages'] as const,
	catalog: ['package-catalog'] as const,
};

// The registry listing is slow (S3 listing plus a manifest fetch per version), so cache it.
const REGISTRY_STALE_MS = 5 * 60_000;

function fetchPackages(appId: string) {
	// The whole list is built in memory before paging; one page of 100 covers the registry.
	return api<PackagesResponse>(
		`/api/v1/apps/${appId}/packages/?page=1&page_size=${MAX_PAGE_SIZE}`,
	).then((r) => r.packages.records);
}

export function usePackages(appId: string) {
	return useQuery({
		queryKey: packageKeys.all(appId),
		queryFn: () => fetchPackages(appId),
		staleTime: REGISTRY_STALE_MS,
	});
}

/** Newest compatible version, if it is newer than the installed one. */
export function updateAvailable(p: Package): string | undefined {
	const latest = p.versions?.[0];
	if (!latest || !p.installed_version) return undefined;
	return compareVersions(latest, p.installed_version) > 0 ? latest : undefined;
}

export function compareVersions(a: string, b: string): number {
	const pa = a.split(/[.-]/).map((x) => parseInt(x, 10) || 0);
	const pb = b.split(/[.-]/).map((x) => parseInt(x, 10) || 0);
	for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
		const d = (pa[i] ?? 0) - (pb[i] ?? 0);
		if (d) return d;
	}
	return 0;
}

const CATALOG_SOURCE_KEY = 'console.packageCatalogSource';

function rememberedSource(): string | null {
	try {
		return localStorage.getItem(CATALOG_SOURCE_KEY);
	} catch {
		return null;
	}
}

function rememberSource(uuid: string) {
	try {
		localStorage.setItem(CATALOG_SOURCE_KEY, uuid);
	} catch {
		// Storage unavailable; we just probe again next time.
	}
}

/**
 * The registry is only exposed per app. Use the first app whose listing succeeds (apps
 * without a workspace on disk fail with a fast 500) and report which app it came from. The
 * app that worked last time is tried first.
 */
export function usePackageCatalog(apps: App[] | undefined) {
	return useQuery({
		queryKey: packageKeys.catalog,
		enabled: !!apps,
		staleTime: REGISTRY_STALE_MS,
		queryFn: async () => {
			let lastError: unknown = new Error('No apps to read the package registry from.');
			const preferred = rememberedSource();
			const ordered = [...(apps ?? [])].sort(
				(a, b) => Number(b.uuid === preferred) - Number(a.uuid === preferred),
			);
			for (const app of ordered) {
				try {
					const packages = await fetchPackages(app.uuid);
					rememberSource(app.uuid);
					return { source: app, packages };
				} catch (e) {
					lastError = e;
				}
			}
			throw lastError;
		},
	});
}

/**
 * Install a package version into an app. Runs migrations and re-syncs policies and tasks,
 * so it can take a while. The endpoint answers 200 even when installation fails, with the
 * failure in the message, so check the message too.
 */
export async function installPackage(appId: string, name: string, version: string) {
	const fd = new FormData();
	fd.append('name', name);
	fd.append('version', version);
	const { message } = await api<{ message: string }>(
		`/api/v1/apps/${appId}/packages/?action=install`,
		'POST',
		fd,
	);
	if (message.startsWith('Package could not be installed')) {
		throw new Error(message.split('\n')[0]);
	}
	return message;
}
