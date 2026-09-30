import { createContext, useContext } from 'react';
import type { SpecIssue } from '@/api/agentMode';
import type { Schema } from './schema';

/** What every rendered node needs to know: the schema, the document, and what to mark. */
export interface BuilderCtx {
	root: Schema;
	doc: unknown;
	/** Issues keyed by the exact pointer they're on. */
	issuesAt: Map<string, SpecIssue[]>;
	/** Pointers with an issue on them or below them. */
	issueWithin: Set<string>;
	/** Pointers changed by the last turn, and every ancestor of one. */
	changedWithin: Set<string>;
	changedExact: Set<string>;
	isOpen: (pointer: string, fallback: boolean) => boolean;
	toggle: (pointer: string, fallback: boolean) => void;
}

export const BuilderContext = createContext<BuilderCtx | null>(null);

export function useBuilder(): BuilderCtx {
	const ctx = useContext(BuilderContext);
	if (!ctx) throw new Error('useBuilder outside a TemplateBuilderPanel');
	return ctx;
}
