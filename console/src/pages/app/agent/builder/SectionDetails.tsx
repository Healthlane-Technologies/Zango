import { Fragment } from 'react';
import { Button } from '@/ui';
import { useBuilder } from './context';
import { child, parsePointer, valueAt } from './pointer';
import { Issues, NodeView } from './render/Node';
import { branchFor, subschemaAt, titleOf, ui } from './schema';
import { isSectionEmpty, type BuilderSection } from './sections';
import { fill } from './template';

/** One builder section, read-only: its fields, or its list, or per-parent child lists. */
export function SectionDetails({
	section,
	onExpandAll,
	onCollapseAll,
}: {
	section: BuilderSection;
	onExpandAll: () => void;
	onCollapseAll: () => void;
}) {
	const { root, doc } = useBuilder();
	const empty = isSectionEmpty(section, doc);

	let body;
	if (empty) {
		body = (
			<div className="bv-empty">
				<b>Not filled in yet</b>
				{section.hint && <p>{section.hint}</p>}
			</div>
		);
	} else if (section.item) {
		const parents = valueAt(doc, section.pointer);
		const parentSchema = subschemaAt(root, section.pointer, doc);
		body = (
			<div className="grid gap-4">
				{(Array.isArray(parents) ? parents : []).map((p, i) => {
					const pp = child(section.pointer, i);
					const itemSchema = branchFor(root, subschemaAt(root, pp, doc), p);
					const ptr = child(pp, section.item!);
					const v = (p as Record<string, unknown> | null)?.[section.item!];
					const title =
						fill({ ...ui(parentSchema), ...ui(itemSchema) }.itemTitle, p) || `#${i + 1}`;
					return (
						<div key={i} className="bv-group" id={`f:${ptr}`} data-path={ptr}>
							<div className="bv-gh">{title}</div>
							<Issues pointer={ptr} />
							{v === undefined || (Array.isArray(v) && !v.length) ? (
								<span className="bv-none">None</span>
							) : (
								<NodeView schema={subschemaAt(root, ptr, doc)} value={v} pointer={ptr} depth={0} />
							)}
						</div>
					);
				})}
				{section.fields?.length ? renderFields(section.fields) : null}
			</div>
		);
	} else if (section.fields?.length) {
		body = <div className="grid gap-4">{renderFields(section.fields)}</div>;
	} else {
		const v = valueAt(doc, section.pointer);
		body = (
			<div id={`f:${section.pointer}`} data-path={section.pointer}>
				<Issues pointer={section.pointer} />
				<NodeView
					schema={subschemaAt(root, section.pointer, doc)}
					value={v}
					pointer={section.pointer}
					depth={0}
				/>
			</div>
		);
	}

	function renderFields(fields: string[]) {
		return fields.map((f) => {
			const v = valueAt(doc, f);
			if (v === undefined) return null;
			const s = subschemaAt(root, f, doc);
			const key = parsePointer(f).pop();
			const simple = v === null || typeof v !== 'object';
			return (
				<Fragment key={f}>
					{simple ? (
						<dl className="bv-rows">
							<div className="bv-row" id={`f:${f}`} data-path={f}>
								<dt title={s.description}>{titleOf(s, key)}</dt>
								<dd>
									<NodeView schema={s} value={v} pointer={f} depth={0} />
									<Issues pointer={f} />
								</dd>
							</div>
						</dl>
					) : (
						<div className="bv-group" id={`f:${f}`} data-path={f}>
							<div className="bv-gh" title={s.description}>
								{titleOf(s, key)}
								{Array.isArray(v) && <span className="ct">{v.length}</span>}
							</div>
							<Issues pointer={f} />
							<NodeView schema={s} value={v} pointer={f} depth={0} />
						</div>
					)}
				</Fragment>
			);
		});
	}

	return (
		<div className="bv-sec">
			<div className="bv-sh">
				<div className="min-w-0">
					<h3>{section.title}</h3>
					{section.hint && !empty && <p>{section.hint}</p>}
				</div>
				{!empty && (
					<div className="ml-auto flex shrink-0 gap-1">
						<Button size="xs" variant="ghost" onClick={onExpandAll}>
							Expand all
						</Button>
						<Button size="xs" variant="ghost" onClick={onCollapseAll}>
							Collapse all
						</Button>
					</div>
				)}
			</div>
			{body}
		</div>
	);
}
