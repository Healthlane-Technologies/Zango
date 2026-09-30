import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { api } from './client';
import { buildQuery, type DropdownOption, type PageParams, type Paginated } from './logs';

// AppReleaseSerializer (api/platform/releases/v1/serializers.py). Releases are read-only here:
// they are created by `zango release` / the agent build, not from the panel.
export type ReleaseStatus = 'initiated' | 'in_progress' | 'released' | 'failed' | 'archived';

export interface Release {
	id: number;
	version: string;
	/** Often the literal "NA". */
	description: string | null;
	status: ReleaseStatus | string;
	last_git_hash: string | null;
	/** Pre-formatted in the app's datetime format and timezone, not ISO. */
	created_at: string;
}

export interface ReleaseFilters extends PageParams {
	status: string;
	version: string;
}

interface ReleasesResponse {
	releases: Paginated<Release>;
	dropdown_options?: { status: DropdownOption[]; version: DropdownOption[] };
}

export const releaseKeys = {
	list: (appId: string, f: ReleaseFilters) => ['apps', appId, 'releases', f] as const,
};

export function useReleases(appId: string, f: ReleaseFilters) {
	return useQuery({
		queryKey: releaseKeys.list(appId, f),
		queryFn: () =>
			api<ReleasesResponse>(
				`/api/v1/apps/${appId}/releases/?${buildQuery({
					page: f.page,
					page_size: f.pageSize,
					include_dropdown_options: 'true',
					search: f.search,
					search_status: f.status,
					search_version: f.version,
				})}`,
			),
		placeholderData: keepPreviousData,
	});
}
