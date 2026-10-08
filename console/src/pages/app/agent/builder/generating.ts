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
