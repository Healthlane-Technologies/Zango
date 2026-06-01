import { useCallback, useEffect, useRef, useState } from 'react';
import useApi from '../../../../hooks/useApi';

/**
 * Lifecycle for the Logs feed:
 *
 *   1. Initial browse — hits /<component>/ to get the LATEST N events
 *      in [since, until-or-now]. Backend uses progressive-window narrowing.
 *   2. Live tail polling — hits /<component>/tail/?after=<cursor> at
 *      `intervalMs` while not paused and document is visible.
 *   3. Load earlier — explicit call via the returned `loadEarlier()`
 *      function. Hits /<component>/?before=<oldest_seen>. Append to bottom.
 *
 *   Lines are kept newest-on-top in `lines`.
 */
export default function useLogTail({
	appId,
	component,
	filters, // { since, until?, q, pattern, levels, streams }
	intervalMs = 2000,
	enabled = true,
	paused = false, // Controlled by the parent — single source of truth.
	maxBufferedLines = 4000,
}) {
	const triggerApi = useApi();
	const [lines, setLines] = useState([]);
	const [error, setError] = useState(null);
	const [isPolling, setIsPolling] = useState(false);
	const [initialLoading, setInitialLoading] = useState(false);
	const [loadingEarlier, setLoadingEarlier] = useState(false);
	const [hasMoreEarlier, setHasMoreEarlier] = useState(true);

	// Forward cursor (timestamp ms) for tail polling — set after initial browse.
	const tailCursorRef = useRef(null);
	// Backward cursor (timestamp ms - 1) for "Load earlier" — set after each browse.
	const earlierCursorRef = useRef(null);
	// Always reflects the latest `paused` value — protects against stale
	// closures captured by leaked intervals.
	const pausedRef = useRef(paused);
	useEffect(() => {
		pausedRef.current = paused;
	}, [paused]);

	// Reset whenever the component or filter set changes meaningfully.
	const filterKey = JSON.stringify({
		component,
		since: filters?.since,
		until: filters?.until,
		levels: filters?.levels || [],
		streams: filters?.streams || [],
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

	// Initial browse — runs whenever filters change.
	useEffect(() => {
		if (!enabled || !component) return;
		let cancelled = false;
		(async () => {
			setInitialLoading(true);
			const { response, success, responseStatus } = await triggerApi({
				url: `/api/v1/apps/${appId}/logs/${component}/?${buildQs()}`,
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
			// Seed the tail cursor from the newest line + 1 ms.
			if (fresh.length > 0) {
				const newestTs = new Date(fresh[0].ts).getTime() + 1;
				tailCursorRef.current = String(newestTs);
			}
			// Seed the "load earlier" cursor from response.next_cursor.
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
	}, [appId, component, filterKey]);

	// Polling — uses tail cursor only.
	const pollOnce = useCallback(async () => {
		// Read paused from the ref so any leaked interval can never sneak
		// in a fetch after the user pauses.
		if (!enabled || !component || pausedRef.current || !tailCursorRef.current)
			return;
		// Don't poll while the tab is hidden — saves CloudWatch calls.
		if (typeof document !== 'undefined' && document.hidden) return;
		// Never tail past a bounded `until` (historical custom-range view).
		if (
			filters?.until &&
			Number(tailCursorRef.current) >= new Date(filters.until).getTime()
		) {
			return;
		}
		setIsPolling(true);
		const qs = buildQs({ after: tailCursorRef.current });
		const { response, success, responseStatus } = await triggerApi({
			url: `/api/v1/apps/${appId}/logs/${component}/tail/?${qs}`,
			type: 'GET',
			loader: false,
			showErrorModal: false,
		});
		setIsPolling(false);
		// If the user paused while the fetch was in flight, discard the
		// response — don't advance the cursor and don't append lines.
		// This guards against in-flight polls AND any leaked-by-HMR
		// interval whose fetch completes after we pause.
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
				// Lines come oldest-first from tail; reverse to newest-first.
				tagged.reverse();
				const out = [...tagged, ...prev];
				if (out.length > maxBufferedLines) out.length = maxBufferedLines;
				return out;
			});
			window.setTimeout(() => {
				setLines((prev) => prev.map((l) => ({ ...l, _fresh: false })));
			}, 1700);
		}
	}, [
		appId,
		component,
		enabled,
		buildQs,
		triggerApi,
		maxBufferedLines,
		filters?.until,
	]);

	// Single interval owner — cleanup uses the locally-captured handle so
	// it never collides with another effect mutating a shared ref.
	useEffect(() => {
		if (!enabled || paused || !component) return;
		const id = window.setInterval(pollOnce, intervalMs);
		return () => window.clearInterval(id);
	}, [enabled, paused, component, intervalMs, pollOnce]);

	// Visibility — only kicks a single immediate poll on becoming
	// visible. The recurring interval is owned exclusively by the
	// polling effect above; this handler never creates a new one.
	useEffect(() => {
		const onVis = () => {
			if (!document.hidden) pollOnce();
		};
		document.addEventListener('visibilitychange', onVis);
		return () => document.removeEventListener('visibilitychange', onVis);
	}, [pollOnce]);

	// Explicit "Load earlier" — append older lines to the bottom.
	const loadEarlier = useCallback(async () => {
		if (!earlierCursorRef.current || loadingEarlier) return;
		setLoadingEarlier(true);
		const qs = buildQs({ before: earlierCursorRef.current });
		const { response, success, responseStatus } = await triggerApi({
			url: `/api/v1/apps/${appId}/logs/${component}/?${qs}`,
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
	}, [appId, component, buildQs, triggerApi, loadingEarlier, maxBufferedLines]);

	const clear = useCallback(() => {
		tailCursorRef.current = null;
		earlierCursorRef.current = null;
		setLines([]);
		setHasMoreEarlier(true);
	}, []);

	return {
		lines,
		error,
		isPolling,
		initialLoading,
		loadingEarlier,
		hasMoreEarlier,
		loadEarlier,
		clear,
	};
}
