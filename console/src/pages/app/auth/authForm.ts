import type { AuthConfig } from '@/api/auth';

/** Editable view of AuthConfig. Blank session fields mean "inherit the platform default". */
export interface AuthForm {
	password: boolean;
	usernames: Array<'email' | 'phone'>;
	forgotPassword: boolean;
	resetLinkHours: string;
	otp: boolean;
	otpMethods: Array<'email' | 'sms'>;
	otpExpiry: string;
	sso: boolean;
	oidc: boolean;
	twoFa: boolean;
	twoFaMethods: Array<'email' | 'sms' | 'totp'>;
	maxSessions: string;
	tokenTtl: string;
	warnAfter: string;
	expireAfter: string;
	logoutOnPasswordChange: boolean;
	minLength: string;
	requireUppercase: boolean;
	requireLowercase: boolean;
	requireNumbers: boolean;
	requireSpecial: boolean;
	expiryDays: string;
	historyCount: string;
	allowChange: boolean;
}

const str = (n: number | undefined | null) => (n === undefined || n === null ? '' : String(n));

export function toForm(c: AuthConfig): AuthForm {
	const lm = c.login_methods ?? {};
	const pp = c.password_policy ?? {};
	const sp = c.session_policy ?? {};
	const tfa = c.two_factor_auth ?? {};
	return {
		password: lm.password?.enabled ?? true,
		// The backend reads login_methods.password.allowed_usernames; the classic setup
		// wizard wrote login_methods.allowed_usernames, so fall back to it.
		usernames: lm.password?.allowed_usernames ?? lm.allowed_usernames ?? ['email', 'phone'],
		forgotPassword: lm.password?.forgot_password_enabled ?? false,
		resetLinkHours: str(lm.password?.password_reset_link_expiry_hours ?? 24),
		otp: lm.otp?.enabled ?? false,
		otpMethods: lm.otp?.allowed_methods ?? [],
		otpExpiry: str(lm.otp?.otp_expiry ?? 300),
		sso: lm.sso?.enabled ?? false,
		oidc: lm.oidc?.enabled ?? false,
		twoFa: tfa.required ?? false,
		// Same story: the backend reads allowed_methods; older configs stored allowedMethods.
		twoFaMethods: tfa.allowed_methods ?? tfa.allowedMethods ?? [],
		maxSessions: str(sp.max_concurrent_sessions ?? 0),
		tokenTtl: str(sp.token_ttl),
		warnAfter: str(sp.session_warn_after),
		expireAfter: str(sp.session_expire_after),
		logoutOnPasswordChange: sp.force_logout_on_password_change ?? false,
		minLength: str(pp.min_length ?? 8),
		requireUppercase: pp.require_uppercase ?? true,
		requireLowercase: pp.require_lowercase ?? true,
		requireNumbers: pp.require_numbers ?? true,
		requireSpecial: pp.require_special_chars ?? false,
		expiryDays: str(pp.password_expiry_days ?? 90),
		historyCount: str(pp.password_history_count ?? 3),
		allowChange: pp.allow_change ?? true,
	};
}

type Errors = Partial<Record<keyof AuthForm | 'methods', string>>;

const int = (s: string) => (/^\d+$/.test(s.trim()) ? Number(s.trim()) : NaN);

function range(
	e: Errors,
	key: keyof AuthForm,
	v: string,
	min: number,
	max: number,
	{ optional = false } = {},
) {
	if (optional && v.trim() === '') return;
	const n = int(v);
	if (Number.isNaN(n) || n < min || n > max) e[key] = `Enter a whole number from ${min} to ${max}`;
}

