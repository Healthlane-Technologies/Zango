// The user's unsaved edits to a template spec, and how they meet the agent's.
//
// Clean: the panel shows the newest server spec and follows every poll. Dirty: the panel
// shows the user's text and never lets a poll overwrite it. If the server moves on
// underneath (the agent edited, or a save came back 409), the draft is in conflict and the
// user decides: review the agent's version, keep theirs (re-save on the new revision), or
// discard theirs.

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
	agentKeys,
	finalizeSpec,
	saveSpecYaml,
	specErrorBody,
	validateSpecYaml,
	type RequirementSpec,
	type SpecIssue,
} from '@/api/agentMode';
import { ApiError } from '@/api/client';
import { toast, useDebounced } from '@/ui';
import { applyEdit, parseSpec, SpecEditError, type SpecEdit } from './yamlDoc';

export type EditOrigin = 'form' | 'yaml';

export interface SpecDraftController {
	dirty: boolean;
	/** Save unsaved edits, if any. Resolves false if they could not be saved. */
	flush: () => Promise<boolean>;
}

const newer = (a: RequirementSpec | null, b: RequirementSpec) =>
	a && a.draft_revision >= b.draft_revision ? a : b;

// Unsaved drafts outlive the panel: switching to the Builds tab (or another round) unmounts
// it, and coming back must not have silently thrown the user's edits away.
interface Kept {
	text: string;
	base: RequirementSpec;
	origin: EditOrigin;
}
const kept = new Map<string, Kept>();

export function useSpecDraft({
	appId,
	reqId,
	server,
}: {
	appId: string;
	reqId: string;
	server: RequirementSpec;
}) {
	const qc = useQueryClient();
	// The newest spec we know of: the polled one, or a save/finalize response if that's newer.
	const [echo, setEcho] = useState<RequirementSpec | null>(null);
	const latest = newer(echo, server);

	const [text, setText] = useState<string | null>(() => kept.get(reqId)?.text ?? null);
	const [origin, setOrigin] = useState<EditOrigin>(() => kept.get(reqId)?.origin ?? 'form');
	const [base, setBase] = useState<RequirementSpec>(() => kept.get(reqId)?.base ?? latest);
	const [rejected, setRejected] = useState<RequirementSpec | null>(null);
	const [reviewing, setReviewing] = useState(false);
	const [saveIssues, setSaveIssues] = useState<SpecIssue[] | null>(null);
	const [busy, setBusy] = useState<'save' | 'finalize' | null>(null);

	const dirty = text !== null && text !== base.text;
	useEffect(() => {
		if (dirty && text !== null) kept.set(reqId, { text, base, origin });
		else kept.delete(reqId);
	}, [dirty, text, base, origin, reqId]);
	// While clean, the draft's base follows the server.
	useEffect(() => {
		if (!dirty) setBase(latest);
	}, [dirty, latest]);

	// The server spec the draft is now behind: a 409's `current`, or a poll that moved on.
	const incoming =
		dirty && (rejected ?? (latest.draft_revision > base.draft_revision ? latest : null));

	const current = text ?? base.text;
	// YAML typed in the editor is parsed once it settles; form edits are parsed at once.
	const settled = useDebounced(current, 250);
	const parseSource = origin === 'yaml' ? settled : current;
	const parsed = useMemo(() => parseSpec(parseSource), [parseSource]);

	// Server-side checks (rules the browser doesn't know) for unsaved text.
	const validateText = useDebounced(dirty && !parsed.errors.length ? parseSource : '', 600);
	const validated = useQuery({
		queryKey: [...agentKeys.spec(appId, reqId), 'validate', validateText],
		queryFn: () => validateSpecYaml(appId, reqId, validateText),
		enabled: !!validateText,
		staleTime: Infinity,
	});

	const reset = useCallback((to: RequirementSpec) => {
		setText(null);
		setBase(to);
		setRejected(null);
		setReviewing(false);
		setSaveIssues(null);
	}, []);

	const settle = useCallback(
		(resp: RequirementSpec) => {
			setEcho(resp);
			reset(resp);
			qc.invalidateQueries({ queryKey: agentKeys.requirement(appId, reqId) });
			qc.invalidateQueries({ queryKey: agentKeys.requirements(appId) });
		},
		[appId, reqId, qc, reset],
	);

	const fail = useCallback((err: unknown) => {
		const body = specErrorBody(err);
		const status = err instanceof ApiError ? err.status : 0;
		if (status === 409 && body.current) {
			setRejected(body.current);
			toast.error('The spec changed while you were editing.');
		} else if (status === 400 && body.issues) {
			setSaveIssues(body.issues);
			toast.error(err instanceof Error ? err.message : 'The spec could not be saved.');
		} else toast.error(err instanceof Error ? err.message : 'The spec could not be saved.');
	}, []);

	/** Save the draft; resolves to the saved spec, or null if it wasn't saved. */
	const persist = useCallback(
		async (onRevision?: number): Promise<RequirementSpec | null> => {
			if (text === null) return base;
			if (parseSpec(text).errors.length) {
				toast.error('Fix the YAML errors before saving.');
				return null;
			}
			setBusy('save');
			try {
				const resp = await saveSpecYaml(appId, reqId, text, onRevision ?? base.draft_revision);
				settle(resp);
				toast.success('Spec saved');
				return resp;
			} catch (err) {
				fail(err);
				return null;
			} finally {
				setBusy(null);
			}
		},
		[text, base, appId, reqId, settle, fail],
	);
	const save = useCallback(async (onRevision?: number) => !!(await persist(onRevision)), [persist]);

	const finalize = useCallback(async (): Promise<boolean> => {
		const from = dirty ? await persist() : latest;
		if (!from) return false;
		setBusy('finalize');
		try {
			settle(await finalizeSpec(appId, reqId, from.draft_revision));
			toast.success('Marked as ready for review');
			return true;
		} catch (err) {
			fail(err);
			return false;
		} finally {
			setBusy(null);
		}
	}, [dirty, persist, latest, appId, reqId, settle, fail]);

	const edit = useCallback(
		(change: SpecEdit) => {
			try {
				setText(applyEdit(text ?? base.text, change));
				setOrigin('form');
				setSaveIssues(null);
			} catch (err) {
				toast.error(err instanceof SpecEditError ? err.message : String(err));
			}
		},
		[text, base.text],
	);

	const type = useCallback((next: string) => {
		setText(next);
		setOrigin('yaml');
		setSaveIssues(null);
	}, []);

	const controller = useRef<SpecDraftController>({ dirty: false, flush: async () => true });
	controller.current.dirty = dirty;
	controller.current.flush = () => (dirty ? save() : Promise.resolve(true));

	const incomingText = incoming ? incoming.text : null;
	const incomingParsed = useMemo(
		() => (incomingText === null ? null : parseSpec(incomingText)),
		[incomingText],
	);

	return {
		/** What the panel shows: the agent's version while reviewing a conflict, else the draft. */
		text: reviewing && incoming ? incoming.text : current,
		shown: reviewing && incoming ? incoming : latest,
		parsed: reviewing && incomingParsed ? incomingParsed : parsed,
		issues:
			reviewing && incoming
				? incoming.issues
				: dirty
					? (saveIssues ?? validated.data?.issues ?? base.issues)
					: latest.issues,
		dirty,
		base,
		latest,
		incoming: incoming || null,
		reviewing,
		busy,
		edit,
		type,
		save: () => save(),
		finalize,
		discard: () => reset(incoming || latest),
		keepMine: () => (incoming ? save(incoming.draft_revision) : save()),
		toggleReview: () => setReviewing((v) => !v),
		controller: controller.current,
	};
}
