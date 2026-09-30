import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import type { Paginated } from '@/api/secrets';

// Lightweight reads for the Overview page only; the full screens own richer hooks.

export interface ReleaseSummary {
	id: number;
	version: string;
	description: string;
	status: string;
	last_git_hash: string | null;
	created_at: string;
}

export interface AuditEntry {
	id: number;
	actor: string | null;
	action: string;
	object_type: string;
	object_id: number | null;
	timestamp: string;
}

const count = (appId: string, path: string, key: string) => () =>
	api<Record<string, Paginated<unknown>>>(`/api/v1/apps/${appId}/${path}/?page=1&page_size=1`).then(
		(r) => r[key].total_records,
	);

export function useOverviewCounts(appId: string) {
	const users = useQuery({
		queryKey: ['app', appId, 'overview', 'users'],
		queryFn: count(appId, 'users', 'users'),
	});
	const roles = useQuery({
		queryKey: ['app', appId, 'overview', 'roles'],
		queryFn: count(appId, 'roles', 'roles'),
	});
	return { users, roles };
}

export function useRecentReleases(appId: string) {
	return useQuery({
		queryKey: ['app', appId, 'overview', 'releases'],
		queryFn: () =>
			api<{ releases: Paginated<ReleaseSummary> }>(
				`/api/v1/apps/${appId}/releases/?page=1&page_size=3`,
			).then((r) => r.releases),
	});
}

export function useRecentAudit(appId: string) {
	return useQuery({
		queryKey: ['app', appId, 'overview', 'audit'],
		queryFn: () =>
			api<{ audit_logs: Paginated<AuditEntry> }>(
				`/api/v1/apps/${appId}/auditlog/?page=1&page_size=6`,
			).then((r) => r.audit_logs.records),
	});
}
