import { useMemo, useState } from 'react';
import type { Requirement } from '@/api/agentMode';
import { Badge, Button, Card, CardHeader, EmptyState, Segmented } from '@/ui';
import { Markdown } from './Markdown';
import { REQUIREMENT_STATUS, cost } from './rounds';
import { specHighlights, type GroupKey } from './specHighlights';

// These say what the app is *not*: worth showing, never as loud as the scope.
const MUTED: GroupKey[] = ['excluded', 'assumptions'];

const SUMMARY_LABEL: Partial<Record<GroupKey, string>> = {
	entities: 'Records',
	roles: 'Roles',
	stages: 'Stages',
	screens: 'Screens',
	automatic: 'Automations',
};

interface Props {
	requirement: Requirement;
	/** The newest round, still being agreed: its spec can be edited. */
	editable: boolean;
	/** Local copy of the spec while editing; null when there are no unsaved edits. */
	draft: string | null;
	onDraft: (v: string | null) => void;
	onSave: () => void;
	saving: boolean;
}

export function RequirementsPanel({
	requirement: r,
	editable,
	draft,
	onDraft,
	onSave,
	saving,
}: Props) {
	const [view, setView] = useState<'highlights' | 'document'>('highlights');
	const [editing, setEditing] = useState(false);
	const spec = draft ?? r.spec_markdown;
	const h = useMemo(() => specHighlights(spec), [spec]);
	const [tone, statusLabel] = REQUIREMENT_STATUS[r.status];
	const dirty = draft !== null && draft !== r.spec_markdown;
	const meta = [
		`Spec v${r.spec_version}`,
		`${r.turns} turn${r.turns === 1 ? '' : 's'}`,
		cost(r.total_cost_usd),
	]
		.filter(Boolean)
		.join(' · ');

	if (!spec.trim()) {
		return (
			<div className="card">
				<EmptyState
					title={r.is_thinking ? 'The agent is working out what you need' : 'No requirements yet'}
				>
					Once the requirement is clear it appears here for review. Nothing is built until you
					approve it.
				</EmptyState>
			</div>
		);
	}

	const scoped = h.groups.filter((g) => !MUTED.includes(g.key));
	const showDocument = view === 'document' || editing || !h.groups.length;

	return (
		<>
			<div className="rq-top">
				<h3 className="min-w-0 truncate">{h.title || r.title}</h3>
				<Badge tone={tone} dot>
					{statusLabel}
				</Badge>
				<span className="text-[12px] text-t3">{meta}</span>
				<div className="r">
					{h.groups.length > 0 && !editing && (
						<Segmented
							label="Requirement view"
							value={view}
							onChange={setView}
							options={[
								{ value: 'highlights', label: 'Highlights' },
								{ value: 'document', label: 'Full spec' },
							]}
						/>
					)}
					{editable && (
						<Button
							size="sm"
							icon={editing ? 'eye' : 'file'}
							onClick={() => {
								if (!editing && draft === null) onDraft(r.spec_markdown);
								setEditing(!editing);
							}}
						>
							{editing ? 'Preview' : 'Edit'}
						</Button>
					)}
				</div>
			</div>
			{h.summary && !showDocument && <p className="mb-3.5 text-t2">{h.summary}</p>}

			{showDocument ? (
				<div className="card">
					{editing ? (
						<textarea
							className="spec-edit"
							value={spec}
							onChange={(e) => onDraft(e.target.value)}
							aria-label="Requirement spec (markdown)"
							autoFocus
						/>
					) : (
						<Markdown className="spec-doc" text={spec} />
					)}
				</div>
			) : (
				<>
					{scoped.length > 1 && (
						<div className="sumstrip">
							{scoped.map((g) => (
								<div key={g.key}>
									<small>{SUMMARY_LABEL[g.key] ?? g.label}</small>
									<b>{g.items.length}</b>
								</div>
							))}
						</div>
					)}
					{h.groups.map((g) => {
						const muted = MUTED.includes(g.key);
						return (
							<Card key={g.key} className="rsec">
								<CardHeader
									title={g.label}
									count={g.items.length > 1 ? g.items.length : undefined}
								/>
								{g.items.map((it, i) => (
									<div key={`${it.name}-${i}`} className={muted ? 'ritem muted' : 'ritem'}>
										<span className="n">{i + 1}</span>
										<span className="tx">
											{it.name}
											{it.detail && <small>{it.detail}</small>}
										</span>
									</div>
								))}
							</Card>
						);
					})}
				</>
			)}

			{editable && dirty && (
				<div className="sticky bottom-0 mt-4 flex items-center gap-3 rounded-[10px] border border-border bg-panel px-4 py-2.5 shadow-pop">
					<span className="text-t1">Unsaved edits to the spec</span>
					<div className="ml-auto flex gap-2">
						<Button
							size="sm"
							disabled={saving}
							onClick={() => {
								onDraft(null);
								setEditing(false);
							}}
						>
							Discard
						</Button>
						<Button size="sm" variant="primary" loading={saving} onClick={onSave}>
							Save edits
						</Button>
					</div>
				</div>
			)}
		</>
	);
}
