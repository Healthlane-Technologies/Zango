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

/**
 * What the preview pane shows. 'awaiting': the agent has asked its questions before writing
 * anything, so the spec is still the placeholder starter; showing that as a preview would
 * pass a made-up "Records" page off as the first cut of the user's app.
 */
export function previewStage(
	args: Parameters<typeof isGeneratingPreview>[0] & { placeholderStarter: boolean },
): PreviewStage {
	if (isGeneratingPreview(args)) return 'generating';
	const { text, starter, draftRevision, placeholderStarter } = args;
	const untouched =
		!text.trim() || draftRevision <= 1 || (!!starter && text.trim() === starter.trim());
	return !args.thinking && placeholderStarter && untouched ? 'awaiting' : 'ready';
}
