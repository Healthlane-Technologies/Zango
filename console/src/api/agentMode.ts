import {
	keepPreviousData,
	queryOptions,
	useMutation,
	useQuery,
	useQueryClient,
} from '@tanstack/react-query';
import { appKeys } from './apps';
import { api } from './client';
import { useApiMutation } from './hooks';
import type { UploadedDocument } from './scaffolds';
import type { TemplateReference } from './templates';

// Agent Mode, phase 1: requirement gathering. Endpoints live under
// /api/v1/apps/<uuid>/agent-mode/ (backend/src/zango/api/platform/agent_mode/v1).
// Runs (phase 2) are owned by pages/app/agent/runs and reuse `agentKeys` from here.

export type RequirementStatus = 'gathering' | 'ready' | 'approved' | 'abandoned';
export type RunStatus =
	| 'queued'
	| 'running'
	| 'syncing'
	/** Paused for the user (e.g. a hosts entry to add); still the app's active run. */
	| 'waiting'
	| 'success'
	| 'partial'
	| 'failed'
	| 'timeout'
	| 'aborted';

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
	/** Where the user was in the preview when they wrote it (user messages only). */
	preview_focus?: PreviewFocus | Record<string, never>;
	/** Files the user attached to this message (reference material for the agent). */
	attachments?: UploadedDocument[];
}

/**
 * Where the user is in the App Studio preview, as the preview reports it ("focus" message).
 * Paths are pointers into the spec YAML. `pointed` is set after they used "Point".
 */
export interface PreviewFocus {
	role?: string;
	page?: string | null;
	title?: string;
	path?: string;
	view?: string;
	record?: { entity: string; id: string | number; label: string };
	tab?: { code?: string; label: string; path: string };
	pointed?: { path: string; label: string; text?: string };
}

/** The chat's build card (backend studio_status.user_status): progress, never failures. */
export interface BuildCardStatus {
	state: 'building' | 'finishing' | 'ready';
	headline: string;
	body: string;
	finishing: string | null;
	active: boolean;
	app_url: string;
	roles: { role: string; steps: string[] }[];
	tried: { steps: number; roles: number; screens: number };
}

export interface RunRef {
	uuid: string;
	status: RunStatus;
	queued_at?: string | null;
	user_status?: BuildCardStatus | null;
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
	/** The template this requirement is built on, pinned to a version; null when from scratch. */
	template?: RequirementTemplate | null;
	/** Bumped on every draft write (agent tool call or manual save); poll-friendly. */
	draft_revision?: number;
	/** True while the spec is the agent's work in progress rather than a finished one. */
	spec_is_draft?: boolean;
	/** The last validation result for a template spec. */
	validation_issues?: SpecIssue[];
	/** 'open': the agent writes a free HTML prototype (Free design); 'kit': the template draws it. */
	preview_mode?: 'open' | 'kit';
	/** Bumped on every prototype write; the frame reloads when it changes. */
	prototype_revision?: number;
	/** Digest of the YAML's not-built menu items, which the preview greys; reloads the frame too. */
	prototype_soon?: string;
	prototype_hash?: string;
}

/** One validation finding on a template spec. `path` is an RFC 6901 pointer into the YAML. */
export interface SpecIssue {
	level: 'error' | 'warning';
	path: string;
	message: string;
	code?: string;
	/** The ui.json section id the path falls in, when the server knows it. */
	section?: string;
	rule?: string;
}

// ---- workflows drawn as swimlanes (agent-described on the payload; lifecycles derived) ----

export type WfNodeKind = 'start' | 'end' | 'task' | 'event' | 'gateway' | 'message';

export interface WfLane {
	id: string;
	/** The role written down the lane's header strip. */
	role: string;
}

export interface WfNode {
	id: string;
	lane: string;
	kind: WfNodeKind;
	label: string;
	/** A small grey annotation under the shape. */
	note?: string;
	/** Where it comes from in the journey (derived nodes), for "show in YAML". */
	pointer?: string;
}

export interface WfFlow {
	from: string;
	to: string;
	kind: 'sequence' | 'message';
	label?: string;
}

