import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { api } from './client';
import { toFormData, useApiMutation } from './hooks';

export interface Secret {
	id: number;
	key: string;
	is_active: boolean;
	/** Pre-formatted in the app's timezone by the server. */
	created_at: string;
	modified_at: string;
}

export interface Paginated<T> {
	total_records: number;
	total_pages: number;
	next: string | null;
	previous: string | null;
	records: T[];
}

export const secretKeys = {
	all: (appId: string) => ['app', appId, 'secrets'] as const,
	list: (appId: string, page: number, search: string) =>
		[...secretKeys.all(appId), page, search] as const,
};

export const SECRETS_PAGE_SIZE = 10;

export function useSecrets(appId: string, page: number, search: string) {
	return useQuery({
		queryKey: secretKeys.list(appId, page, search),
		queryFn: () => {
			const qs = new URLSearchParams({
				page: String(page),
				page_size: String(SECRETS_PAGE_SIZE),
				search,
			});
			return api<{ secrets: Paginated<Secret> }>(`/api/v1/apps/${appId}/secrets/?${qs}`).then(
				(r) => r.secrets,
			);
		},
		placeholderData: keepPreviousData,
	});
}

/** Decrypted value; fetched on demand, never cached. */
export function fetchSecretValue(appId: string, id: number) {
	return api<{ secret_value: string }>(
		`/api/v1/apps/${appId}/secrets/?action=get_secret_value&secret_id=${id}`,
	).then((r) => r.secret_value);
}

/** SecretsModel.key validator. */
export const SECRET_KEY_RE = /^[A-Z][a-z0-9_]*$/;

export function useCreateSecret(appId: string) {
	return useApiMutation({
		fn: (v: { key: string; value: string }) =>
			api(`/api/v1/apps/${appId}/secrets/`, 'POST', toFormData(v)),
		invalidate: [secretKeys.all(appId)],
		success: (_r, v) => `Added ${v.key}`,
	});
}

/** Partial update; omit `value` to keep the current one (the serializer re-saves it). */
export function useUpdateSecret(appId: string) {
	return useApiMutation({
		fn: ({ id, ...v }: { id: number; key?: string; value?: string; is_active?: boolean }) =>
			api(`/api/v1/apps/${appId}/secrets/?secret_id=${id}`, 'PUT', toFormData(v)),
		invalidate: [secretKeys.all(appId)],
		success: (_r, v) =>
			v.is_active === undefined
				? 'Secret saved'
				: v.is_active
					? 'Secret activated'
					: 'Secret deactivated',
	});
}

/** Only inactive secrets can be deleted; the API rejects active ones. */
export function useDeleteSecret(appId: string) {
	return useApiMutation({
		fn: (s: Secret) => api(`/api/v1/apps/${appId}/secrets/?secret_id=${s.id}`, 'DELETE'),
		invalidate: [secretKeys.all(appId)],
		success: (_r, s) => `Deleted ${s.key}`,
	});
}
