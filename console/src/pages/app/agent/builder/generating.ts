import { useRef } from 'react';
import { parse as parseYaml } from 'yaml';

/**
 * Whether the agent is still producing the first version of the app's preview: it is working
 * and what the spec holds isn't an app yet (the template's untouched starter, the very first
 * revision, or YAML the preview can't read). After that, a turn only updates the preview.
 */
export function isGeneratingPreview({
	thinking,
	text,
	starter,
	draftRevision,
	yamlBroken,
}: {
	thinking: boolean;
	text: string;
	starter?: string | null;
	draftRevision: number;
	yamlBroken: boolean;
}): boolean {
	if (!thinking) return false;
	return (
		draftRevision <= 1 ||
		yamlBroken ||
		!text.trim() ||
		(!!starter && text.trim() === starter.trim())
	);
}

/**
 * The generic template's starter is a placeholder ("New App" with a "Records" page), not a
 * first cut of anything: a domain template's starter is a real app worth looking at.
 */
export function starterIsPlaceholder(
	builder?: {
		spec_dialect?: string;
		preview_source?: 'template' | 'generic' | null;
	} | null,
): boolean {
	return builder?.spec_dialect === 'zango-app/1' && builder?.preview_source === 'template';
}

export type PreviewStage = 'generating' | 'awaiting' | 'ready';

/** The codes of a spec's entities and its app, read leniently (half-written YAML included). */
function landmarks(text: string): { app: string; entities: Set<string> } {
	const out = { app: '', entities: new Set<string>() };
	try {
		const doc = parseYaml(text) as {
			app?: { code?: unknown };
			modules?: Array<{ entities?: Array<{ code?: unknown }> }>;
		} | null;
		out.app = typeof doc?.app?.code === 'string' ? doc.app.code : '';
		for (const m of Array.isArray(doc?.modules) ? doc.modules : [])
			for (const e of Array.isArray(m?.entities) ? m.entities : [])
				if (typeof e?.code === 'string') out.entities.add(e.code);
	} catch {
		/* unreadable YAML is handled by the caller */
	}
	return out;
}

/**
 * Whether the spec still carries the placeholder starter's own content: its app code, or one
 * of its made-up entities. The agent writes the first version in several edits, so the spec
 * stops being *equal* to the starter long before it stops showing the starter's pages.
 */
export function placeholderRemains(text: string, starter?: string | null): boolean {
	if (!starter?.trim() || !text.trim()) return false;
	const before = landmarks(starter);
	const now = landmarks(text);
	return (
		(!!before.app && now.app === before.app) ||
		[...before.entities].some((c) => now.entities.has(c))
	);
}

export interface PreviewStageArgs {
	thinking: boolean;
	text: string;
	starter?: string | null;
	draftRevision: number;
	yamlBroken: boolean;
	placeholderStarter: boolean;
	/** False once the agent has marked the spec ready: then it is whatever it is. */
	isDraft?: boolean;
}

/**
 * What the preview pane shows.
 *  - 'generating': the agent is writing the first version (which takes several edits).
 *  - 'awaiting': it asked its questions first, so the spec is still the placeholder starter;
 *    showing that would pass a made-up "Records" page off as the first cut of the user's app.
 *  - 'ready': there is an app to look at.
 */
export function previewStage(args: PreviewStageArgs): PreviewStage {
	if (isGeneratingPreview(args)) return 'generating';
	const { text, starter, draftRevision, placeholderStarter, thinking } = args;
	if (!placeholderStarter) return 'ready';
	const untouched =
		!text.trim() || draftRevision <= 1 || (!!starter && text.trim() === starter.trim());
	const placeholder = untouched || (args.isDraft !== false && placeholderRemains(text, starter));
	if (!placeholder) return 'ready';
	return thinking ? 'generating' : 'awaiting';
}

/**
 * previewStage, held at 'generating' until the turn that started the first version ends:
 * halfway through it the placeholder is gone but the app is only half there.
 */
export function usePreviewStage(args: PreviewStageArgs): PreviewStage {
	const stage = previewStage(args);
	const firstCut = useRef(false);
	if (!args.thinking) firstCut.current = false;
	else if (stage === 'generating') firstCut.current = true;
	return args.thinking && firstCut.current ? 'generating' : stage;
}
