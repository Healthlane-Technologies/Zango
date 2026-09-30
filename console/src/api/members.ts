import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { api } from './client';
import { toFormData } from './hooks';

// PlatformUserSerializerModel (api/platform/auth/v1/serializers.py). `apps` is the
// full tenant serializer; only the fields the console shows are typed.
export interface Member {
	id: number;
	name: string;
	email: string;
	apps: Array<{ uuid: string; name: string }>;
	is_superadmin: boolean;
	is_active: boolean;
	last_login: string | null;
	created_at: string;
}

interface Paginated<T> {
	total_records: number;
	total_pages: number;
	next: string | null;
	previous: string | null;
	records: T[];
}

export interface MembersResponse {
	platform_users: Paginated<Member>;
	dropdown_options?: { apps: Array<{ id: string; label: string }> };
}

export type MemberStatus = 'all' | 'active' | 'inactive';

export interface MembersQuery {
	page: number;
	pageSize: number;
	search: string;
	status: MemberStatus;
}

export const memberKeys = {
	all: ['members'] as const,
	list: (q: MembersQuery) => [...memberKeys.all, 'list', q] as const,
};

export function useMembers(q: MembersQuery) {
	const params = new URLSearchParams({
		page: String(q.page),
		page_size: String(q.pageSize),
		include_dropdown_options: 'true',
		search: q.search,
	});
	// The list view reads `search_<column>` params (core.utils.get_search_columns).
	if (q.status !== 'all') params.set('search_is_active', q.status === 'active' ? 'true' : 'false');
	return useQuery({
		queryKey: memberKeys.list(q),
		queryFn: () => api<MembersResponse>(`/api/v1/auth/platform-users/?${params}`),
		placeholderData: keepPreviousData,
	});
}

// The views read `apps` with QueryDict.getlist, so each uuid is its own form field.
const memberForm = (values: Record<string, string | boolean | string[] | undefined>) =>
	toFormData(values, { repeatArrays: true });

export interface NewMember {
	name: string;
	email: string;
	password: string;
	apps: string[];
}

export function createMember(values: NewMember) {
	return api<{ message: string }>(
		'/api/v1/auth/platform-users/',
		'POST',
		memberForm({ ...values }),
	);
}

/**
 * Partial update. Omitted fields are left alone; `apps` replaces the whole list, and an
 * empty list is ignored by the server (it cannot remove every app).
 */
export function updateMember(
	id: number,
	values: Partial<{
		name: string;
		email: string;
		password: string;
		apps: string[];
		is_active: boolean;
	}>,
) {
	return api<{ message: string }>(`/api/v1/auth/platform-users/${id}/`, 'PUT', memberForm(values));
}

// PlatformUserModel.validate_password: 8-18 chars, upper, lower, digit, special from @$!%*#?&.
export const PASSWORD_RULE =
	/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{8,18}$/;
export const PASSWORD_HINT =
	'8–18 characters with upper and lower case, a number and one of @$!%*#?&.';
