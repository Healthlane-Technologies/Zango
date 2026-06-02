import { useCallback, useEffect, useRef, useState } from 'react';
import useApi from '../../../../hooks/useApi';

/**
 * Variant of appLogs/RuntimeLogs/useLogTail that targets the platform-admin
 * endpoints (`/api/v1/platform/logs/...`) and threads a `tenants` query
 * param through every request. Behaviour otherwise mirrors the in-app hook.
 */
export default function useLogTail({
	component,
	filters, // { since, until?, q, pattern, levels, streams, tenants }
	intervalMs = 2000,
	enabled = true,
	paused = false,
	maxBufferedLines = 4000,
}) {
	const triggerApi = useApi();
	const [lines, setLines] = useState([]);
	const [error, setError] = useState(null);
	const [isPolling, setIsPolling] = useState(false);
	const [initialLoading, setInitialLoading] = useState(false);
	const [loadingEarlier, setLoadingEarlier] = useState(false);
	const [hasMoreEarlier, setHasMoreEarlier] = useState(true);

	const tailCursorRef = useRef(null);
	const earlierCursorRef = useRef(null);
	const pausedRef = useRef(paused);
	useEffect(() => {
		pausedRef.current = paused;
	}, [paused]);

	const filterKey = JSON.stringify({
		component,
		since: filters?.since,
		until: filters?.until,
		levels: filters?.levels || [],
		streams: filters?.streams || [],
		tenants: filters?.tenants || [],
		q: filters?.q || '',
		pattern: filters?.pattern || '',
	});
	useEffect(() => {
		tailCursorRef.current = null;
		earlierCursorRef.current = null;
		setLines([]);
		setError(null);
		setHasMoreEarlier(true);
	}, [filterKey]);

	const buildQs = useCallback(
		(extra = {}) => {
			const p = new URLSearchParams();
			if (filters?.since) p.set('since', filters.since);
			if (filters?.until) p.set('until', filters.until);
			if (filters?.levels?.length) p.set('levels', filters.levels.join(','));
			if (filters?.streams?.length) p.set('streams', filters.streams.join(','));
			if (filters?.tenants?.length) p.set('tenants', filters.tenants.join(','));
			if (filters?.q) p.set('q', filters.q);
			if (filters?.pattern) p.set('pattern', filters.pattern);
			p.set('limit', String(extra.limit || 200));
			Object.entries(extra).forEach(([k, v]) => {
				if (k === 'limit') return;
				if (v !== undefined && v !== null && v !== '') p.set(k, String(v));
			});
			return p.toString();
		},
		[filters]
	);

	useEffect(() => {
		if (!enabled || !component) return;
		let cancelled = false;
		(async () => {
			setInitialLoading(true);
			const { response, success, responseStatus } = await triggerApi({
				url: `/api/v1/platform/logs/${component}/?${buildQs()}`,
				type: 'GET',
				loader: false,
				showErrorModal: false,
			});
			if (cancelled) return;
			setInitialLoading(false);
			if (responseStatus === 503) {
				setError({ kind: 'throttled', retryAfter: 5 });
				return;
			}
			if (!success || !response) {
				setError({ kind: 'fetch_failed', detail: response?.message });
				return;
			}
			setError(null);
			const fresh = response.lines || [];
			setLines(fresh);
			if (fresh.length > 0) {
				const newestTs = new Date(fresh[0].ts).getTime() + 1;
				tailCursorRef.current = String(newestTs);
			}
			if (response.next_cursor?.token) {
				earlierCursorRef.current = response.next_cursor.token;
				setHasMoreEarlier(true);
			} else {
				setHasMoreEarlier(false);
			}
		})();
		return () => {
			cancelled = true;
		};
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [component, filterKey]);

	const pollOnce = useCallback(async () => {
		if (!enabled || !component || pausedRef.current || !tailCursorRef.current)
			return;
		if (typeof document !== 'undefined' && document.hidden) return;
		if (
			filters?.until &&
			Number(tailCursorRef.current) >= new Date(filters.until).getTime()
		) {
			return;
		}
		setIsPolling(true);
		const qs = buildQs({ after: tailCursorRef.current });
		const { response, success, responseStatus } = await triggerApi({
			url: `/api/v1/platform/logs/${component}/tail/?${qs}`,
			type: 'GET',
			loader: false,
			showErrorModal: false,
		});
		setIsPolling(false);
		if (pausedRef.current) return;
		if (responseStatus === 503) {
			setError({ kind: 'throttled', retryAfter: 5 });
			return;
		}
		if (!success || !response) {
			setError({ kind: 'fetch_failed', detail: response?.message });
			return;
		}
		setError(null);
		const fresh = response.lines || [];
		if (response.next_cursor?.token) {
			tailCursorRef.current = response.next_cursor.token;
		}
		if (fresh.length > 0) {
			setLines((prev) => {
				const tagged = fresh.map((l) => ({ ...l, _fresh: true }));
				tagged.reverse();
				const out = [...tagged, ...prev];
				if (out.length > maxBufferedLines) out.length = maxBufferedLines;
				return out;
			});
			window.setTimeout(() => {
				setLines((prev) => prev.map((l) => ({ ...l, _fresh: false })));
			}, 1700);
		}
	}, [component, enabled, buildQs, triggerApi, maxBufferedLines, filters?.until]);

	useEffect(() => {
		if (!enabled || paused || !component) return;
		const id = window.setInterval(pollOnce, intervalMs);
		return () => window.clearInterval(id);
	}, [enabled, paused, component, intervalMs, pollOnce]);

	useEffect(() => {
		const onVis = () => {
			if (!document.hidden) pollOnce();
		};
		document.addEventListener('visibilitychange', onVis);
		return () => document.removeEventListener('visibilitychange', onVis);
	}, [pollOnce]);

	const loadEarlier = useCallback(async () => {
		if (!earlierCursorRef.current || loadingEarlier) return;
		setLoadingEarlier(true);
		const qs = buildQs({ before: earlierCursorRef.current });
		const { response, success, responseStatus } = await triggerApi({
			url: `/api/v1/platform/logs/${component}/?${qs}`,
			type: 'GET',
			loader: false,
			showErrorModal: false,
		});
		setLoadingEarlier(false);
		if (responseStatus === 503) {
			setError({ kind: 'throttled', retryAfter: 5 });
			return;
		}
		if (!success || !response) {
			setError({ kind: 'fetch_failed', detail: response?.message });
			return;
		}
		const older = response.lines || [];
		if (older.length === 0) {
			setHasMoreEarlier(false);
			earlierCursorRef.current = null;
			return;
		}
		setLines((prev) => {
			const out = [...prev, ...older];
			if (out.length > maxBufferedLines) out.length = maxBufferedLines;
			return out;
		});
		if (response.next_cursor?.token) {
			earlierCursorRef.current = response.next_cursor.token;
		} else {
			setHasMoreEarlier(false);
			earlierCursorRef.current = null;
		}
	}, [component, buildQs, triggerApi, loadingEarlier, maxBufferedLines]);

	return {
		lines,
		error,
		isPolling,
		initialLoading,
		loadingEarlier,
		hasMoreEarlier,
		loadEarlier,
	};
}
