import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from '@/ui';
import { agentKeys, type BuildCardStatus, type RunStatus } from './agentMode';
import { api, ApiError } from './client';

// Agent Mode, phase 2: development runs. Endpoints under /api/v1/apps/<uuid>/agent-mode/runs/
// (backend/src/zango/api/platform/agent_mode/v1/views.py). Requirement-level queries and keys
// live in ./agentMode; this module only adds what the Builds panel needs.

/** AgentRunListSerializer. */
export interface RunSummary {
	uuid: string;
	title: string;
	status: RunStatus;
	is_terminal: boolean;
	trigger_kind: 'ui' | 'resume' | string;
	triggered_by: string;
	queued_at: string | null;
	started_at: string | null;
	ended_at: string | null;
	duration_ms: number | null;
	total_cost_usd: string | null;
	num_turns: number | null;
	requires_restart: boolean;
	/** App Studio builds: a compact count of the checks, when the list serializer provides it. */
	checks?: ChecksSummary | null;
	/** The CLI's apiKeySource from the session-init event; "none" = Claude subscription login. */
	auth_source?: string | null;
}

export interface ChecksSummary {
	passed: number;
	failed: number;
	not_verified: number;
	total: number;
}

/** Something only the user can do before a paused (`waiting`) build can go on. */
export interface PendingAction {
	id: string;
	kind: 'hosts_entry' | 'install_playwright' | string;
	title: string;
	detail: string;
	/** A shell command to copy, or "". */
	command: string;
	/** The steps or checks it blocks. */
	blocks: string[];
	/** Set on a refused continue: why the fix isn't detected yet. */
	still_failing_reason?: string;
}

export type LayerName =
	'app_shell' | 'audit_holes' | 'design_lint' | 'api' | 'ui' | 'design' | 'scenarios';

export interface CheckFailure {
	id: string;
	title?: string;
	role?: string;
	spec_path?: string;
	detail?: string;
}

export interface CheckLayer {
	status: 'pass' | 'fail' | 'skip';
	counts?: { pass?: number; fail?: number; skip?: number };
	failures?: CheckFailure[];
	reason?: string;
}

/** An App Studio build's checks (AgentRun.studio_report as the run detail exposes it). */
export interface StudioReport {
	ok: boolean;
	bring_up_ok: boolean;
	frontend?: boolean;
	frontend_reason?: string;
	verdict?: string;
	not_verified?: string[];
	rounds?: number;
	skipped?: Array<{ layer: string; reason: string }>;
	layers?: Partial<Record<LayerName | string, CheckLayer>>;
	report?: { summary_md?: string; md_path?: string; html_path?: string; verdict?: string };
	/** The full HTML report (runs/<run>/report.html), or null when none was written. */
	html_url?: string | null;
	/** What the person who made the app is told (studio_status.user_status). */
	user_status?: BuildCardStatus | null;
}

export interface TestUser {
	role?: string;
	email: string;
	/** Only present for accounts the build created; existing ones report `status: "exists"`. */
	password?: string;
	status?: string;
}

export interface PostStep {
	step: string;
	returncode: number | null;
	duration_ms?: number;
	stderr_tail?: string;
}

export type ModelUsage = Record<
	string,
	{
		costUSD?: number;
		inputTokens?: number;
		outputTokens?: number;
		cacheReadInputTokens?: number;
		cacheCreationInputTokens?: number;
		messages?: number;
	}
>;

/** AgentRunDetailSerializer plus the view's `app_access` and `restart_hint`. */
export interface RunDetail extends RunSummary {
	prompt: string;
	abort_requested: boolean;
	agent_ended_at: string | null;
	model: string;
	effort: string;
	max_turns: number | null;
	max_budget_usd: string | null;
	session_id: string;
	workspace_path: string;
	resumed_from: string | null;
	result_subtype: string;
	terminal_reason: string;
	result_text: string;
	duration_api_ms: number | null;
	input_tokens: number | null;
	output_tokens: number | null;
	cache_read_tokens: number | null;
	cache_creation_tokens: number | null;
	model_usage: ModelUsage | null;
	error_type: string;
	error_message: string;
	api_error_status: number | null;
	files_changed: { added?: string[]; modified?: string[]; deleted?: string[] } | null;
	tool_use_counts: Record<string, number> | null;
	post_steps: PostStep[] | null;
	test_users: TestUser[] | null;
	can_resume: boolean;
	pending_actions?: PendingAction[] | null;
	report?: StudioReport | null;
	restart_hint?: string;
	app_access?: { domain: string; url: string; path: string };
}

/** AgentRunEvent row, as the event tail returns it. */
export interface RunEvent {
	seq: number;
	ts: string | null;
	kind: string;
	phase: string;
	level: string;
	message: string;
	tool_name: string;
	tool_use_id: string;
	parent_tool_use_id: string;
	is_error: boolean;
	data: unknown;
}

export interface TailResponse {
	status: RunStatus;
	is_terminal: boolean;
	phase: string;
	phase_order: string[];
	events: RunEvent[];
	oldest_seq: number | null;
	newest_seq: number | null;
	total: number;
	next_seq: number | null;
	progress: { turns: number | null; cost_usd: string | null };
}

const base = (appId: string) => `/api/v1/apps/${appId}/agent-mode`;

/** The most events one tail request returns (AgentRunEventTailView.MAX_PAGE_SIZE). */
export const TAIL_PAGE = 500;

export const fetchTail = (appId: string, runId: string, afterSeq: number) =>
	api<TailResponse>(
		`${base(appId)}/runs/${runId}/event-tail/?after_seq=${afterSeq}&limit=${TAIL_PAGE}`,
	);

