import { useQuery } from '@tanstack/react-query';
import { api } from './client';

export interface ModelField {
	name: string;
	type: string;
	attributes: Record<string, unknown>;
}

export interface ModelRelationship extends ModelField {
	related_model: string;
}

export interface DataModel {
	name: string;
	fields: ModelField[];
	relationships: ModelRelationship[];
	meta: { verbose_name?: string; db_table?: string };
}

export interface CodeModule {
	name: string;
	path: string;
	models_count: number;
	views_count: number;
	templates_count: number;
	has_urls: boolean;
	has_policies: boolean;
	models: DataModel[];
}

export interface RouteEntry {
	root_path: string;
	module: string;
	pattern: string;
	full_url: string;
	name: string | null;
	full_module_path: string;
}

// GET /api/v1/apps/<uuid>/codebase/ — parsed from the app's workspace on disk.
export interface Codebase {
	app_name: string;
	version: string;
	modules: CodeModule[];
	package_routes: Array<{ re_path: string; package: string; url: string }>;
	app_routes: Array<{ module: string; re_path: string; url: string }>;
	route_tree: RouteEntry[];
	total_modules: number;
	total_packages: number;
	total_routes: number;
	last_modified: string | null;
}

export function useCodebase(appId: string) {
	return useQuery({
		queryKey: ['app', appId, 'codebase'],
		queryFn: () =>
			api<{ app_codebase: Codebase }>(`/api/v1/apps/${appId}/codebase/`).then(
				(r) => r.app_codebase,
			),
		retry: false,
	});
}
