import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { api, ApiError } from './client';
import { useApiMutation } from './hooks';
import { buildQuery } from './logs';
import type { Paginated } from './secrets';

// The app's AI module: /api/v1/apps/<uuid>/ai/ (zango.api.platform.ai.v1).
// Quirks worth knowing:
// - Toggles read `is_enabled` with bool(), so it must be a JSON boolean, never form data.
// - Money fields are decimal strings, except agent `metrics` and the test result's cost.
// - Agents reference prompts and tools by name; agent timestamps are tenant-formatted strings.
// - A page past the last one is a 500 ("Invalid page.") on DRF lists; reset to page 1 on filter changes.

const base = (appId: string) => `/api/v1/apps/${appId}/ai`;

/* ---------- providers ---------- */

export interface ProviderModelInfo {
	id: string;
	name: string;
	context_window: number;
	max_output_tokens: number;
	input_cost_per_mtok?: number | null;
	output_cost_per_mtok?: number | null;
	supports_tools: boolean;
	supports_vision: boolean;
	supports_streaming: boolean;
}

export interface ConfigField {
	name: string;
	type: 'secret' | 'string' | 'url' | 'integer' | 'select';
	required: boolean;
	label: string;
	help_text?: string;
	default?: string | number;
	/** Only on `default_model`, which is a top-level body field, not part of `config`. */
	options_from?: 'supported_models';
}

export interface AvailableProvider {
	slug: string;
	display_name: string;
	icon: string | null;
	/** Static list; empty for azure_openai and bedrock, which need a live fetch. */
	supported_models: ProviderModelInfo[];
	config_fields: ConfigField[];
}

export interface ProviderModel {
	id: number;
	model_id: string;
	display_name: string;
	input_cost_per_mtok_override: string | null;
	output_cost_per_mtok_override: string | null;
	is_enabled: boolean;
	rate_limit_rpm: number | null;
}

export interface Provider {
	id: number;
	name: string;
	description: string;
	provider_slug: string;
	default_model: string | null;
	is_enabled: boolean;
	is_validated: boolean;
	last_validated_at: string | null;
	validation_error: string | null;
	rate_limit_rpm: number | null;
	rate_limit_tpm: number | null;
	monthly_budget_usd: string | null;
	budget_alert_threshold: string;
	current_month_spend_usd: string | number | null;
	total_invocations: number;
	total_input_tokens: number;
	total_output_tokens: number;
	total_cost_usd: string;
	created_at: string;
	modified_at: string;
	status: 'active' | 'inactive';
	/** Counts every model row, enabled or not. */
	models_count: number;
	/** Saved config with secrets masked (`sk-ant...****abcd`). */
	masked_config: Record<string, unknown>;
	budget_status: { within_budget: boolean; used: string; limit: string | null; pct: number };
	/** Despite the name: every model row, including disabled ones. */
	enabled_models: ProviderModel[];
}

export interface ProviderInput {
	name: string;
	description?: string;
	provider_slug?: string;
	config?: Record<string, unknown>;
	default_model: string;
	fetched_models?: ProviderModelInfo[];
	rate_limit_rpm?: number | null;
	monthly_budget_usd?: string | null;
}

/** Agents blocking a provider disable/delete or a prompt delete (409 with `agents`). */
export function inUseAgents(err: unknown): Array<{ id: number; name: string }> | null {
	if (!(err instanceof ApiError) || err.status !== 409) return null;
	const agents = (err.body as { response?: { agents?: Array<{ id: number; name: string }> } })
		?.response?.agents;
	return agents ?? null;
}

/** fetch-models answers bad credentials with `error_type: 'auth_error'`. */
export function isAuthError(err: unknown): boolean {
	return (
		err instanceof ApiError &&
		(err.body as { response?: { error_type?: string } })?.response?.error_type === 'auth_error'
	);
}

/* ---------- prompts ---------- */

export type PromptType = 'system' | 'user';

export interface PromptVersion {
	id: number;
	version_number: number;
	content: string;
	change_description: string;
	status: 'draft' | 'active' | 'inactive';
	variables: string[];
	created_at: string;
	created_by: string;
	modified_at: string;
}

export interface Prompt {
	id: number;
	name: string;
	description: string;
	type: PromptType;
	is_active: boolean;
	active_version: PromptVersion | null;
	active_version_number: number | null;
	/** Newest first. */
	versions: PromptVersion[];
	total_versions: number;
	used_by_agents: Array<{ id: number; name: string }>;
	created_at: string;
	modified_at: string;
}

