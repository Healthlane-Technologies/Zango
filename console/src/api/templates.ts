import { useQuery } from '@tanstack/react-query';
import { api } from './client';

// The app template catalogue: /api/v1/platform/app-templates/ (published templates only).
// zango.apps.shared.app_templates — each template is a versioned pack with catalogue
// metadata, a requirement builder and a build skill.

const BASE = '/api/v1/platform/app-templates';

export interface NamedItem {
	name: string;
	description?: string;
}

export interface TemplateCatalogue {
	description?: string;
	aka?: string[];
	fits_when?: string[];
	gives_you?: string[];
	packages?: NamedItem[];
	roles?: NamedItem[];
	workflows?: NamedItem[];
	data_objects?: string[];
	integrations?: string[];
	compliance?: string[];
	recommended_agents?: Array<NamedItem & { id?: string; hitl?: string; mode?: string }>;
	app_name_prefill?: string;
	app_prompt_prefill?: string;
}

export interface TemplateSection {
	id: string;
	title: string;
	hint?: string;
}

export interface TemplateSummary {
	slug: string;
	name: string;
	category: string;
	/** A prototype icon key (heart, dna, truck…); unknown keys fall back to a template glyph. */
	icon: string;
	one_liner: string;
	is_beta: boolean;
	version: string;
	version_uuid: string;
	published_at: string | null;
	apps_using: number;
	spec_format: 'yaml' | 'markdown';
	catalogue: TemplateCatalogue;
	sections: TemplateSection[];
}

export interface TemplateVersionRef {
	version: string;
	status: 'published' | 'deprecated' | 'draft';
	published_at: string | null;
	changelog: string;
}

/** A curated example journey a draft can start from (template-owned). */
export interface TemplateReference {
	id: string;
	title: string;
	summary?: string;
	tags?: string[];
}

export interface TemplateDetail extends TemplateSummary {
	versions: TemplateVersionRef[];
	starter_yaml: string;
	example_yaml: string;
	/** Reference journeys the agent can draft from. */
	references?: TemplateReference[];
}

/** What apps, scaffolds and requirements say about the template they're built on. */
export interface TemplateRef {
	slug: string;
	name: string;
	version: string;
}

export const templateKeys = {
	all: ['app-templates'] as const,
	list: () => [...templateKeys.all, 'list'] as const,
	detail: (slug: string) => [...templateKeys.all, 'detail', slug] as const,
};

export function useTemplates() {
	return useQuery({
		queryKey: templateKeys.list(),
		queryFn: () =>
			api<{ templates: TemplateSummary[] }>(`${BASE}/templates/`).then((r) => r.templates),
		staleTime: 5 * 60_000,
	});
}

export function useTemplate(slug: string | undefined) {
	return useQuery({
		queryKey: templateKeys.detail(slug ?? ''),
		queryFn: () =>
			api<{ template: TemplateDetail }>(`${BASE}/templates/${slug}/`).then((r) => r.template),
		enabled: !!slug,
		staleTime: 5 * 60_000,
	});
}
