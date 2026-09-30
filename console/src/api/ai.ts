import { useQuery } from '@tanstack/react-query';
import { api } from './client';
import { useApiMutation } from './hooks';
import type { Paginated } from './secrets';

// AppLLMProviderListSerializer, trimmed.
export interface Provider {
	id: number;
	name: string;
	description: string;
	provider_slug: string;
	default_model: string | null;
	is_enabled: boolean;
	is_validated: boolean;
	validation_error: string | null;
	status: string;
	models_count: number;
	current_month_spend_usd: string | number | null;
	monthly_budget_usd: string | number | null;
	total_invocations: number;
}

// AgentListSerializer, trimmed.
export interface Agent {
	id: number;
	name: string;
	description: string;
	provider_name: string | null;
	model: string | null;
	is_enabled: boolean;
	total_invocations: number;
	total_cost_usd: string | number | null;
	session_count: number;
}

const aiKeys = {
	providers: (appId: string) => ['app', appId, 'ai', 'providers'] as const,
	agents: (appId: string) => ['app', appId, 'ai', 'agents'] as const,
};

export function useProviders(appId: string) {
	return useQuery({
		queryKey: aiKeys.providers(appId),
		queryFn: () =>
			api<{ providers: Paginated<Provider> }>(
				`/api/v1/apps/${appId}/ai/providers/?page_size=100`,
			).then((r) => r.providers.records),
	});
}

export function useAgents(appId: string) {
	return useQuery({
		queryKey: aiKeys.agents(appId),
		queryFn: () =>
			api<{ agents: Paginated<Agent> }>(
				`/api/v1/apps/${appId}/ai/agents/?page=1&page_size=100`,
			).then((r) => r.agents.records),
	});
}

// Toggle endpoints read `is_enabled` with bool(), so it must be a JSON boolean, not form data.
export function useToggleProvider(appId: string) {
	return useApiMutation({
		fn: (p: { id: number; is_enabled: boolean }) =>
			api(`/api/v1/apps/${appId}/ai/providers/${p.id}/toggle/`, 'POST', {
				is_enabled: p.is_enabled,
			}),
		invalidate: [aiKeys.providers(appId)],
		success: (_r, p) => (p.is_enabled ? 'Provider enabled' : 'Provider disabled'),
	});
}

export function useValidateProvider(appId: string) {
	return useApiMutation({
		fn: (p: { id: number }) =>
			api(`/api/v1/apps/${appId}/ai/providers/${p.id}/validate/`, 'POST', {}),
		invalidate: [aiKeys.providers(appId)],
		success: 'Credentials validated',
	});
}

export function useToggleAgent(appId: string) {
	return useApiMutation({
		fn: (a: { id: number; is_enabled: boolean }) =>
			api(`/api/v1/apps/${appId}/ai/agents/${a.id}/toggle/`, 'POST', { is_enabled: a.is_enabled }),
		invalidate: [aiKeys.agents(appId)],
		success: (_r, a) => (a.is_enabled ? 'Agent enabled' : 'Agent disabled'),
	});
}