export interface WfProcess {
	id: string;
	title: string;
	group?: string;
	source: 'lifecycle' | 'agent';
	lanes: WfLane[];
	nodes: WfNode[];
	flows: WfFlow[];
	/** The lifecycle's object in the journey (derived processes). */
	pointer?: string;
}

export interface Workflows {
	processes: WfProcess[];
}

/** GET requirements/<r>/spec/ — the spec as the builder panel reads it. */
export interface RequirementSpec {
	text: string;
	format: 'yaml' | 'markdown';
	status: RequirementStatus;
	spec_version: number;
	draft_revision: number;
	is_draft: boolean;
	issues: SpecIssue[];
	/** Pointers the last agent turn (or manual save) changed. */
	changed_paths: string[];
	template: { slug: string; name: string; version: string; version_uuid: string } | null;
	/** What the agent didn't take straight from the user's material, per path. */
	flags?: SpecFlag[];
	/** Real gaps only, each tied to a path with a recommended answer; answered in one go. */
	open_decisions?: OpenDecision[];
	/** Documents the requirement was drafted from. */
	documents?: UploadedDocument[];
	/** 'draft' while the agent drafts the whole journey in one pass; null when unknown. */
	mode?: 'draft' | 'interview' | null;
	/** User journeys the agent described while drafting, drawn as swimlanes. */
	workflows?: Workflows | null;
}

export type FlagKind = 'inferred' | 'reference' | 'default' | 'missing';

export interface SpecFlag {
	path: string;
	kind: FlagKind;
	note: string;
	section?: string;
	source?: { document?: string; locator?: string; quote?: string } | null;
}

export interface OpenDecision {
	id: string;
	path: string;
	question: string;
	options: string[];
	recommended?: string;
	why?: string;
}

export interface DecisionAnswer {
	id: string;
	path: string;
	answer: string;
}

/** GET …/app-templates/templates/<slug>/versions/<uuid>/builder/ — immutable per version. */
export interface TemplateBuilderDef {
	json_schema: Record<string, unknown>;
	ui_schema: {
		sections: Array<{
			id: string;
			title: string;
			pointer: string;
			hint?: string;
			order?: number;
			fields?: string[];
			item?: string;
		}>;
	};
	rules: unknown[];
	spec_root: string;
	spec_format: 'yaml' | 'markdown';
	/** Same-origin URL of the template's own builder page (text/html), when it ships one. */
	builder_url?: string | null;
	/**
	 * The page that renders the app's live preview from the spec: the template's own, or the
	 * platform's generic one (App Studio) for specs in the generic dialect. Null: no preview.
	 */
	preview_url?: string | null;
	preview_source?: 'template' | 'generic' | null;
	/** The spec's vocabulary: 'zango-app/1' for the generic app spec, '' for a template's own. */
	spec_dialect?: string;
	/** Reference journeys the draft can start from. */
	references?: TemplateReference[];
	starter_yaml: string;
	example_yaml: string;
}

