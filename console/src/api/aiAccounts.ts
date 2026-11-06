import { useQuery } from '@tanstack/react-query';
import type { AvailableProvider, ProviderModelInfo } from './ai';
import { api } from './client';

// Platform AI accounts (api/platform/ai_accounts): AI service credentials set up once
// for every app. Apps link to an account instead of holding a key.

const BASE = '/api/v1/platform/ai-accounts';

export type AiAccountStatus = 'connected' | 'failing' | 'off';

export interface AiAccountApp {
	uuid: string;
	name: string;
	/** The app's AI accounts that use this platform account. */
	providers: string[];
}

export interface AiAccount {
	uuid: string;
	name: string;
	description: string;
	provider_slug: string;
	service_name: string;
	default_model: string;
	models: ProviderModelInfo[];
	app_monthly_budget_usd: number | null;
	is_default: boolean;
	is_enabled: boolean;
	is_validated: boolean;
	status: AiAccountStatus;
	last_validated_at: string | null;
	validation_error: string;
	/** Saved config with secrets masked. */
	masked_config: Record<string, unknown>;
	created_at: string;
	modified_at: string;
	apps?: AiAccountApp[];
}

export interface AiAccountInput {
	name: string;
	description?: string;
	provider_slug: string;
	config: Record<string, unknown>;
	default_model: string;
	model_ids: string[];
	app_monthly_budget_usd: number | null;
	is_default: boolean;
}

export type AiAccountPatch = Partial<
	Omit<AiAccountInput, 'provider_slug' | 'config'> & {
		is_enabled: boolean;
		config: Record<string, unknown>;
		/** The list the form loaded, so newly ticked models can be kept. */
		models: ProviderModelInfo[];
	}
>;

export const aiAccountKeys = {
	all: ['platform', 'ai-accounts'] as const,
};

export function useAiAccounts() {
	return useQuery({
		queryKey: aiAccountKeys.all,
		queryFn: () => api<{ accounts: AiAccount[]; services: AvailableProvider[] }>(`${BASE}/`),
	});
}

export function checkAiAccount(body: {
	provider_slug: string;
	config: Record<string, unknown>;
	account_uuid?: string;
	default_model?: string;
}) {
	return api<{ models: ProviderModelInfo[] }>(`${BASE}/check/`, 'POST', body).then((r) => r.models);
}

export function createAiAccount(body: AiAccountInput) {
	return api<{ account: AiAccount; message: string }>(`${BASE}/`, 'POST', body);
}

export function updateAiAccount(uuid: string, body: AiAccountPatch) {
	return api<{ account: AiAccount; message: string }>(`${BASE}/${uuid}/`, 'PUT', body);
}

export function deleteAiAccount(uuid: string) {
	return api<{ message: string }>(`${BASE}/${uuid}/`, 'DELETE');
}

export function validateAiAccount(uuid: string) {
	return api<{ account: AiAccount; message: string }>(`${BASE}/${uuid}/validate/`, 'POST');
}

/** The apps in a 409 ACCOUNT_IN_USE refusal. */
export function inUseApps(err: unknown): AiAccountApp[] | null {
	const body = (err as { body?: { response?: { error_code?: string; apps?: AiAccountApp[] } } })
		?.body;
	return body?.response?.error_code === 'ACCOUNT_IN_USE' ? (body.response.apps ?? []) : null;
}
