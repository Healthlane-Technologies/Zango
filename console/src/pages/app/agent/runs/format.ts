import type { RunStatus } from '@/api/agentMode';
import type { Tone } from '@/ui';

export const RUN_STATUS: Record<RunStatus, { label: string; tone: Tone }> = {
	queued: { label: 'Queued', tone: 'gray' },
	running: { label: 'Building', tone: 'accent' },
	syncing: { label: 'Applying changes', tone: 'amber' },
	waiting: { label: 'Waiting for you', tone: 'amber' },
	success: { label: 'Built', tone: 'green' },
	partial: { label: 'Built with sync errors', tone: 'amber' },
	failed: { label: 'Failed', tone: 'red' },
	timeout: { label: 'Timed out', tone: 'red' },
	aborted: { label: 'Stopped', tone: 'gray' },
};

export const runStatus = (s: string) =>
	RUN_STATUS[s as RunStatus] ?? { label: s, tone: 'gray' as Tone };

/** The build's coarse stages, in order (RUN_PHASE_ORDER on the backend). */
export const PHASES: Array<{ id: string; label: string; hint: string }> = [
	{ id: 'preparing', label: 'Preparing', hint: 'Packages and workspace snapshot' },
	{ id: 'planning', label: 'Planning', hint: 'Reading the app' },
	{ id: 'building', label: 'Building', hint: 'Models, views and forms' },
	{ id: 'wiring', label: 'Wiring up', hint: 'Routes, menus and the app module' },
	{ id: 'applying', label: 'Applying', hint: 'Migrations and sync' },
	{ id: 'users', label: 'Roles and users', hint: 'Test sign-ins' },
	{ id: 'done', label: 'Finished', hint: '' },
];

export function fmtCost(v: string | number | null | undefined): string {
	if (v === null || v === undefined || v === '') return '—';
	const n = Number(v);
	if (!Number.isFinite(n)) return '—';
	// Sub-cent runs still cost something; don't round them away to $0.00.
	return `$${n > 0 && n < 0.01 ? n.toFixed(4) : n.toFixed(2)}`;
}

export function fmtTokens(v: number | null | undefined): string {
	if (v === null || v === undefined) return '—';
	if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(v >= 10_000_000 ? 0 : 1)}M`;
	if (v >= 1_000) return `${(v / 1_000).toFixed(v >= 10_000 ? 0 : 1)}k`;
	return String(v);
}

export function fmtDuration(ms: number | null | undefined): string {
	if (ms === null || ms === undefined || !Number.isFinite(ms)) return '—';
	const s = Math.round(ms / 1000);
	if (s < 60) return `${s}s`;
	const m = Math.floor(s / 60);
	if (m < 60) return `${m}m ${String(s % 60).padStart(2, '0')}s`;
	return `${Math.floor(m / 60)}h ${String(m % 60).padStart(2, '0')}m`;
}

/** mm:ss (or h:mm:ss) between two instants; `end` defaults to now. */
export function clock(
	startIso: string | null | undefined,
	endIso?: string | null,
	now = Date.now(),
): string {
	if (!startIso) return '';
	const secs = Math.max(
		0,
		Math.floor(((endIso ? Date.parse(endIso) : now) - Date.parse(startIso)) / 1000),
	);
	const h = Math.floor(secs / 3600);
	const mm = String(Math.floor((secs % 3600) / 60)).padStart(2, '0');
	const ss = String(secs % 60).padStart(2, '0');
	return h ? `${h}:${mm}:${ss}` : `${mm}:${ss}`;
}

export function timeOfDay(iso: string | null | undefined): string {
	if (!iso) return '';
	const d = new Date(iso);
	return Number.isNaN(d.getTime()) ? '' : d.toLocaleTimeString('en-GB', { hour12: false });
}