export interface PromptStats {
	total_prompts: number;
	active_versions: number;
	total_versions: number;
}

/* ---------- agents ---------- */

export type OutputSchema = 'JSON' | 'Text' | 'Markdown';

export interface Agent {
	id: number;
	name: string;
	description: string;
	provider: number | null;
	provider_name: string | null;
	provider_slug: string | null;
	model: string | null;
	system_prompt: number | null;
	system_prompt_name: string | null;
	system_prompt_variables: string[];
	user_prompt: number | null;
	user_prompt_name: string | null;
	user_prompt_variables: string[];
	temperature: number;
	max_tokens: number;
	timeout_seconds: number;
	output_schema: OutputSchema;
	output_json_schema: Record<string, unknown> | null;
	/** Tool names. */
	tools: string[];
	is_enabled: boolean;
	status: 'active' | 'disabled';
	total_invocations: number;
	total_cost_usd: string | number | null;
	short_term_memory: boolean;
	short_term_memory_max_messages: number;
	session_count: number;
	/** Display strings in the app's timezone, not ISO. */
	created_at: string;
	modified_at: string;
	metrics?: {
		totalInvocations: number;
		successRate: number;
		avgLatency: string;
		totalCost: number;
		avgInputTokens: number;
		avgOutputTokens: number;
		invocations24h: number;
		avgCost: number;
	};
}

export interface AgentInput {
	name: string;
	description: string;
	provider_id: number;
	model: string;
	/** Prompt names; '' unlinks. */
	system_prompt_name: string;
	user_prompt_name: string;
	temperature: number;
	max_tokens: number;
	timeout_seconds: number;
	output_schema: OutputSchema;
	output_json_schema: Record<string, unknown> | null;
	tools: string[];
	short_term_memory: boolean;
	short_term_memory_max_messages: number;
}

export interface AgentTestInput {
	variables: Record<string, string>;
	system_variables: Record<string, string>;
	user_message: string;
	files: File[];
}

export interface AgentTestResult {
	/** First 2000 characters. */
	content: string;
	model: string;
	latency_ms: number;
	input_tokens: number;
	output_tokens: number;
	cost_usd: number;
}

export interface MemorySession {
	id: number;
	session_id: string;
	user_ref: string;
	is_active: boolean;
	last_active_at: string;
	metadata: Record<string, unknown>;
	message_count: number;
	created_at: string;
	modified_at: string;
}

export interface MemoryMessage {
	id: number;
	role: 'user' | 'assistant' | 'tool' | 'assistant_tool_use';
	content: unknown;
	sequence: number;
	invocation: number | null;
	created_at: string;
}

/* ---------- tools ---------- */

export type ToolSafety = 'read_only' | 'write' | 'external';

export interface Tool {
	id: number;
	name: string;
	description: string;
	section: string;
	safety: ToolSafety;
	timeout_seconds: number;
	rate_limit_rpm: number | null;
	return_type: string | null;
	is_active: boolean;
	total_calls: number;
	total_errors: number;
	total_timeouts: number;
	avg_execution_ms: number;
	last_called_at: string | null;
	schema_hash: string;
	python_path: string;
	params_count: number;
	memory_policy: 'include' | 'exclude';
}

export interface ToolDetail extends Omit<Tool, 'params_count'> {
	parameters_schema: Record<string, unknown>;
	parameters_display: Array<{
		name: string;
		type: string;
		required: boolean;
		description: string;
		enum: unknown[] | null;
	}>;
	created_at: string;
	modified_at: string;
}

/* ---------- invocations ---------- */

export type InvocationStatus = 'success' | 'error' | 'timeout' | 'rate_limited' | 'budget_exceeded';
export type TriggeredBy = 'user' | 'celery' | 'cron' | 'system';

export interface Invocation {
	id: number;
	run_id: string | null;
	session_id: string | null;
	round_number: number | null;
	provider_name: string;
	provider_slug: string;
	model: string;
	agent_name: string;
	input_tokens: number;
	output_tokens: number;
	cost_usd: string;
	latency_ms: number | null;
	triggered_by: TriggeredBy;
	status: InvocationStatus;
	error_type: string | null;
	stop_reason: string | null;
	created_at: string;
}

