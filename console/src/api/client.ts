// Thin fetch wrapper for the platform API. Every endpoint returns
// `{ success, response }` (zango.core.api.utils.get_api_response); callers get `response`.

declare global {
	interface Window {
		csrf_token?: string;
		platform_version?: string;
	}
}

export class ApiError extends Error {
	constructor(
		public status: number,
		public body: unknown,
	) {
		super(messageOf(body) ?? `Request failed (${status})`);
	}
}

type Method = 'GET' | 'POST' | 'PUT' | 'DELETE';

function csrfToken(): string {
	// The Django template injects the token; the Vite dev server has no template, so fall back to the cookie.
	if (window.csrf_token) return window.csrf_token;
	const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
	return match ? decodeURIComponent(match[1]) : '';
}

/** Flatten DRF-style `{ field: [msg] }` errors into one line. */
function flatten(value: unknown): string | undefined {
	if (typeof value === 'string') return value || undefined;
	if (Array.isArray(value)) return value.map(flatten).filter(Boolean).join(' ') || undefined;
	if (value && typeof value === 'object') {
		const parts = Object.entries(value as Record<string, unknown>)
			.map(([field, v]) => {
				const text = flatten(v);
				return text && (field === 'non_field_errors' ? text : `${field}: ${text}`);
			})
			.filter(Boolean);
		return parts.join('; ') || undefined;
	}
	return undefined;
}

function messageOf(body: unknown): string | undefined {
	if (!body || typeof body !== 'object') return undefined;
	const b = body as {
		response?: { message?: unknown; errors?: unknown };
		detail?: unknown;
		message?: unknown;
	};
	return (
		flatten(b.response?.message) ??
		flatten(b.response?.errors) ??
		flatten(b.detail) ??
		flatten(b.message)
	);
}

function isNotAuthenticated(status: number, body: unknown): boolean {
	// DRF answers anonymous requests with 403 "Authentication credentials were not provided."
	if (status === 401) return true;
	return status === 403 && /credentials were not provided/i.test(messageOf(body) ?? '');
}

export function redirectToLogin(): void {
	const next = window.location.pathname + window.location.search;
	window.location.assign(`/auth/login/?next=${encodeURIComponent(next)}`);
}

export async function api<T>(path: string, method: Method = 'GET', body?: unknown): Promise<T> {
	const headers: Record<string, string> = { 'X-CSRFToken': csrfToken() };
	const isForm = body instanceof FormData;
	if (body !== undefined && !isForm) headers['Content-Type'] = 'application/json';

	const res = await fetch(path, {
		method,
		headers,
		credentials: 'same-origin',
		body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
	});

	const text = await res.text();
	let data: unknown = text;
	try {
		data = text ? JSON.parse(text) : null;
	} catch {
		// Non-JSON (e.g. an HTML error page); keep the raw text for the error.
	}

	if (isNotAuthenticated(res.status, data)) {
		redirectToLogin();
		throw new ApiError(res.status, data);
	}
	if (!res.ok || (data as { success?: boolean })?.success === false) {
		throw new ApiError(res.status, data);
	}
	return (data as { response: T }).response;
}
