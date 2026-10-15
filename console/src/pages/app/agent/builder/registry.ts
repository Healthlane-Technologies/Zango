// Extension point: a template can ship its own builder UI (e.g. a Journey Studio port for
// PSP) without the generic panel changing. Keyed by template slug; empty for now.

import type { ComponentType, LazyExoticComponent } from 'react';
import type { PreviewFocus, Requirement, RequirementSpec, TemplateBuilderDef } from '@/api/agentMode';
import type { SpecDraftController } from './useSpecDraft';

export interface BuilderProps {
	appId: string;
	requirement: Requirement;
	builder: TemplateBuilderDef;
	spec: RequirementSpec;
	/** Pointers changed by the last agent turn (server-reported, or diffed as a fallback). */
	changed: string[];
	/** The user may edit this spec (the active round, still open). */
	editable?: boolean;
	/** Receives the draft controller, so the page can save unsaved edits before sending/approving. */
	onController?: (controller: SpecDraftController) => void;
	/** Show this pointer in the spec (e.g. "show me" on a decision in the chat). */
	jump?: { pointer: string; nonce: number } | null;
	/** Preview-first: the page's "Commit for build" action, shown in the pane header too. */
	commit?: CommitAction;
	/** Open one of the preview pane's sheets from outside (e.g. Checks after a refused commit). */
	sheet?: { sheet: 'checks' | 'flags' | 'spec'; nonce: number } | null;
	/** Where the user is in the preview, and what they pointed at; goes with their next message. */
	onPreviewFocus?: (focus: PreviewFocus) => void;
}

export interface CommitAction {
	onClick: () => void;
	/** Why it can't be used right now; null when it can. */
	blocked: string | null;
	loading: boolean;
}

export const builderOverrides: Record<
	string,
	LazyExoticComponent<ComponentType<BuilderProps>>
> = {};