/**
 * Every run for the app, for cost/duration columns. The runs list can't filter by requirement,
 * so the panel joins these against the requirement's own `runs` refs.
 */
export function useRunSummaries(appId: string) {
	return useQuery({
		queryKey: agentKeys.runs(appId),
		queryFn: () =>
			api<{ runs: { records: RunSummary[] } }>(`${base(appId)}/runs/?page=1&page_size=100`).then(
				(r) => r.runs.records,
			),
	});
}

/** Full run: usage, errors, files, test users and the app's URL. */
export function useRunDetail(appId: string, runId: string | undefined) {
	return useQuery({
		queryKey: agentKeys.run(appId, runId ?? ''),
		queryFn: () => api<RunDetail>(`${base(appId)}/runs/${runId}/`),
		enabled: !!runId,
	});
}

/** Refetch everything a run's start or end changes. */
export function useInvalidateRuns(appId: string, requirementId: string) {
	const qc = useQueryClient();
	return () =>
		Promise.all([
			qc.invalidateQueries({ queryKey: agentKeys.requirement(appId, requirementId) }),
			qc.invalidateQueries({ queryKey: agentKeys.requirements(appId) }),
			qc.invalidateQueries({ queryKey: agentKeys.runs(appId) }),
			qc.invalidateQueries({ queryKey: agentKeys.availability(appId) }),
		]);
}

/** The 409 bodies for "already running" carry the in-flight run, which is where to look. */
function inFlightRunOf(err: unknown): string | undefined {
	if (!(err instanceof ApiError) || err.status !== 409) return undefined;
	return (err.body as { response?: { run_uuid?: string } })?.response?.run_uuid;
}

/**
 * Start a build from the approved requirement. `onStarted` gets the new run, or the run
 * already in flight when the server refuses a second one.
 */
export function useStartRun(
	appId: string,
	requirementId: string,
	onStarted: (runId: string) => void,
) {
	const invalidate = useInvalidateRuns(appId, requirementId);
	return useMutation({
		mutationFn: () =>
			api<{ uuid: string; status: RunStatus }>(`${base(appId)}/runs/`, 'POST', {
				requirement_uuid: requirementId,
			}),
		onSuccess: async (r) => {
			await invalidate();
			toast.success('Build started');
			onStarted(r.uuid);
		},
		onError: async (err: Error) => {
			const running = inFlightRunOf(err);
			if (running) {
				await invalidate();
				toast.error('A build is already running for this app');
				onStarted(running);
			} else toast.error(err.message);
		},
	});
}

export function useAbortRun(appId: string) {
	return useMutation({
		mutationFn: (runId: string) =>
			api<{ status: RunStatus }>(`${base(appId)}/runs/${runId}/abort/`, 'POST', {}),
		onSuccess: () => toast.success('Stopping after the current step'),
		onError: (err: Error) => toast.error(err.message),
	});
}

/** Continue a stopped run in a new run that reuses its agent session. */
export function useResumeRun(
	appId: string,
	requirementId: string,
	onStarted: (runId: string) => void,
) {
	const invalidate = useInvalidateRuns(appId, requirementId);
	return useMutation({
		mutationFn: (runId: string) =>
			api<{ uuid: string; resumed_from: string }>(
				`${base(appId)}/runs/${runId}/resume/`,
				'POST',
				{},
			),
		onSuccess: async (r) => {
			await invalidate();
			toast.success('Resuming from where the last run stopped');
			onStarted(r.uuid);
		},
		onError: async (err: Error) => {
			const running = inFlightRunOf(err);
			if (running) {
				await invalidate();
				onStarted(running);
			}
			toast.error(err.message);
		},
	});
}

/**
 * Go on with a build that paused for the user (`waiting`). `skip` finishes without the blocked
 * checks. A 409 that lists `pending_actions` means the fix isn't detected yet; the error's
 * `actions` carry the reason per action.
 */
export class ContinueRefused extends Error {
	constructor(
		message: string,
		readonly actions: PendingAction[],
	) {
		super(message);
	}
}

export function useContinueRun(appId: string, runId: string, onContinued?: () => void) {
	const qc = useQueryClient();
	return useMutation({
		mutationFn: async (skip: boolean) => {
			try {
				return await api<{ status: RunStatus }>(`${base(appId)}/runs/${runId}/continue/`, 'POST', {
					skip,
				});
			} catch (err) {
				if (err instanceof ApiError && err.status === 409) {
					const body = (
						err.body as { response?: { message?: string; pending_actions?: PendingAction[] } }
					)?.response;
					throw new ContinueRefused(body?.message || err.message, body?.pending_actions ?? []);
				}
				throw err;
			}
		},
		onSuccess: async () => {
			await Promise.all([
				qc.invalidateQueries({ queryKey: agentKeys.run(appId, runId) }),
				qc.invalidateQueries({ queryKey: agentKeys.runs(appId) }),
				qc.invalidateQueries({ queryKey: agentKeys.all(appId) }),
			]);
			onContinued?.();
		},
	});
}

/** "6/7 passed · 1 not verified", from a run's report or the list's compact counts. */
export function checksOf(
	source: StudioReport | ChecksSummary | null | undefined,
): ChecksSummary | null {
	if (!source) return null;
	if ('total' in source) return source;
	const layers = Object.values(source.layers ?? {}).filter(Boolean) as CheckLayer[];
	if (!layers.length) return null;
	return {
		total: layers.length,
		passed: layers.filter((l) => l.status === 'pass').length,
		failed: layers.filter((l) => l.status === 'fail').length,
		not_verified: layers.filter((l) => l.status === 'skip').length,
	};
}