export interface RunGroup {
	type: 'run';
	run_id: string;
	rounds: Invocation[];
	run_label?: string;
}
export interface StandaloneGroup {
	type: 'standalone';
	inv: Invocation;
}
export interface SessionGroup {
	type: 'session';
	session_id: string;
	runs: Array<RunGroup | StandaloneGroup>;
}
export type InvocationGroup = SessionGroup | RunGroup | StandaloneGroup;

export interface InvocationFile {
	id: number;
	filename: string | null;
	media_type: string | null;
	size_bytes: number | null;
	sha256: string | null;
	source_kind: 'upload' | 'url';
	source_url: string | null;
	url: string | null;
}

export interface InvocationDetail extends Invocation {
	provider: number | null;
	agent: number | null;
	request_messages: unknown[];
	request_system: string | null;
	request_tools: Array<{ name: string; description: string; input_schema: object }> | null;
	request_params: Record<string, unknown>;
	request_files: Array<{
		filename: string | null;
		media_type: string | null;
		size_bytes: number | null;
		source: 'upload' | 'url';
		url?: string;
	}> | null;
	files: InvocationFile[];
	response_content: string | null;
	response_tool_calls: Array<{ id: string; name: string; input: Record<string, unknown> }> | null;
	cache_creation_tokens: number;
	cache_read_tokens: number;
	time_to_first_token_ms: number | null;
	user_id_ref: string | null;
	celery_task_id: string | null;
	error_message: string | null;
	system_prompt_name: string;
	system_prompt_version: number | null;
	user_prompt_name: string;
	user_prompt_version: number | null;
	rendered_system_prompt: string | null;
	context_snapshot: Record<string, unknown> | null;
	modified_at: string;
}

export interface InvocationStats {
	total_runs: number;
	today: number;
	errors_24h: number;
	cost_today: string;
}

export interface InvocationFilters {
	agent_id: string;
	provider_id: string;
	status: string;
	triggered_by: string;
	has_session: string;
	start_date: string;
	end_date: string;
}

/* ---------- keys ---------- */

export const aiKeys = {
	all: (appId: string) => ['app', appId, 'ai'] as const,
	available: (appId: string) => ['app', appId, 'ai', 'available'] as const,
	providers: (appId: string) => ['app', appId, 'ai', 'providers'] as const,
	agents: (appId: string) => ['app', appId, 'ai', 'agents'] as const,
	prompts: (appId: string) => ['app', appId, 'ai', 'prompts'] as const,
	tools: (appId: string) => ['app', appId, 'ai', 'tools'] as const,
	invocations: (appId: string) => ['app', appId, 'ai', 'invocations'] as const,
};

/* ---------- queries ---------- */

export function useAvailableProviders(appId: string) {
	return useQuery({
		queryKey: aiKeys.available(appId),
		queryFn: () =>
			api<{ providers: AvailableProvider[] }>(`${base(appId)}/providers/available/`).then(
				(r) => r.providers,
			),
		staleTime: Infinity,
	});
}

export function useProviders(appId: string) {
	return useQuery({
		queryKey: aiKeys.providers(appId),
		queryFn: () =>
			api<{ providers: Paginated<Provider> }>(`${base(appId)}/providers/?page_size=100`).then(
				(r) => r.providers.records,
			),
	});
}

export interface AgentListParams {
	page: number;
	pageSize: number;
	search: string;
	status: '' | 'active' | 'disabled';
}

export function useAgentList(appId: string, p: AgentListParams) {
	return useQuery({
		queryKey: [...aiKeys.agents(appId), 'list', p],
		queryFn: () =>
			api<{
				agents: Paginated<Agent>;
				stats: { total_agents: number; active_agents: number };
			}>(
				`${base(appId)}/agents/?${buildQuery({
					page: p.page,
					page_size: p.pageSize,
					search: p.search,
					status: p.status,
				})}`,
			),
		placeholderData: keepPreviousData,
	});
}

/** Every agent, for pickers and filters. */
export function useAgents(appId: string) {
	return useQuery({
		queryKey: [...aiKeys.agents(appId), 'all'],
		queryFn: () =>
			api<{ agents: Paginated<Agent> }>(`${base(appId)}/agents/?page=1&page_size=100`).then(
				(r) => r.agents.records,
			),
	});
}

export function useAgent(appId: string, id: number | null) {
	return useQuery({
		queryKey: [...aiKeys.agents(appId), 'one', id],
		queryFn: () => api<{ agent: Agent }>(`${base(appId)}/agents/${id}/`).then((r) => r.agent),
		enabled: id != null,
	});
}

