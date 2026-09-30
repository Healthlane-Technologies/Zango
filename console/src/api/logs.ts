import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { api } from './client';

// Shapes shared by the paginated platform list endpoints (zango.core.api.utils.ZangoAPIPagination).
export interface Paginated<T> {
	total_records: number;
	total_pages: number;
	next: string | null;
	previous: string | null;
	records: T[];
}

export interface DropdownOption {
	id: string | number | null;
	label: string | null;
}

/** `search_<col>` date filters take `{"start":"YYYY-MM-DD","end":"YYYY-MM-DD"}`, read in the app's timezone. */
export interface DateRange {
	start: string;
	end: string;
}

type QueryValue = string | number | DateRange | null | undefined;

/** Build a query string, skipping empty values and JSON-encoding date ranges. */
export function buildQuery(params: Record<string, QueryValue>): string {
	const q = new URLSearchParams();
	for (const [k, v] of Object.entries(params)) {
		if (v === undefined || v === null || v === '') continue;
		q.set(k, typeof v === 'object' ? JSON.stringify(v) : String(v));
	}
	return q.toString();
}

export interface PageParams {
	page: number;
	pageSize: number;
	search: string;
}

/* ---------- audit logs: /api/v1/apps/<uuid>/auditlog/ ---------- */

/** `dynamic_models` = app data; `core_models` = framework objects (users, roles, policies…); omitted = both. */
export type AuditModelType = 'dynamic_models' | 'core_models' | undefined;

/** Field -> [before, after] for creates/updates; m2m changes come as an object. Values are stringified by the server. */
export type AuditChanges = Record<
	string,
	[string, string] | { type: 'm2m'; objects: string[]; operation: string } | unknown
>;

export interface AuditLog {
	id: number;
	actor: string | null;
	actor_type: 'tenant_actor' | 'platform_actor' | null;
	action: 'Create' | 'Update' | 'Delete' | string;
	object_id: number | null;
	object_uuid: string | null;
	object_type: string;
	/** Pre-formatted in the app's datetime format and timezone, not ISO. */
	timestamp: string;
	changes: AuditChanges | null;
}

export interface AuditLogFilters extends PageParams {
	modelType: AuditModelType;
	/** "0" create, "1" update, "2" delete. */
	action: string;
	/** ContentType id, from dropdown_options.object_type. */
	objectType: string;
	range: DateRange | null;
}

interface AuditLogResponse {
	audit_logs: Paginated<AuditLog>;
	total_stats: {
		total_changes: number;
		total_created: number;
		total_updated: number;
		total_deleted: number;
	};
	dropdown_options?: { action: DropdownOption[]; object_type: DropdownOption[] };
}

export const logKeys = {
	all: (appId: string) => ['apps', appId, 'logs'] as const,
	audit: (appId: string, f: AuditLogFilters) => [...logKeys.all(appId), 'audit', f] as const,
	access: (appId: string, f: AccessLogFilters) => [...logKeys.all(appId), 'access', f] as const,
};

export function useAuditLogs(appId: string, f: AuditLogFilters) {
	return useQuery({
		queryKey: logKeys.audit(appId, f),
		queryFn: () =>
			api<AuditLogResponse>(
				`/api/v1/apps/${appId}/auditlog/?${buildQuery({
					page: f.page,
					page_size: f.pageSize,
					include_dropdown_options: 'true',
					model_type: f.modelType,
					search: f.search,
					search_action: f.action,
					search_object_type: f.objectType,
					search_timestamp: f.range,
				})}`,
			),
		placeholderData: keepPreviousData,
	});
}

/* ---------- access logs: /api/v1/apps/<uuid>/access-logs/ ---------- */

export interface AccessLog {
	id: number;
	ip_address: string | null;
	/** "Name (id)" or "NA". */
	user: string;
	username: string | null;
	attempt_type: 'login' | 'switch_role' | string | null;
	/** Pre-formatted in the app's datetime format, or "NA". */
	attempt_time: string;
	/** Role name or "NA". */
	role: string;
	user_agent: string | null;
	is_login_successful: boolean;
	session_expired_at: string;
}

export interface AccessLogFilters extends PageParams {
	attemptType: string;
	/** "successful" | "failed" | "". */
	result: string;
	/** Role id, from dropdown_options.role. */
	role: string;
	range: DateRange | null;
}

interface AccessLogResponse {
	access_logs: Paginated<AccessLog>;
	total_failed_attempts: number;
	dropdown_options?: {
		role: DropdownOption[];
		attempt_type: DropdownOption[];
		is_login_successful: DropdownOption[];
	};
}

export function useAccessLogs(appId: string, f: AccessLogFilters) {
	return useQuery({
		queryKey: logKeys.access(appId, f),
		queryFn: () =>
			api<AccessLogResponse>(
				`/api/v1/apps/${appId}/access-logs/?${buildQuery({
					page: f.page,
					page_size: f.pageSize,
					include_dropdown_options: 'true',
					search: f.search,
					search_attempt_type: f.attemptType,
					search_is_login_successful: f.result,
					search_role: f.role,
					search_attempt_time: f.range,
				})}`,
			),
		placeholderData: keepPreviousData,
	});
}

/** The API uses the literal string "NA" for missing values. */
export const na = (v: string | null | undefined): string | null => (v && v !== 'NA' ? v : null);
