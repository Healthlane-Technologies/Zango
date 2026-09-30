import { useQuery } from '@tanstack/react-query';
import { api } from './client';

const BASE = '/api/v1/platform/general';

export interface ThemeConfig {
	color?: Record<string, string>;
	button?: Record<string, string>;
	typography?: Record<string, string>;
	[key: string]: unknown;
}

// Writable fields of PlatformGeneralSettingsView (api/platform/platform_settings_admin).
export interface GeneralSettingsForm {
	auto_domain_enabled: boolean;
	base_domain: string;
	auto_domain_is_primary: boolean;
	default_timezone: string;
	default_date_format: string;
	default_datetime_format: string;
	default_language: string;
	default_theme_config: ThemeConfig | null;
}

export interface GeneralSettings extends GeneralSettingsForm {
	base_domain_valid: boolean;
	modified_at: string | null;
	options: {
		timezones: string[];
		date_formats: Array<{ value: string; example: string }>;
		datetime_formats: Array<{ value: string; example: string }>;
		languages: Array<{ value: string; label: string }>;
		default_theme_config: ThemeConfig;
	};
}

export const generalSettingsKey = ['platform-settings', 'general'] as const;

export function useGeneralSettings() {
	return useQuery({
		queryKey: generalSettingsKey,
		queryFn: () => api<GeneralSettings>(`${BASE}/`),
	});
}

export function saveGeneralSettings(form: GeneralSettingsForm) {
	return api<GeneralSettings & { message: string }>(`${BASE}/`, 'POST', form);
}

export function previewSubdomains(baseDomain: string) {
	return api<{ samples: string[] }>(
		`${BASE}/preview-subdomain/?base_domain=${encodeURIComponent(baseDomain)}`,
	);
}
