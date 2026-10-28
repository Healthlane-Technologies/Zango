import { useQuery } from '@tanstack/react-query';
import { api } from './client';
import type { TemplateRef } from './templates';

// "Build with Agent": POST a one-line ask, a worker names and creates the app, then the
// hand-off opens a requirement conversation inside it seeded with the same ask.
// api/platform/agent_mode_admin/v1/views.py, apps/agent_mode/scaffold.py (state_payload).

const BASE = '/api/v1/platform/agent-mode';

/** apps/agent_mode/availability.py probe(None), trimmed to what the page shows. */
export interface AgentAvailability {
	available: boolean;
	reasons: string[];
	config: { model: string | null; analyst_model: string | null } & Record<string, unknown>;
}

/** Why Build with AI can't start, in plain words. Mirrors the classic panel's copy. */
export const AVAILABILITY_REASONS: Record<string, string> = {
	feature_disabled: 'Build with AI is turned off for this platform.',
	sdk_not_installed: 'The Claude Agent SDK is not installed on the server.',
	cli_not_found: 'The Claude Code binary could not be found on the server.',
	no_credentials: 'No Anthropic API key is configured for the platform.',
	skill_plugin_missing: 'The Zango skill plugin is missing from the install.',
	no_worker: 'No worker is consuming the agent_mode queue.',
};

export type ScaffoldStatus = 'naming' | 'creating' | 'ready' | 'failed';
export type ScaffoldAppState = 'pending' | 'ready' | 'failed';

export interface Scaffold {
	uuid: string;
	status: ScaffoldStatus;
	prompt: string;
	app_uuid: string | null;
	app_name: string;
	/** Display name; falls back to app_name server-side. */
	app_label: string;
	app_description: string;
	name_source: string;
	app_state: ScaffoldAppState;
	/** Set once the hand-off has opened the conversation. */
	requirement_uuid: string | null;
	error_message: string;
	created_at: string | null;
	/** The template the app is being created from, or null for a described app. */
	template?: TemplateRef | null;
	/** Documents uploaded with the ask (SOPs, RFPs…), handed to the analyst. */
	documents?: UploadedDocument[];
	/** The reference journey the draft starts from, or null to let the agent choose. */
	reference?: string | null;
}

export interface UploadedDocument {
	id: string | number;
	name: string;
	size: number;
	content_type: string;
	pages?: number | null;
}

/** The backend rejects longer prompts (AgentAppScaffoldCreateView.MAX_PROMPT_CHARS). */
export const MAX_PROMPT_CHARS = 10_000;
export const POLL_MS = 2500;

export const scaffoldKeys = {
	availability: ['agent-mode', 'availability'] as const,
	detail: (uuid: string) => ['agent-mode', 'scaffolds', uuid] as const,
};

export function useAgentAvailability() {
	return useQuery({
		queryKey: scaffoldKeys.availability,
		queryFn: () => api<AgentAvailability>(`${BASE}/availability/`),
		staleTime: 60_000,
	});
}

/** Terminal: nothing more will change without the user acting. */
export const isSettled = (s: Scaffold) =>
	s.status === 'failed' || s.app_state === 'failed' || !!s.requirement_uuid;

/** Polls a scaffold until it settles. `paused` stops polling (e.g. after repeated hand-off failures). */
export function useScaffold(uuid: string | null, { paused = false } = {}) {
	return useQuery({
		queryKey: scaffoldKeys.detail(uuid ?? ''),
		queryFn: () => api<Scaffold>(`${BASE}/scaffolds/${uuid}/`),
		enabled: !!uuid,
		refetchInterval: (q) => (paused || (q.state.data && isSettled(q.state.data)) ? false : POLL_MS),
		retry: 2,
	});
}

export interface ScaffoldInput {
	/** Optional with a template: documents can stand in for it, or the server's prefill. */
	prompt?: string;
	template_slug?: string;
	/** A template reference journey id; omitted lets the agent choose. */
	reference?: string;
	/** Files to draft from (pdf, docx, xlsx, csv, txt, md). */
	documents?: File[];
	/** 'open': the agent writes a free-design prototype next to the spec. */
	preview_mode?: 'open' | 'kit';
}

/** Multipart: the ask, the template, and any documents (one `documents` part per file). */
export const createScaffold = ({
	prompt,
	template_slug,
	reference,
	documents,
	preview_mode,
}: ScaffoldInput) => {
	const body = new FormData();
	if (preview_mode) body.append('preview_mode', preview_mode);
	if (prompt) body.append('prompt', prompt);
	if (template_slug) body.append('template_slug', template_slug);
	if (reference) body.append('reference', reference);
	for (const file of documents ?? []) body.append('documents', file, file.name);
	return api<Scaffold>(`${BASE}/scaffolds/`, 'POST', body);
};

/** Open the requirement conversation in the new app. 409 while the app is still being created. */
export const handOffScaffold = (uuid: string) =>
	api<Scaffold>(`${BASE}/scaffolds/${uuid}/requirement/`, 'POST', {});