export function useSessions(appId: string, agentId: number) {
	return useQuery({
		queryKey: [...aiKeys.agents(appId), 'sessions', agentId],
		queryFn: () =>
			api<{ sessions: Paginated<MemorySession> }>(
				`${base(appId)}/agents/${agentId}/sessions/?page_size=100`,
			).then((r) => r.sessions.records),
	});
}

export function useSession(appId: string, agentId: number, sessionId: string | null) {
	return useQuery({
		queryKey: [...aiKeys.agents(appId), 'session', agentId, sessionId],
		queryFn: () =>
			api<{ session: MemorySession & { messages: MemoryMessage[] } }>(
				`${base(appId)}/agents/${agentId}/sessions/${encodeURIComponent(sessionId!)}/`,
			).then((r) => r.session),
		enabled: sessionId != null,
	});
}

export interface PromptListParams {
	page: number;
	pageSize: number;
	search: string;
	type: '' | PromptType;
	includeInactive: boolean;
}

export function usePromptList(appId: string, p: PromptListParams) {
	return useQuery({
		queryKey: [...aiKeys.prompts(appId), 'list', p],
		queryFn: () =>
			api<{ prompts: Paginated<Prompt>; stats: PromptStats }>(
				`${base(appId)}/prompts/?${buildQuery({
					page: p.page,
					page_size: p.pageSize,
					search: p.search,
					type: p.type,
					include_inactive: p.includeInactive ? 'true' : '',
				})}`,
			),
		placeholderData: keepPreviousData,
	});
}

/** Active prompts of one type, for the agent form's pickers. */
export function usePromptOptions(appId: string, type: PromptType) {
	return useQuery({
		queryKey: [...aiKeys.prompts(appId), 'options', type],
		queryFn: () =>
			api<{ prompts: Paginated<Prompt> }>(
				`${base(appId)}/prompts/?type=${type}&page_size=100`,
			).then((r) => r.prompts.records),
	});
}

export function usePromptCompare(appId: string, promptId: number, v1: number, v2: number) {
	return useQuery({
		queryKey: [...aiKeys.prompts(appId), 'compare', promptId, v1, v2],
		queryFn: () =>
			api<{ version_1: PromptVersion; version_2: PromptVersion }>(
				`${base(appId)}/prompts/${promptId}/compare/?v1=${v1}&v2=${v2}`,
			),
		enabled: v1 > 0 && v2 > 0 && v1 !== v2,
	});
}

export interface ToolListParams {
	search: string;
	section: string;
	safety: '' | ToolSafety;
	isActive: '' | 'true' | 'false';
}

export function useTools(appId: string, p: ToolListParams) {
	return useQuery({
		queryKey: [...aiKeys.tools(appId), 'list', p],
		queryFn: () =>
			api<{ tools: Paginated<Tool>; stats: { active_tools: number; sections: number } }>(
				`${base(appId)}/tools/?${buildQuery({
					page_size: 100,
					search: p.search,
					section: p.section,
					safety: p.safety,
					is_active: p.isActive,
				})}`,
			),
		placeholderData: keepPreviousData,
	});
}

export function useToolSections(appId: string) {
	return useQuery({
		queryKey: [...aiKeys.tools(appId), 'sections'],
		queryFn: () =>
			api<{ sections: Array<{ section: string; count: number; active_count: number }> }>(
				`${base(appId)}/tools/sections/`,
			).then((r) => r.sections),
	});
}

export function useTool(appId: string, id: number | null) {
	return useQuery({
		queryKey: [...aiKeys.tools(appId), 'one', id],
		queryFn: () => api<{ tool: ToolDetail }>(`${base(appId)}/tools/${id}/`).then((r) => r.tool),
		enabled: id != null,
	});
}

export function useInvocationStats(appId: string) {
	return useQuery({
		queryKey: [...aiKeys.invocations(appId), 'stats'],
		queryFn: () => api<InvocationStats>(`${base(appId)}/invocations/stats/`),
	});
}

