import { queryOptions, useQuery } from '@tanstack/react-query';
import { appKeys } from './apps';
import { api } from './client';
import { useApiMutation } from './hooks';

// Agent Mode, phase 1: requirement gathering. Endpoints live under
// /api/v1/apps/<uuid>/agent-mode/ (backend/src/zango/api/platform/agent_mode/v1).
// Runs (phase 2) are owned by pages/app/agent/runs and reuse `agentKeys` from here.

export type RequirementStatus = 'gathering' | 'ready' | 'approved' | 'abandoned';
export type RunStatus =
	'queued' | 'running' | 'syncing' | 'success' | 'partial' | 'failed' | 'timeout' | 'aborted';

export const TERMINAL_RUN_STATUSES: RunStatus[] = [
	'success',
	'partial',
	'failed',
	'timeout',
	'aborted',
];
export const isRunActive = (s: RunStatus | undefined | null) =>
	!!s && !TERMINAL_RUN_STATUSES.includes(s);

/** One structured question from the analyst's ```zango-questions block (requirements.py). */
export interface AnalystQuestion {
	id: string;
	question: string;
	type: 'single' | 'multi';
	options: string[];
	/** Pre-ticked defaults: the analyst's recommendation. */
	selected: string[];
	allow_other: boolean;
}

export interface RequirementMessage {
	seq: number;
	role: 'user' | 'assistant';
	content: string;
	ts: string;
	is_question: boolean;
	questions: AnalystQuestion[];
}

export interface RunRef {
	uuid: string;
	status: RunStatus;
	queued_at?: string | null;
}

export interface RequirementSummary {
	uuid: string;
	title: string;
	status: RequirementStatus;
	can_build: boolean;
	spec_version: number;
	turns: number;
	total_cost_usd: string | number | null;
	run_count: number;
	latest_run: RunRef | null;
	created_at: string;
	approved_at: string | null;
}

export interface Requirement {
	uuid: string;
	title: string;
	status: RequirementStatus;
	can_build: boolean;
	initial_prompt: string;
	spec_markdown: string;
	spec_version: number;
	turns: number;
	total_cost_usd: string | number | null;
	/** True while an analyst turn is queued or running. Poll until it clears. */
	is_thinking: boolean;
	error_message: string;
	created_at: string;
	approved_at: string | null;
	approved_by: string | null;
	messages: RequirementMessage[];
	/** Latest ten runs, newest first. */
	runs: RunRef[];
}

export interface Availability {
	available: boolean;
	reasons: string[];
	checks: Record<string, unknown>;
	in_flight_run: { uuid: string; status: RunStatus; started_at: string | null } | null;
	last_run: {
		uuid: string;
		status: RunStatus;
		ended_at: string | null;
		requires_restart: boolean;
	} | null;
}

interface Paginated<T> {
	total_records: number;
	total_pages: number;
	records: T[];
}

const base = (appId: string) => `/api/v1/apps/${appId}/agent-mode`;

export const agentKeys = {
	all: (appId: string) => [...appKeys.detail(appId), 'agent'] as const,
	availability: (appId: string) => [...agentKeys.all(appId), 'availability'] as const,
	requirements: (appId: string) => [...agentKeys.all(appId), 'requirements'] as const,
	requirement: (appId: string, reqId: string) => [...agentKeys.requirements(appId), reqId] as const,
	runs: (appId: string) => [...agentKeys.all(appId), 'runs'] as const,
	run: (appId: string, runId: string) => [...agentKeys.runs(appId), runId] as const,
};

/** How often to re-read a requirement while the analyst is replying (the classic panel's cadence). */
export const THINKING_POLL_MS = 2000;
/** A build takes minutes; while one is in flight the requirement's run list is re-read at this pace. */
export const RUN_POLL_MS = 3000;

/**
 * Query options for one requirement. Polls while the analyst is composing a reply, and while
 * the requirement's latest run is still going (a build changes the requirement without any
 * message arriving). Shared so every screen reading a requirement polls the same way.
 */
export function requirementQuery(appId: string, reqId: string | undefined) {
	return queryOptions({
		queryKey: agentKeys.requirement(appId, reqId ?? ''),
		queryFn: () => api<Requirement>(`${base(appId)}/requirements/${reqId}/`),
		enabled: !!reqId,
		refetchInterval: (q) => {
			const r = q.state.data;
			if (!r) return false;
			if (r.is_thinking) return THINKING_POLL_MS;
			return isRunActive(r.runs[0]?.status) ? RUN_POLL_MS : false;
		},
	});
}

export function useAvailability(appId: string) {
	return useQuery({
		queryKey: agentKeys.availability(appId),
		queryFn: () => api<Availability>(`${base(appId)}/availability/`),
		staleTime: 30_000,
	});
}

export function useRequirements(appId: string) {
	return useQuery({
		queryKey: agentKeys.requirements(appId),
		// Newest first, as the backend orders them; one page covers any realistic history.
		queryFn: () =>
			api<{ requirements: Paginated<RequirementSummary> }>(
				`${base(appId)}/requirements/?page=1&page_size=100`,
			).then((r) => r.requirements.records),
	});
}

/** A requirement's conversation, spec, status and latest runs. Polls while anything is in flight. */
export function useRequirement(appId: string, reqId: string | undefined) {
	return useQuery(requirementQuery(appId, reqId));
}

export function useCreateRequirement(appId: string, onCreated: (uuid: string) => void) {
	return useApiMutation({
		fn: (prompt: string) =>
			api<{ uuid: string; status: RequirementStatus }>(`${base(appId)}/requirements/`, 'POST', {
				prompt,
			}),
		invalidate: [agentKeys.requirements(appId)],
		onSuccess: (r) => onCreated(r.uuid),
	});
}

export function useSendMessage(appId: string, reqId: string) {
	return useApiMutation({
		fn: (content: string) =>
			api<{ status: RequirementStatus }>(`${base(appId)}/requirements/${reqId}/messages/`, 'POST', {
				content,
			}),
		invalidate: [agentKeys.requirement(appId, reqId)],
	});
}

export function useSaveSpec(appId: string, reqId: string) {
	return useApiMutation({
		fn: (spec_markdown: string) =>
			api<{ spec_version: number; status: RequirementStatus }>(
				`${base(appId)}/requirements/${reqId}/spec/`,
				'POST',
				{ spec_markdown },
			),
		invalidate: [agentKeys.requirement(appId, reqId), agentKeys.requirements(appId)],
		success: 'Spec saved',
	});
}

export function useApproveRequirement(appId: string, reqId: string) {
	return useApiMutation({
		fn: () =>
			api<{ status: RequirementStatus; can_build: boolean }>(
				`${base(appId)}/requirements/${reqId}/approve/`,
				'POST',
				{},
			),
		invalidate: [agentKeys.requirement(appId, reqId), agentKeys.requirements(appId)],
		success: 'Requirements approved',
	});
}
