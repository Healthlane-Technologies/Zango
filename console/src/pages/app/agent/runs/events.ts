import type { RunEvent } from '@/api/agentRuns';

// Pure helpers over the run event stream. No React, so they can be checked in isolation.

/**
 * Append a tail page to what's already loaded. Pages are ascending and normally follow on, but
 * a slow response can land after a faster later one, so dedupe by `seq` and keep order.
 */
export function mergeEvents(prev: RunEvent[], page: RunEvent[]): RunEvent[] {
	if (!page.length) return prev;
	const last = prev.length ? prev[prev.length - 1].seq : 0;
	if (page[0].seq > last) return [...prev, ...page];
	const bySeq = new Map(prev.map((e) => [e.seq, e]));
	for (const e of page) bySeq.set(e.seq, e);
	return [...bySeq.values()].sort((a, b) => a.seq - b.seq);
}

const WRITE_TOOLS = new Set(['Write', 'Edit', 'MultiEdit']);

/** Files the agent has written so far, in first-touched order. */
export function filesWritten(events: RunEvent[]): string[] {
	const seen = new Set<string>();
	for (const e of events) {
		if (e.kind !== 'tool_use' || !WRITE_TOOLS.has(e.tool_name)) continue;
		const d = e.data as { file_path?: string; path?: string } | null;
		const path = d?.file_path || d?.path;
		if (path) seen.add(path);
	}
	return [...seen];
}

const MEANINGFUL = new Set(['assistant', 'tool_use', 'post_step', 'sys', 'skill']);

/** The newest event worth showing as "what it's doing now". */
export function latestActivity(events: RunEvent[]): RunEvent | undefined {
	for (let i = events.length - 1; i >= 0; i--)
		if (MEANINGFUL.has(events[i].kind) && events[i].message) return events[i];
	return undefined;
}

/** Strip the workspace root so paths read as the app's own. */
export function relativePath(path: string, workspace?: string): string {
	if (workspace && path.startsWith(workspace))
		return path.slice(workspace.length).replace(/^\/+/, '');
	const i = path.indexOf('/workspaces/');
	return i >= 0 ? path.slice(i + '/workspaces/'.length).replace(/^[^/]+\//, '') : path;
}
