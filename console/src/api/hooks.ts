import { useMutation, useQueryClient, type QueryKey } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import { toast } from '@/ui';

/** The current app's uuid. Only valid under /apps/:appId. */
export function useAppId(): string {
	const { appId } = useParams();
	if (!appId) throw new Error('useAppId used outside an app route');
	return appId;
}

interface ApiMutationOptions<TVars, TResult> {
	fn: (vars: TVars) => Promise<TResult>;
	/** Queries to refetch on success. */
	invalidate?: QueryKey[];
	/** Toast on success; a function receives the result and variables. */
	success?: string | ((result: TResult, vars: TVars) => string);
	onSuccess?: (result: TResult, vars: TVars) => void;
}

/**
 * useMutation with the console's conventions: success toast, error toast with the server's
 * message, and invalidation of affected queries.
 */
export function useApiMutation<TVars = void, TResult = unknown>({
	fn,
	invalidate,
	success,
	onSuccess,
}: ApiMutationOptions<TVars, TResult>) {
	const qc = useQueryClient();
	return useMutation({
		mutationFn: fn,
		onSuccess: async (result, vars) => {
			await Promise.all((invalidate ?? []).map((queryKey) => qc.invalidateQueries({ queryKey })));
			if (success) toast.success(typeof success === 'function' ? success(result, vars) : success);
			onSuccess?.(result, vars);
		},
		onError: (err: Error) => toast.error(err.message),
	});
}

/**
 * Build a FormData body from a flat object. Objects are JSON-encoded. Arrays are JSON-encoded
 * too, unless `repeatArrays` is set: views that read a field with `QueryDict.getlist` need
 * one form entry per item.
 */
export function toFormData(
	values: Record<string, unknown>,
	{ repeatArrays = false } = {},
): FormData {
	const fd = new FormData();
	for (const [k, v] of Object.entries(values)) {
		if (v === undefined || v === null) continue;
		if (v instanceof Blob) fd.append(k, v);
		else if (Array.isArray(v) && repeatArrays) v.forEach((item) => fd.append(k, String(item)));
		else if (typeof v === 'object') fd.append(k, JSON.stringify(v));
		else fd.append(k, String(v));
	}
	return fd;
}
