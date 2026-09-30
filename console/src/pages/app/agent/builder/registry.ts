// Extension point: a template can ship its own builder UI (e.g. a Journey Studio port for
// PSP) without the generic panel changing. Keyed by template slug; empty for now.

import type { ComponentType, LazyExoticComponent } from 'react';
import type { Requirement, RequirementSpec, TemplateBuilderDef } from '@/api/agentMode';

export interface BuilderProps {
	appId: string;
	requirement: Requirement;
	builder: TemplateBuilderDef;
	spec: RequirementSpec;
	/** Pointers changed by the last agent turn (server-reported, or diffed as a fallback). */
	changed: string[];
}

export const builderOverrides: Record<
	string,
	LazyExoticComponent<ComponentType<BuilderProps>>
> = {};