export function useInvocations(
	appId: string,
	p: InvocationFilters & { page: number; pageSize: number },
) {
	return useQuery({
		queryKey: [...aiKeys.invocations(appId), 'list', p],
		queryFn: () =>
			api<{
				invocations: { records: InvocationGroup[]; total_pages: number; total_records: number };
			}>(
				`${base(appId)}/invocations/?${buildQuery({
					page: p.page,
					page_size: p.pageSize,
					agent_id: p.agent_id,
					provider_id: p.provider_id,
					status: p.status,
					triggered_by: p.triggered_by,
					has_session: p.has_session,
					start_date: p.start_date,
					end_date: p.end_date,
				})}`,
			).then((r) => r.invocations),
		placeholderData: keepPreviousData,
	});
}

export function useInvocation(appId: string, id: number | null) {
	return useQuery({
		queryKey: [...aiKeys.invocations(appId), 'one', id],
		queryFn: () =>
			api<{ invocation: InvocationDetail }>(`${base(appId)}/invocations/${id}/`).then(
				(r) => r.invocation,
			),
		enabled: id != null,
		staleTime: Infinity,
	});
}

/* ---------- plain calls (for forms that manage their own flow) ---------- */

export const fetchModels = (appId: string, provider_slug: string, config: Record<string, unknown>) =>
	api<{ models: ProviderModelInfo[] }>(`${base(appId)}/providers/fetch-models/`, 'POST', {
		provider_slug,
		config,
	}).then((r) => r.models);

export const createProvider = (appId: string, body: ProviderInput) =>
	api<{ provider_id: number }>(`${base(appId)}/providers/`, 'POST', body);

export const updateProvider = (appId: string, id: number, body: Partial<ProviderInput>) =>
	api<{ provider: Provider }>(`${base(appId)}/providers/${id}/`, 'PUT', body);

export const createAgent = (appId: string, body: AgentInput) =>
	api<{ agent_id: number }>(`${base(appId)}/agents/`, 'POST', body);

export const updateAgent = (appId: string, id: number, body: Partial<AgentInput>) =>
	api<{ agent: Agent }>(`${base(appId)}/agents/${id}/`, 'PUT', body);

export const createPrompt = (
	appId: string,
	body: {
		name: string;
		description: string;
		type: PromptType;
		content: string;
		change_description: string;
	},
) => api<{ prompt_id: number }>(`${base(appId)}/prompts/`, 'POST', body);

/** Multipart only when files are attached; the server reads JSON-string variables from form data. */
export function testAgent(appId: string, id: number, input: AgentTestInput) {
	const url = `${base(appId)}/agents/${id}/test/`;
	const fields: Record<string, unknown> = {};
	if (Object.keys(input.variables).length) fields.variables = input.variables;
	if (Object.keys(input.system_variables).length) fields.system_variables = input.system_variables;
	if (input.user_message) fields.user_message = input.user_message;
	if (!input.files.length) {
		return api<{ result: AgentTestResult }>(url, 'POST', fields).then((r) => r.result);
	}
	const fd = new FormData();
	for (const [k, v] of Object.entries(fields)) {
		fd.append(k, typeof v === 'string' ? v : JSON.stringify(v));
	}
	for (const f of input.files) fd.append('files', f);
	return api<{ result: AgentTestResult }>(url, 'POST', fd).then((r) => r.result);
}

/* ---------- mutations ---------- */

export function useToggleProvider(appId: string) {
	return useApiMutation({
		fn: (p: { id: number; is_enabled: boolean }) =>
			api(`${base(appId)}/providers/${p.id}/toggle/`, 'POST', { is_enabled: p.is_enabled }),
		invalidate: [aiKeys.providers(appId)],
		success: (_r, p) => (p.is_enabled ? 'Provider enabled' : 'Provider disabled'),
	});
}

export function useValidateProvider(appId: string) {
	return useApiMutation({
		fn: (p: { id: number }) => api(`${base(appId)}/providers/${p.id}/validate/`, 'POST', {}),
		invalidate: [aiKeys.providers(appId)],
		success: 'Credentials are valid',
	});
}

export function useDeleteProvider(appId: string) {
	return useApiMutation({
		fn: (p: { id: number }) =>
			api<{ message: string }>(`${base(appId)}/providers/${p.id}/`, 'DELETE'),
		invalidate: [aiKeys.providers(appId)],
		success: (r) => r.message,
	});
}

export function useToggleProviderModel(appId: string) {
	return useApiMutation({
		fn: (p: { providerId: number; modelPk: number; is_enabled: boolean }) =>
			api(`${base(appId)}/providers/${p.providerId}/models/${p.modelPk}/toggle/`, 'POST', {
				is_enabled: p.is_enabled,
			}),
		invalidate: [aiKeys.providers(appId)],
	});
}