export interface RequirementTemplate {
	slug: string;
	name: string;
	one_liner: string;
	spec_format: 'yaml' | 'markdown';
	version: string;
	version_uuid: string;
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
	/** Free design (open prototypes) is switched on for this platform. */
	open_prototype?: boolean;
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
	spec: (appId: string, reqId: string) => [...agentKeys.requirement(appId, reqId), 'spec'] as const,
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

/**
 * A new round: plain text, or (template apps) a brief with documents and a reference. `focus` is
 * where the user was in the preview (or what they pointed at), as on a reply.
 */
export type NewRoundInput =
	| string
	| {
			prompt?: string;
			reference?: string;
			documents?: File[];
			focus?: PreviewFocus | null;
			preview_mode?: 'open' | 'kit';
	  };

export function useCreateRequirement(appId: string, onCreated: (uuid: string) => void) {
	return useApiMutation({
		fn: (input: NewRoundInput) => {
			const url = `${base(appId)}/requirements/`;
			if (typeof input === 'string')
				return api<{ uuid: string; status: RequirementStatus }>(url, 'POST', { prompt: input });
			const body = new FormData();
			if (input.prompt) body.append('prompt', input.prompt);
			if (input.reference) body.append('reference', input.reference);
			if (input.focus) body.append('focus', JSON.stringify(input.focus));
			if (input.preview_mode) body.append('preview_mode', input.preview_mode);
			for (const file of input.documents ?? []) body.append('documents', file, file.name);
			return api<{ uuid: string; status: RequirementStatus }>(url, 'POST', body);
		},
		invalidate: [agentKeys.requirements(appId)],
		onSuccess: (r) => onCreated(r.uuid),
	});
}

export function useSendMessage(appId: string, reqId: string) {
	return useApiMutation({
		fn: (
			message: string | { content: string; focus?: PreviewFocus | null; documents?: File[] },
		) => {
			const url = `${base(appId)}/requirements/${reqId}/messages/`;
			if (typeof message === 'string') return api<{ status: RequirementStatus }>(url, 'POST', { content: message });
			if (!message.documents?.length)
				return api<{ status: RequirementStatus }>(url, 'POST', {
					content: message.content,
					...(message.focus ? { focus: message.focus } : {}),
				});
			// Attachments go as multipart, like a new change's documents.
			const body = new FormData();
			body.append('content', message.content);
			if (message.focus) body.append('focus', JSON.stringify(message.focus));
			for (const file of message.documents) body.append('documents', file, file.name);
			return api<{ status: RequirementStatus }>(url, 'POST', body);
		},
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

/**
 * Preview-first "Commit for build": the server finalizes a draft spec and approves it in one
 * step, refusing as approve does (400 spec errors, 409 open decisions / agent working / stale
 * revision). Errors are left to the caller, which turns each into the right next step.
 */
export function useCommitRequirement(appId: string, reqId: string) {
	const qc = useQueryClient();
	return useMutation({
		mutationFn: (baseRevision: number) =>
			api<{ status: RequirementStatus; can_build: boolean }>(
				`${base(appId)}/requirements/${reqId}/approve/`,
				'POST',
				{ commit: true, base_revision: baseRevision },
			),
		onSettled: () =>
			Promise.all([
				qc.invalidateQueries({ queryKey: agentKeys.requirement(appId, reqId) }),
				qc.invalidateQueries({ queryKey: agentKeys.requirements(appId) }),
			]),
	});
}

/**
 * A requirement's spec for the builder panel. Keyed on the revision the requirement reports,
 * so every draft write (agent or manual) fetches afresh while the previous one stays on screen.
 */
export function useRequirementSpec(
	appId: string,
	reqId: string | undefined,
	revision: { draft?: number; version?: number; status?: string; turns?: number; thinking?: boolean },
) {
	return useQuery({
		// Open decisions and flags change without a draft revision: the turn's end refetches them.
		queryKey: [
			...agentKeys.spec(appId, reqId ?? ''),
			revision.draft ?? 0,
			revision.version ?? 0,
			revision.status ?? '',
			revision.turns ?? 0,
			!!revision.thinking,
		],
		queryFn: () => api<RequirementSpec>(`${base(appId)}/requirements/${reqId}/spec/`),
		enabled: !!reqId,
		placeholderData: keepPreviousData,
	});
}

/** A template version's builder definition. Published versions never change. */
export function useTemplateBuilder(slug: string | undefined, versionUuid: string | undefined) {
	return useQuery({
		queryKey: ['template-builder', slug ?? '', versionUuid ?? ''],
		queryFn: () =>
			api<TemplateBuilderDef>(
				`/api/v1/platform/app-templates/templates/${slug}/versions/${versionUuid}/builder/`,
			),
		enabled: !!slug && !!versionUuid,
		staleTime: Infinity,
		gcTime: Infinity,
	});
}

// ---- template spec writes (F3) ------------------------------------------------------------
// PUT/finalize answer with the same payload as GET …/spec/. A stale base_revision, a save
// while the agent is thinking, or an approved spec → 409 {message, current}; a spec that
// breaks the template's shape → 400 {message, issues}.

export const saveSpecYaml = (appId: string, reqId: string, yaml: string, baseRevision: number) =>
	api<RequirementSpec>(`${base(appId)}/requirements/${reqId}/spec/`, 'PUT', {
		yaml,
		base_revision: baseRevision,
	});

export const finalizeSpec = (appId: string, reqId: string, baseRevision: number) =>
	api<RequirementSpec>(`${base(appId)}/requirements/${reqId}/spec/finalize/`, 'POST', {
		base_revision: baseRevision,
	});

export const validateSpecYaml = (appId: string, reqId: string, yaml: string) =>
	api<{ issues: SpecIssue[] }>(`${base(appId)}/requirements/${reqId}/spec/validate/`, 'POST', {
		yaml,
	});

/** The 409 body's `current` spec, or the 400 body's `issues`, from an ApiError. */
export function specErrorBody(err: unknown): { current?: RequirementSpec; issues?: SpecIssue[] } {
	const body = (err as { body?: { response?: unknown } } | null)?.body?.response;
	return body && typeof body === 'object'
		? (body as { current?: RequirementSpec; issues?: SpecIssue[] })
		: {};
}

/**
 * A template's own builder page (e.g. Journey Studio), composed by the server with the
 * platform adapter already injected. Immutable per template version.
 */
/** The open prototype, assembled into one page; `version` pins an approved version. */
export const prototypeUrl = (appId: string, reqId: string, version?: number) =>
	`${base(appId)}/requirements/${reqId}/prototype/${version ? `?v=${version}` : ''}`;

/** The prototype page at a revision: refetched when the agent writes a part. */
export function usePrototypeHtml(
	appId: string,
	reqId: string,
	revision: number | undefined,
	soon?: string,
) {
	return useQuery({
		queryKey: ['agent-prototype', appId, reqId, revision ?? 0, soon ?? ''],
		queryFn: async () => {
			const res = await fetch(prototypeUrl(appId, reqId), { credentials: 'same-origin' });
			if (res.status === 404) return null;
			if (!res.ok) throw new Error(`The prototype could not be loaded (${res.status}).`);
			return res.text();
		},
		enabled: !!revision,
		staleTime: Infinity,
		placeholderData: keepPreviousData,
		retry: 1,
	});
}

export function useBuilderHtml(url: string | null | undefined) {
	return useQuery({
		queryKey: ['template-builder-html', url ?? ''],
		queryFn: async () => {
			const res = await fetch(url!, { credentials: 'same-origin' });
			if (!res.ok) throw new Error(`The template's builder could not be loaded (${res.status}).`);
			return res.text();
		},
		enabled: !!url,
		staleTime: Infinity,
		gcTime: Infinity,
		retry: 1,
	});
}

// ---- one-pass drafting: decisions, flags, documents -----------------------------------------

/** Answer every open decision in one message; the agent applies them in one turn. */
export function useAnswerDecisions(appId: string, reqId: string) {
	return useApiMutation({
		fn: ({ content, answers }: { content: string; answers: DecisionAnswer[] }) =>
			api<{ status: RequirementStatus }>(`${base(appId)}/requirements/${reqId}/messages/`, 'POST', {
				content,
				answers,
			}),
		invalidate: [agentKeys.requirement(appId, reqId)],
		success: 'Answers sent',
	});
}

/** Accept the agent's assumptions at these paths; returns the spec without those flags. */
export function useConfirmFlags(appId: string, reqId: string) {
	return useApiMutation({
		fn: (paths: string[]) =>
			api<RequirementSpec>(`${base(appId)}/requirements/${reqId}/flags/confirm/`, 'POST', {
				paths,
			}),
		invalidate: [agentKeys.spec(appId, reqId), agentKeys.requirement(appId, reqId)],
	});
}

/** Where a requirement's uploaded document can be downloaded. */
export const documentUrl = (appId: string, reqId: string, id: string | number) =>
	`${base(appId)}/requirements/${reqId}/documents/${id}/`;
