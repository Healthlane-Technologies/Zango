import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { api } from './client';

// UserRoleSerializerModel (api/platform/tenancy/v1/serializers.py), trimmed.
export interface RoleAuthConfig {
	redirect_url?: string;
	enforce_sso?: boolean;
	two_factor_auth?: { required?: boolean; allowed_methods?: string[] };
	session_policy?: Record<string, unknown>;
	[key: string]: unknown;
}

export interface Role {
	id: number;
	name: string;
	is_active: boolean;
	is_default: boolean;
	policies: number[];
	attached_policies: Array<{ id: number; name: string; type: string; description?: string | null }>;
	policies_count: { policies: number; policy_groups: number; total: number };
	users_count: number;
	auth_config: RoleAuthConfig;
	modified_at: string;
}

export interface PolicyOption {
	id: number;
	label: string;
	type: string;
	path: string | null;
}

export interface Paginated<T> {
	total_records: number;
	total_pages: number;
	next: string | null;
	previous: string | null;
	records: T[];
}

/** Built-in roles: their names are fixed and they can't be deactivated. */
export const RESERVED_ROLES = ['AnonymousUsers', 'SystemUsers'];

export interface RoleFilters {
	search?: string;
	active?: 'all' | 'active' | 'inactive';
}

export const roleKeys = {
	all: (app: string) => ['apps', app, 'roles'] as const,
	list: (app: string, f: RoleFilters) => [...roleKeys.all(app), 'list', f] as const,
};

function query(f: RoleFilters): string {
	// Roles are few; the classic panel also loads up to 100 in one page.
	const p = new URLSearchParams({ page: '1', page_size: '100', include_dropdown_options: 'true' });
	if (f.search) p.set('search', f.search);
	if (f.active && f.active !== 'all') p.set('search_is_active', String(f.active === 'active'));
	return p.toString();
}

export function useRoles(app: string, f: RoleFilters = {}) {
	return useQuery({
		queryKey: roleKeys.list(app, f),
		queryFn: () =>
			api<{ roles: Paginated<Role>; dropdown_options: { policies: PolicyOption[] } }>(
				`/api/v1/apps/${app}/roles/?${query(f)}`,
			),
		placeholderData: keepPreviousData,
	});
}

export interface RoleInput {
	name?: string;
	is_active?: boolean;
	policies?: number[];
	auth_config?: RoleAuthConfig;
}

// The role serializer accepts JSON, so lists and nested auth_config go as-is.
export const createRole = (app: string, body: RoleInput) =>
	api<{ message: string; role_id: number }>(`/api/v1/apps/${app}/roles/`, 'POST', body);

export const updateRole = (app: string, id: number, body: RoleInput) =>
	api<{ message: string; role_id: number }>(`/api/v1/apps/${app}/roles/${id}/`, 'PUT', body);

/** Server-computed hints (platform_*) that must not be written back. */
export function stripPlatformHints<T extends { session_policy?: Record<string, unknown> }>(
	config: T,
): T {
	const copy = structuredClone(config);
	if (copy.session_policy) {
		for (const k of Object.keys(copy.session_policy))
			if (k.startsWith('platform_')) delete copy.session_policy[k];
		if (Object.keys(copy.session_policy).length === 0) delete copy.session_policy;
	}
	return copy;
}
