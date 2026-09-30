import { useQuery } from '@tanstack/react-query';
import { api } from './client';
import type { TemplateRef } from './templates';

export interface AppDomain {
	domain: string;
	is_primary: boolean;
}

// Subset of TenantSerializerModel (api/platform/tenancy/v1/serializers.py) the console uses.
export interface App {
	uuid: string;
	name: string;
	schema_name: string;
	description: string | null;
	status: string;
	domains: AppDomain[];
	domain_url: string | null;
	last_released_version: string | null;
	modified_at: string;
	/** The template the app is built on (AppTemplateBinding), or null for a from-scratch app. */
	template?: TemplateRef | null;
}

export const appKeys = {
	all: ['apps'] as const,
	list: () => [...appKeys.all, 'list'] as const,
	detail: (uuid: string) => [...appKeys.all, 'detail', uuid] as const,
};

export function useApps() {
	return useQuery({
		queryKey: appKeys.list(),
		queryFn: () => api<{ apps: App[] }>('/api/v1/apps/').then((r) => r.apps),
	});
}

export function useApp(uuid: string | undefined) {
	return useQuery({
		queryKey: appKeys.detail(uuid ?? ''),
		queryFn: () => api<{ app: App }>(`/api/v1/apps/${uuid}/`).then((r) => r.app),
		enabled: !!uuid,
	});
}
