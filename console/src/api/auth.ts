import { useQuery } from '@tanstack/react-query';
import { api } from './client';
import { appKeys } from './apps';

/**
 * App auth_config (apps/shared/tenancy/schema.py AuthConfigSchema). Stored configs also carry
 * keys written by the classic UI (e.g. `login_methods.allowed_usernames`,
 * `two_factor_auth.allowedMethods`); the backend reads the canonical ones typed here. Unknown
 * keys are kept untouched on save, so the index signatures stay open.
 */
export interface AuthConfig {
	login_methods?: {
		password?: {
			enabled?: boolean;
			allowed_usernames?: Array<'email' | 'phone'>;
			forgot_password_enabled?: boolean;
			password_reset_link_expiry_hours?: number;
			[key: string]: unknown;
		};
		otp?: {
			enabled?: boolean;
			allowed_methods?: Array<'email' | 'sms'>;
			otp_expiry?: number;
			[key: string]: unknown;
		};
		sso?: { enabled?: boolean; [key: string]: unknown };
		oidc?: { enabled?: boolean; [key: string]: unknown };
		allowed_usernames?: Array<'email' | 'phone'>;
		[key: string]: unknown;
	};
	two_factor_auth?: {
		required?: boolean;
		allowed_methods?: Array<'email' | 'sms' | 'totp'>;
		allowedMethods?: Array<'email' | 'sms' | 'totp'>;
		[key: string]: unknown;
	};
	session_policy?: {
		max_concurrent_sessions?: number;
		token_ttl?: number;
		session_warn_after?: number;
		session_expire_after?: number;
		force_logout_on_password_change?: boolean;
		/** Read-only platform defaults injected by the serializer. */
		platform_token_ttl?: number;
		platform_session_warn_after?: number;
		platform_session_expire_after?: number;
		[key: string]: unknown;
	};
	password_policy?: {
		min_length?: number;
		require_uppercase?: boolean;
		require_lowercase?: boolean;
		require_numbers?: boolean;
		require_special_chars?: boolean;
		password_history_count?: number;
		password_expiry_days?: number;
		allow_change?: boolean;
		[key: string]: unknown;
	};
	[key: string]: unknown;
}

export function useAuthConfig(app: string) {
	return useQuery({
		// Same cache entry as useApp(): both read the app detail endpoint.
		queryKey: appKeys.detail(app),
		queryFn: () =>
			api<{ app: { name: string; auth_config: AuthConfig } }>(`/api/v1/apps/${app}/`).then(
				(r) => r.app,
			),
		select: (a) => ({
			name: a.name,
			authConfig: (a as { auth_config?: AuthConfig }).auth_config ?? {},
		}),
	});
}

/** auth_config is replaced wholesale, so pass the complete merged config. */
export const saveAuthConfig = (app: string, authConfig: AuthConfig) =>
	api<{ message: string }>(`/api/v1/apps/${app}/`, 'PUT', { auth_config: authConfig });

// SAMLModel (apps/appauth/models.py).
export interface SamlProvider {
	id: number;
	label: string;
	is_active: boolean;
	is_strict: boolean;
	is_debug_true: boolean;
	idp_entityId: string;
	idp_sso: string;
	idp_slo: string;
	idp_x509cert: string;
	sp_entityId: string;
	sp_acsURL: string;
	sp_slo: string;
	sp_x509cert: string;
	sp_privatekey: string;
	security_signatureAlgorithm: string;
	security_digestAlgorithm: string;
	security_requestedAuthnContextComparison: string;
	name_id_format: string;
	[flag: `security_${string}`]: boolean | string;
}

export type SamlInput = Omit<SamlProvider, 'id'>;

export const samlKeys = {
	list: (app: string) => ['apps', app, 'saml-providers'] as const,
};

export function useSamlProviders(app: string) {
	return useQuery({
		queryKey: samlKeys.list(app),
		queryFn: () =>
			api<{ saml_providers: SamlProvider[] }>(`/api/v1/apps/${app}/saml-providers/`).then(
				(r) => r.saml_providers,
			),
	});
}

export const createSamlProvider = (app: string, body: Partial<SamlInput>) =>
	api<{ saml_provider: SamlProvider }>(`/api/v1/apps/${app}/saml-providers/`, 'POST', body);

export const updateSamlProvider = (app: string, id: number, body: Partial<SamlInput>) =>
	api<{ saml_provider: SamlProvider }>(`/api/v1/apps/${app}/saml-providers/${id}/`, 'PUT', body);

export const deleteSamlProvider = (app: string, id: number) =>
	api<{ message: string }>(`/api/v1/apps/${app}/saml-providers/${id}/`, 'DELETE');
