import { useQuery } from '@tanstack/react-query';
import { api } from './client';
import { appKeys } from './apps';

// PolicySerializer (api/platform/permissions/v1/serializers.py).
export interface Policy {
	id: number;
	name: string;
	description: string | null;
	statement: unknown;
	roles: Array<{ id: number; name: string }>;
	type: 'system' | 'user';
	/** Module the policy was synced from; null for system policies. */
	path: string | null;
	/** Preformatted in the app's timezone, e.g. "05 April 2025 19:55". Not ISO. */
	created_at: string;
}

export interface RoleOption {
	id: number;
	label: string;
}

/** ZangoAPIPagination.get_paginated_response_data (core/api/utils.py). */
export interface Paginated<T> {
	total_records: number;
	total_pages: number;
	records: T[];
}

/** The backend caps page_size at 100. */
export const MAX_PAGE_SIZE = 100;

/**
 * Fetch every page of a paginated list. Used for per-app lists that stay small (policies,
 * tasks) so search and filters can run on the client across all records.
 */
export async function fetchAllPages<T, R>(
	url: (page: number) => string,
	pick: (response: R) => Paginated<T>,
): Promise<{ records: T[]; first: R }> {
	const first = await api<R>(url(1));
	const { total_pages, records } = pick(first);
	const rest = await Promise.all(
		Array.from({ length: Math.max(0, total_pages - 1) }, (_, i) =>
			api<R>(url(i + 2)).then((r) => pick(r).records),
		),
	);
	return { records: [...records, ...rest.flat()], first };
}

export const policyKeys = {
	all: (appId: string) => [...appKeys.detail(appId), 'policies'] as const,
};

interface PoliciesResponse {
	policies: Paginated<Policy>;
	dropdown_options?: { roles: RoleOption[] };
}

export function usePolicies(appId: string) {
	return useQuery({
		queryKey: policyKeys.all(appId),
		queryFn: async () => {
			const { records, first } = await fetchAllPages<Policy, PoliciesResponse>(
				(page) =>
					`/api/v1/apps/${appId}/policies/?page=${page}&page_size=${MAX_PAGE_SIZE}${page === 1 ? '&include_dropdown_options=true' : ''}`,
				(r) => r.policies,
			);
			return { policies: records, roles: first.dropdown_options?.roles ?? [] };
		},
	});
}

/**
 * Replace a policy's roles. The backend reads roles with `getlist`, so each id is its own
 * form field; sending none clears them. For system policies only roles are saved.
 */
export function updatePolicyRoles(appId: string, policy: Policy, roleIds: number[]) {
	const fd = new FormData();
	fd.append('name', policy.name);
	fd.append('description', policy.description ?? '');
	roleIds.forEach((id) => fd.append('roles', String(id)));
	return api<{ message: string }>(`/api/v1/apps/${appId}/policies/${policy.id}/`, 'PUT', fd);
}

/** Re-read policies declared in the app's code (policies.json in each module). */
export function syncPolicies(appId: string) {
	return api<{ message: string }>(
		`/api/v1/apps/${appId}/policies/?action=sync_policies`,
		'POST',
		new FormData(),
	);
}
