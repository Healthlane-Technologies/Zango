import { useQuery } from '@tanstack/react-query';
import { api } from './client';

const BASE = '/api/v1/platform/agent-mode';

// Writable fields (agent_mode_admin/v1/views.py `_WRITABLE`). Numbers travel as strings
// from inputs; the view treats blank as "unset".
export interface AgentModeForm {
	is_enabled: boolean;
	ensure_packages: boolean;
	allow_frontend_build: boolean;
	default_model: string;
	default_effort: string;
	max_run_seconds: string;
	max_budget_usd: string;
	max_turns: string;
	analyst_model: string;
	analyst_effort: string;
	analyst_budget_usd: string;
	analyst_max_turns: string;
	monthly_budget_usd: string;
}

type Stored = {
	[K in keyof AgentModeForm]: AgentModeForm[K] extends boolean ? boolean : string | number | null;
};

export interface AgentModeSettings {
	configured: boolean;
	/** 'platform_settings' when a stored row overrides the environment. */
	source: string;
	has_api_key: boolean;
	/** Server-masked; never the key itself. */
	masked_config: { api_key?: string };
	environment: { node_available: boolean; env_api_key_present: boolean };
	resolved: {
		enabled: boolean;
		model: string;
		effort: string;
		max_run_seconds: number | null;
		max_turns: number | null;
		max_budget_usd: number | null;
		analyst_model: string;
		analyst_effort: string;
		analyst_max_turns: number | null;
		analyst_budget_usd: number | null;
		allow_frontend_build: boolean;
		ensure_packages: boolean;
	};
	settings: (Stored & { provider?: string }) | null;
	is_validated: boolean;
	last_validated_at: string | null;
}

export const agentModeSettingsKey = ['platform-settings', 'agent-mode'] as const;

export function useAgentModeSettings() {
	return useQuery({
		queryKey: agentModeSettingsKey,
		queryFn: () => api<AgentModeSettings>(`${BASE}/settings/`),
	});
}

/** `api_key` is optional: omitting it keeps the stored key. */
export function saveAgentModeSettings(form: AgentModeForm & { api_key?: string }) {
	return api<AgentModeSettings>(`${BASE}/settings/`, 'POST', form);
}

/** One-token call to the model. `valid: false` comes back as a success with a message. */
export function validateAgentModeKey() {
	return api<{ valid: boolean; message: string; model?: string }>(
		`${BASE}/settings/validate/`,
		'POST',
		{},
	);
}