export function useToggleAgent(appId: string) {
	return useApiMutation({
		fn: (a: { id: number; is_enabled: boolean }) =>
			api(`${base(appId)}/agents/${a.id}/toggle/`, 'POST', { is_enabled: a.is_enabled }),
		invalidate: [aiKeys.agents(appId)],
		success: (_r, a) => (a.is_enabled ? 'Agent enabled' : 'Agent disabled'),
	});
}

export function useDuplicateAgent(appId: string) {
	return useApiMutation({
		fn: (a: { id: number }) =>
			api<{ message: string; agent: Agent }>(`${base(appId)}/agents/${a.id}/duplicate/`, 'POST'),
		invalidate: [aiKeys.agents(appId)],
		success: (r) => `${r.message}. The copy starts disabled.`,
	});
}

export function useDeleteAgent(appId: string) {
	return useApiMutation({
		fn: (a: { id: number }) => api<{ message: string }>(`${base(appId)}/agents/${a.id}/`, 'DELETE'),
		invalidate: [aiKeys.agents(appId)],
		success: (r) => r.message,
	});
}

export function useClearSession(appId: string, agentId: number) {
	return useApiMutation({
		fn: (s: { sessionId: string }) =>
			api(
				`${base(appId)}/agents/${agentId}/sessions/${encodeURIComponent(s.sessionId)}/`,
				'DELETE',
			),
		invalidate: [aiKeys.agents(appId)],
		success: 'Session cleared',
	});
}

export function useUpdatePrompt(appId: string) {
	return useApiMutation({
		fn: (p: { id: number; name: string; description: string; type: PromptType }) =>
			api(`${base(appId)}/prompts/${p.id}/`, 'PUT', {
				name: p.name,
				description: p.description,
				type: p.type,
			}),
		invalidate: [aiKeys.prompts(appId), aiKeys.agents(appId)],
		success: 'Prompt updated',
	});
}

export function useDeletePrompt(appId: string) {
	return useApiMutation({
		fn: (p: { id: number }) =>
			api<{ message: string }>(`${base(appId)}/prompts/${p.id}/`, 'DELETE'),
		invalidate: [aiKeys.prompts(appId)],
		success: (r) => r.message,
	});
}

export function useActivatePrompt(appId: string) {
	return useApiMutation({
		fn: (p: { id: number }) => api(`${base(appId)}/prompts/${p.id}/activate/`, 'POST'),
		invalidate: [aiKeys.prompts(appId)],
		success: 'Prompt activated',
	});
}

export function useCreateVersion(appId: string) {
	return useApiMutation({
		fn: (p: { id: number; content: string; change_description: string }) =>
			api<{ message: string; version: PromptVersion }>(
				`${base(appId)}/prompts/${p.id}/versions/`,
				'POST',
				{ content: p.content, change_description: p.change_description },
			),
		invalidate: [aiKeys.prompts(appId)],
		success: (r) => `${r.message} as a draft. Make it live from the version history.`,
	});
}

export function usePromoteVersion(appId: string) {
	return useApiMutation({
		fn: (p: { promptId: number; versionId: number }) =>
			api<{ message: string }>(
				`${base(appId)}/prompts/${p.promptId}/versions/${p.versionId}/promote/`,
				'POST',
			),
		invalidate: [aiKeys.prompts(appId), aiKeys.agents(appId)],
		success: (r) => r.message,
	});
}

export function useSyncTools(appId: string) {
	return useApiMutation({
		fn: () =>
			api<{ stats: { created: number; updated: number; deactivated: number } }>(
				`${base(appId)}/tools/sync/`,
				'POST',
			),
		invalidate: [aiKeys.tools(appId)],
		success: (r) =>
			`Tools synced: ${r.stats.created} new, ${r.stats.updated} updated, ${r.stats.deactivated} removed`,
	});
}

/* ---------- formatting ---------- */

export const money = (v: string | number | null | undefined, digits = 2) => {
	const n = Number(v);
	return v == null || v === '' || Number.isNaN(n) ? '—' : `$${n.toFixed(digits)}`;
};

/** `{{name}}` slots in order of first appearance. */
export function templateVars(content: string): string[] {
	return [...new Set([...content.matchAll(/\{\{(\w+)\}\}/g)].map((m) => m[1]))];
}
