import { useQuery } from '@tanstack/react-query';
import { appKeys, type App } from './apps';
import { api } from './client';
import { useApiMutation } from './hooks';

export interface Option {
	id: string;
	label: string;
}

export interface GitConfig {
	repo_url?: string | null;
	branch?: { dev?: string | null; staging?: string | null; prod?: string | null };
}

export interface ExtraConfig {
	app_metadata?: { meta_title?: string | null };
	git_config?: GitConfig;
	sync_packages?: boolean;
	[key: string]: unknown;
}

export interface LoginMethods {
	password?: { enabled: boolean };
	otp?: { enabled: boolean };
	sso?: { enabled: boolean; providers?: unknown[] };
	oidc?: { enabled: boolean; providers?: unknown[] };
}

// Full TenantSerializerModel as returned by GET /api/v1/apps/<uuid>/.
export interface AppDetail extends App {
	tenant_type: string;
	timezone: string;
	language: string;
	date_format: string;
	datetime_format: string;
	date_format_display: string;
	datetime_format_display: string;
	logo: string | null;
	fav_icon: string | null;
	extra_config: ExtraConfig | null;
	created_at: string;
	deployed_on: string | null;
	auth_config?: { login_methods?: LoginMethods; two_factor_auth?: { required?: boolean } };
}

export interface DropdownOptions {
	timezones: Option[];
	date_formats: Option[];
	datetime_formats: Option[];
}

/** App detail plus the timezone/date-format options the settings form needs. */
export function useAppSettings(uuid: string) {
	return useQuery({
		queryKey: [...appKeys.detail(uuid), 'options'],
		queryFn: () =>
			api<{ app: AppDetail; dropdown_options: DropdownOptions }>(
				`/api/v1/apps/${uuid}/?include_dropdown_options=true`,
			),
		staleTime: 5 * 60_000,
	});
}

export interface AppSettingsUpdate {
	description: string;
	timezone: string;
	date_format: string;
	datetime_format: string;
	domains: Array<{ domain: string; is_primary: boolean }>;
	extra_config: ExtraConfig;
	logo?: File;
	fav_icon?: File;
}

/**
 * PUT /api/v1/apps/<uuid>/ as multipart. `domains` and `extra_config` are JSON strings; the
 * serializer replaces extra_config wholesale, so callers pass the merged object. The name is
 * read-only server-side and never sent.
 */
export function useUpdateApp(uuid: string) {
	return useApiMutation({
		fn: (v: AppSettingsUpdate) => {
			const fd = new FormData();
			fd.append('description', v.description);
			fd.append('timezone', v.timezone);
			fd.append('date_format', v.date_format);
			fd.append('datetime_format', v.datetime_format);
			fd.append('domains', JSON.stringify(v.domains));
			fd.append('extra_config', JSON.stringify(v.extra_config));
			if (v.logo) fd.append('logo', v.logo);
			if (v.fav_icon) fd.append('fav_icon', v.fav_icon);
			return api<{ message: string }>(`/api/v1/apps/${uuid}/`, 'PUT', fd);
		},
		// Prefix match: refreshes the plain detail (sidebar, overview) and the options variant.
		invalidate: [appKeys.all],
		success: 'Settings saved',
	});
}
