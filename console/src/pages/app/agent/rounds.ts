import {
	isRunActive,
	type Requirement,
	type RequirementStatus,
	type RequirementSummary,
	type RunStatus,
} from '@/api/agentMode';
import type { Tone } from '@/ui';

/**
 * A round is one AgentRequirement: ask for something, agree it, build it. The first is the
 * initial build and later ones are changes. (`spec_version` counts revisions inside a round.)
 */
export interface Round {
	index: number;
	summary: RequirementSummary;
	detail: Requirement | undefined;
}

export const roundLabel = (index: number) => (index === 0 ? 'Initial build' : `Change ${index}`);

export const REQUIREMENT_STATUS: Record<RequirementStatus, [Tone, string]> = {
	gathering: ['accent', 'Gathering'],
	ready: ['amber', 'Ready for review'],
	approved: ['green', 'Approved'],
	abandoned: ['gray', 'Abandoned'],
};

const RUN_LABEL: Record<RunStatus, string> = {
	queued: 'Build queued',
	running: 'Building',
	syncing: 'Applying changes',
	success: 'Built',
	partial: 'Built with sync errors',
	failed: 'Build failed',
	timeout: 'Build timed out',
	aborted: 'Build stopped',
};
export const runLabel = (s: RunStatus) => RUN_LABEL[s] ?? s;

/** Compact date and time; the year only when it isn't this one. */
export function stamp(iso: string | null | undefined): string {
	if (!iso) return '';
	const when = new Date(iso);
	if (Number.isNaN(when.getTime())) return '';
	const opts: Intl.DateTimeFormatOptions = { day: 'numeric', month: 'short' };
	if (when.getFullYear() !== new Date().getFullYear()) opts.year = 'numeric';
	return `${when.toLocaleDateString(undefined, opts)} · ${when.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}`;
}

export type Stage = 'requirements' | 'approved' | 'build' | 'built';
export const STAGES: Array<[Stage, string]> = [
	['requirements', 'Requirements'],
	['approved', 'Approved'],
	['build', 'Build'],
	['built', 'Built'],
];

/** Where a round has got to, from the requirement status and its latest run. */
export function stageOf(r: Requirement | undefined): { stage: Stage; failed: boolean } {
	if (!r || r.status === 'gathering' || r.status === 'ready' || r.status === 'abandoned')
		return { stage: 'requirements', failed: false };
	const run = r.runs[0];
	if (!run) return { stage: 'approved', failed: false };
	if (isRunActive(run.status)) return { stage: 'build', failed: false };
	if (run.status === 'success' || run.status === 'partial')
		return { stage: 'built', failed: false };
	return { stage: 'build', failed: true };
}

/** "$0.42", or "" when there's no cost yet. */
export function cost(v: string | number | null | undefined): string {
	const n = typeof v === 'string' ? parseFloat(v) : v;
	return n && Number.isFinite(n) ? `$${n.toFixed(2)}` : '';
}
