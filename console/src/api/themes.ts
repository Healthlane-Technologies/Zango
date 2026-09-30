import { useQuery } from '@tanstack/react-query';
import { api } from './client';
import { useApiMutation } from './hooks';

export interface ThemeConfig {
	color: Record<string, string>;
	button: { color?: string; background?: string; border_color?: string; border_radius?: string };
	typography: { font_family?: string; font_size_base?: string; line_height?: number | string };
}

export interface Theme {
	id: number;
	name: string;
	config: ThemeConfig;
	is_active: boolean;
	modified_at: string;
}

export const themeKeys = { list: (appId: string) => ['app', appId, 'themes'] as const };

export function useThemes(appId: string) {
	return useQuery({
		queryKey: themeKeys.list(appId),
		queryFn: () => api<{ themes: Theme[] }>(`/api/v1/apps/${appId}/themes/`).then((r) => r.themes),
	});
}

// ThemeModelSerializer json.loads() `config` after DRF has already parsed the multipart field,
// so the classic panel (transformToFormDataStringify) sends it JSON-encoded twice. Match that.
function themeForm(v: { name?: string; config?: ThemeConfig; is_active?: boolean }): FormData {
	const fd = new FormData();
	if (v.name !== undefined) fd.append('name', v.name);
	if (v.config !== undefined) fd.append('config', JSON.stringify(JSON.stringify(v.config)));
	if (v.is_active !== undefined) fd.append('is_active', String(v.is_active));
	return fd;
}

export function useCreateTheme(appId: string) {
	return useApiMutation({
		fn: (v: { name: string; config: ThemeConfig }) =>
			api(`/api/v1/apps/${appId}/themes/`, 'POST', themeForm(v)),
		invalidate: [themeKeys.list(appId)],
		success: 'Theme created',
	});
}

/** Edit a theme, or activate it (`{ is_active: true }`); the model deactivates the others. */
export function useUpdateTheme(appId: string) {
	return useApiMutation({
		fn: ({ id, ...v }: { id: number; name?: string; config?: ThemeConfig; is_active?: boolean }) =>
			api(`/api/v1/apps/${appId}/themes/${id}/`, 'PUT', themeForm(v)),
		invalidate: [themeKeys.list(appId)],
		success: (_r, v) => (v.is_active ? 'Theme activated' : 'Theme saved'),
	});
}
