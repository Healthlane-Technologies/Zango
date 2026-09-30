import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { api } from './client';
import type { Paginated, Role } from './roles';

// AppUserModelSerializerModel (api/platform/tenancy/v1/serializers.py), trimmed.
export interface AppUser {
	id: number;
	name: string;
	email: string | null;
	mobile: string | null;
	pn_country_code: string | null;
	is_active: boolean;
	roles: Role[];
	/** Effective config (tenant, role and user merged), not just the user's own. */
	auth_config: {
		two_factor_auth?: { required?: boolean; allowed_methods?: string[]; allowedMethods?: string[] };
	};
	/** Already formatted in the app's timezone, e.g. "18 Sep 2026 11:35 PM". */
	last_login: string | null;
	date_joined: string | null;
}

export interface UserFilters {
	page: number;
	pageSize: number;
	search?: string;
	active?: 'all' | 'active' | 'inactive';
	/** Role name; the backend matches it with icontains. */
	role?: string;
}

export interface UsersResponse {
	users: Paginated<AppUser> & { active_count: number; inactive_count: number };
	pn_country_code: string;
	dropdown_options: { roles: Array<{ id: number; label: string }> };
}

export const userKeys = {
	all: (app: string) => ['apps', app, 'users'] as const,
	list: (app: string, f: UserFilters) => [...userKeys.all(app), 'list', f] as const,
};

function query(f: UserFilters): string {
	const p = new URLSearchParams({
		page: String(f.page),
		page_size: String(f.pageSize),
		include_dropdown_options: 'true',
	});
	if (f.search) p.set('search', f.search);
	if (f.active && f.active !== 'all') p.set('search_is_active', String(f.active === 'active'));
	if (f.role) p.set('search_roles_access', f.role);
	return p.toString();
}

export function useUsers(app: string, f: UserFilters) {
	return useQuery({
		queryKey: userKeys.list(app, f),
		queryFn: () => api<UsersResponse>(`/api/v1/apps/${app}/users/?${query(f)}`),
		placeholderData: keepPreviousData,
	});
}

export interface UserInput {
	name?: string;
	email?: string;
	/** E.164, e.g. "+919876543210". */
	mobile?: string;
	password?: string;
	roles?: number[];
	is_active?: boolean;
	auth_config?: { two_factor_auth: { required: boolean; allowed_methods: string[] } };
}

/**
 * The user views read `request.data.getlist("roles")`, so this must be multipart with one
 * `roles` entry per id (the shared toFormData JSON-encodes arrays, which breaks that).
 */
function userForm(input: UserInput, { create }: { create: boolean }): FormData {
	const fd = new FormData();
	if (input.name !== undefined) fd.append('name', input.name);
	// create_user indexes email/mobile/password directly, so send them even when blank.
	if (input.email !== undefined || create) fd.append('email', input.email ?? '');
	if (input.mobile !== undefined || create) fd.append('mobile', input.mobile ?? '');
	if (input.password !== undefined || create) fd.append('password', input.password ?? '');
	for (const id of input.roles ?? []) fd.append('roles', String(id));
	if (input.is_active !== undefined) fd.append('is_active', String(input.is_active));
	if (input.auth_config) fd.append('auth_config', JSON.stringify(input.auth_config));
	return fd;
}

export const createUser = (app: string, input: UserInput) =>
	api<{ message: string }>(`/api/v1/apps/${app}/users/`, 'POST', userForm(input, { create: true }));

export const updateUser = (app: string, id: number, input: UserInput) =>
	api<{ message: string; user_id: number }>(
		`/api/v1/apps/${app}/users/${id}/`,
		'PUT',
		userForm(input, { create: false }),
	);