export function validate(f: AuthForm, platform: { warn?: number; expire?: number }): Errors {
	const e: Errors = {};
	if (!f.password && !f.otp && !f.sso && !f.oidc) e.methods = 'Turn on at least one sign-in method';
	if (f.password && f.usernames.length === 0) e.usernames = 'Pick at least one';
	if (f.otp && f.otpMethods.length === 0) e.otpMethods = 'Pick at least one';
	if (f.twoFa && f.twoFaMethods.length === 0) e.twoFaMethods = 'Pick at least one';
	if (f.password && f.forgotPassword) range(e, 'resetLinkHours', f.resetLinkHours, 1, 720);
	if (f.otp) range(e, 'otpExpiry', f.otpExpiry, 30, 3600);
	range(e, 'maxSessions', f.maxSessions, 0, 1000);
	range(e, 'tokenTtl', f.tokenTtl, 0, 31_536_000, { optional: true });
	range(e, 'warnAfter', f.warnAfter, 60, 604_800, { optional: true });
	range(e, 'expireAfter', f.expireAfter, 60, 604_800, { optional: true });
	const warn = f.warnAfter.trim() ? int(f.warnAfter) : platform.warn;
	const expire = f.expireAfter.trim() ? int(f.expireAfter) : platform.expire;
	if (
		!e.warnAfter &&
		!e.expireAfter &&
		warn !== undefined &&
		expire !== undefined &&
		warn >= expire
	) {
		e.warnAfter = f.warnAfter.trim()
			? 'The warning must come before sign-out'
			: `The platform default warns after ${humanSeconds(warn)}; set a warning shorter than the sign-out time`;
	}
	range(e, 'minLength', f.minLength, 4, 128);
	range(e, 'expiryDays', f.expiryDays, 1, 365);
	range(e, 'historyCount', f.historyCount, 0, 24);
	return e;
}

/**
 * Apply the form onto the stored config. auth_config is replaced wholesale on save, so keys
 * this screen doesn't edit (reset/OTP message templates, role_overrides, ...) are carried over.
 */
export function applyForm(stored: AuthConfig, f: AuthForm): AuthConfig {
	const c = structuredClone(stored);
	const lm = (c.login_methods ??= {});
	lm.password = {
		...lm.password,
		enabled: f.password,
		allowed_usernames: f.usernames,
		forgot_password_enabled: f.forgotPassword,
		password_reset_link_expiry_hours: int(f.resetLinkHours) || 24,
	};
	if (lm.allowed_usernames) lm.allowed_usernames = f.usernames;
	lm.otp = {
		...lm.otp,
		enabled: f.otp,
		allowed_methods: f.otpMethods,
		otp_expiry: int(f.otpExpiry) || 300,
	};
	lm.sso = { ...lm.sso, enabled: f.sso };
	lm.oidc = { ...lm.oidc, enabled: f.oidc };

	c.two_factor_auth = { ...c.two_factor_auth, required: f.twoFa, allowed_methods: f.twoFaMethods };
	if (c.two_factor_auth.allowedMethods) c.two_factor_auth.allowedMethods = f.twoFaMethods;

	const sp: NonNullable<AuthConfig['session_policy']> = { ...c.session_policy };
	for (const k of Object.keys(sp)) if (k.startsWith('platform_')) delete sp[k];
	sp.max_concurrent_sessions = int(f.maxSessions) || 0;
	sp.force_logout_on_password_change = f.logoutOnPasswordChange;
	const optional: Array<[keyof typeof sp, string]> = [
		['token_ttl', f.tokenTtl],
		['session_warn_after', f.warnAfter],
		['session_expire_after', f.expireAfter],
	];
	for (const [k, v] of optional) {
		if (v.trim() === '') delete sp[k];
		else sp[k] = int(v);
	}
	c.session_policy = sp;

	c.password_policy = {
		...c.password_policy,
		min_length: int(f.minLength),
		require_uppercase: f.requireUppercase,
		require_lowercase: f.requireLowercase,
		require_numbers: f.requireNumbers,
		require_special_chars: f.requireSpecial,
		password_expiry_days: int(f.expiryDays),
		password_history_count: int(f.historyCount),
		allow_change: f.allowChange,
	};
	return c;
}

/** "30 min", "24 h", "1 h 30 min". */
export function humanSeconds(s: number | undefined): string {
	if (s === undefined || Number.isNaN(s)) return '';
	if (s === 0) return 'never';
	const h = Math.floor(s / 3600);
	const m = Math.floor((s % 3600) / 60);
	const sec = s % 60;
	return [h && `${h} h`, m && `${m} min`, sec && `${sec} s`].filter(Boolean).join(' ') || '0 s';
}
