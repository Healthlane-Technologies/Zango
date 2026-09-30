import { useQuery } from '@tanstack/react-query';
import { api } from './client';

const BASE = '/api/v1/platform/logs';

export type LogComponent = 'app' | 'celery' | 'celery_beat';

export interface ConnectorConfig {
	region?: string;
	log_group_name?: string;
	stream_prefix?: string;
	format?: string;
	/** Masked by the server to its last 4 characters. */
	aws_access_key_id?: string;
	/** Always blank on read; blank on write keeps the stored value. */
	aws_secret_access_key?: string;
	role_arn?: string;
}

export interface ConnectorRow {
	object_uuid: string;
	environment: string;
	component: LogComponent;
	connector: string;
	config: ConnectorConfig;
	is_active: boolean;
	created_at: string;
	modified_at: string;
}

export interface ConnectorsResponse {
	environment: string;
	rows: ConnectorRow[];
	available_types: string[];
	components: LogComponent[];
}

export const logKeys = {
	connectors: ['platform-logs', 'connectors'] as const,
	components: ['platform-logs', 'components'] as const,
	tenants: (component: string, since: string) =>
		['platform-logs', 'tenants', component, since] as const,
};

export function useConnectors() {
	return useQuery({
		queryKey: logKeys.connectors,
		queryFn: () => api<ConnectorsResponse>(`${BASE}/connectors/`),
	});
}

export interface ConnectorPayload {
	environment: string;
	component: LogComponent;
	connector: string;
	config: ConnectorConfig;
	is_active: boolean;
}

/** Upsert by (environment, component). Validation errors come back in `response.errors`. */
export function saveConnector(payload: ConnectorPayload) {
	return api<ConnectorRow>(`${BASE}/connectors/`, 'POST', payload);
}

export function testConnector(payload: ConnectorPayload) {
	return api<{ ok: boolean; stream_count: number; newest_event_ts: string | null }>(
		`${BASE}/connectors/test/`,
		'POST',
		payload,
	);
}

// ---------- platform-wide log browsing (all tenants; super admins only) ----------

export interface LogLine {
	ts: string;
	level: string;
	message: string;
	stream: string;
	structured: unknown;
	cursor_token: string;
}

export interface LogPage {
	lines: LogLine[];
	next_cursor: { token: string; direction: string } | null;
	has_more: boolean;
}

export function usePlatformLogComponents() {
	return useQuery({
		queryKey: logKeys.components,
		queryFn: () =>
			api<{
				environment: string;
				components: Array<{ key: LogComponent; label: string; configured: boolean }>;
			}>(`${BASE}/components/`),
	});
}

export function usePlatformLogTenants(component: string | undefined, since: string) {
	return useQuery({
		queryKey: logKeys.tenants(component ?? '', since),
		queryFn: () =>
			api<{ tenants: string[] }>(
				`${BASE}/${component}/tenants/?since=${encodeURIComponent(since)}`,
			),
		enabled: !!component,
		retry: false,
	});
}

export interface LogFilters {
	since: string;
	levels: string[];
	q: string;
	tenants: string[];
}

export function logQuery(f: LogFilters, extra: Record<string, string> = {}): string {
	const p = new URLSearchParams({ since: f.since, limit: '200' });
	if (f.levels.length) p.set('levels', f.levels.join(','));
	if (f.q) p.set('q', f.q);
	if (f.tenants.length) p.set('tenants', f.tenants.join(','));
	for (const [k, v] of Object.entries(extra)) p.set(k, v);
	return p.toString();
}

export function fetchLogs(component: string, f: LogFilters, before?: string) {
	return api<LogPage>(`${BASE}/${component}/?${logQuery(f, before ? { before } : {})}`);
}

export function fetchLogTail(component: string, f: LogFilters, after: string) {
	return api<LogPage>(`${BASE}/${component}/tail/?${logQuery(f, { after })}`);
}
