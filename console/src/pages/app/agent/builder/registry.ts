// Extension point: a template can ship its own builder UI (e.g. a Journey Studio port for
// PSP) without the generic panel changing. Keyed by template slug; empty for now.

import type { ComponentType, LazyExoticComponent } from 'react';
import type { Requirement, RequirementSpec, TemplateBuilderDef } from '@/api/agentMode';
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
}

export const builderOverrides: Record<
	string,
	LazyExoticComponent<ComponentType<BuilderProps>>
> = {};
