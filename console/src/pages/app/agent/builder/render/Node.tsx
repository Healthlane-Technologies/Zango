// Schema-driven view of a spec value, read-only unless the section is in edit mode. Every
// node carries id="f:<pointer>" so the checks list and the changed chip can scroll to it.

import { memo, useState, type ReactNode } from 'react';
import { cx, Icon } from '@/ui';
import { useBuilder } from '../context';
import { child } from '../pointer';
import {
	branchFor,
	childSchema,
	enumLabel,
	isSingleKeyMap,
	kindOf,
	resolve,
	titleOf,
	ui,
	type Kind,
	type Schema,
} from '../schema';
import { fill } from '../template';
import {
	AddProperty,
	AddRow,
	collectionKeys,
	defaultFor,
	identityKey,
	isScalarSchema,
	ItemActions,
	ScalarEditor,
	TagsEditor,
	TextEditor,
} from './Edit';

interface NodeProps {
	schema: Schema;
	value: unknown;
	pointer: string;
	depth: number;
}

const SIMPLE: Kind[] = ['scalar', 'tags', 'text', 'unknown'];

function isEmpty(v: unknown): boolean {
	if (v === undefined || v === null || v === '') return true;
	if (Array.isArray(v)) return v.length === 0;
	if (typeof v === 'object') return Object.keys(v as object).length === 0;
	return false;
}

/** Inline messages for issues sitting exactly on this pointer. */
export function Issues({ pointer }: { pointer: string }) {
	const { issuesAt } = useBuilder();
	const list = issuesAt.get(pointer);
	if (!list?.length) return null;
	return (
		<div className="bv-issues">
			{list.map((i, n) => (
				<div key={n} className={cx('bv-issue', i.level === 'error' ? 'err' : 'wrn')}>
					<Icon name="alert" size={12} />
					{i.message}
				</div>
			))}
		</div>
	);
}

function Marks({ pointer }: { pointer: string }) {
	const { issueWithin, changedWithin } = useBuilder();
	return (
		<>
			{changedWithin.has(pointer) && <i className="bv-dot chg" title="Changed by the agent" />}
			{issueWithin.has(pointer) && <i className="bv-dot err" title="Needs attention" />}
		</>
	);
}

export const NodeView = memo(function NodeView({ schema, value, pointer, depth }: NodeProps) {
	const { root, editing } = useBuilder();
	const s = branchFor(root, schema, value);
	const kind = kindOf(root, s, value);
	if (editing) {
		if (kind === 'scalar' || (kind === 'tags' && !Array.isArray(value)))
			return <ScalarEditor schema={s} value={value} pointer={pointer} />;
		if (kind === 'text') return <TextEditor schema={s} value={value} pointer={pointer} />;
		if (kind === 'tags')
			return <TagsEditor schema={s} value={value as unknown[]} pointer={pointer} />;
		if (kind === 'unknown' && isScalarSchema(root, s))
			return <ScalarEditor schema={s} value={value} pointer={pointer} />;
	}
	switch (kind) {
		case 'scalar':
			return <Scalar schema={s} value={value} />;
		case 'text':
			return <p className="bv-prose">{String(value ?? '')}</p>;
		case 'tags':
			return <Tags schema={s} value={value} />;
		case 'keyed':
			return <KeyedList schema={s} value={value as unknown[]} pointer={pointer} depth={depth} />;
		case 'map':
			return (
				<MapCards
					schema={s}
					value={value as Record<string, unknown>}
					pointer={pointer}
					depth={depth}
				/>
			);
		case 'cards':
			return <Cards schema={s} value={value as unknown[]} pointer={pointer} depth={depth} />;
		case 'object':
			return (
				<ObjectRows
					schema={s}
					value={value as Record<string, unknown>}
					pointer={pointer}
					depth={depth}
				/>
			);
		default:
			return <span className="bv-none">—</span>;
	}
});

function Scalar({ schema, value }: { schema: Schema; value: unknown }) {
	if (typeof value === 'boolean') return <span className="bv-val">{value ? 'Yes' : 'No'}</span>;
	const text = schema.enum || schema.oneOf ? enumLabel(schema, value) : String(value);
	if (ui(schema).ref) return <span className="bv-chip ref">{text}</span>;
	if (schema.enum) return <span className="bv-chip enum">{text}</span>;
	return <span className="bv-val">{text}</span>;
}

function Tags({ schema, value }: { schema: Schema; value: unknown }) {
	const items = Array.isArray(value) ? value : value === undefined || value === null ? [] : [value];
	if (!items.length) return <span className="bv-none">—</span>;
	const ref = !!ui(schema).ref;
	return (
		<span className="bv-tags">
			{items.map((v, i) => (
				<span key={i} className={cx('bv-chip', ref && 'ref')}>
					{typeof v === 'object' ? JSON.stringify(v) : String(v)}
				</span>
			))}
		</span>
	);
}

/** Labelled rows for an object's properties, schema order first, then anything extra. */
function ObjectRows({
	schema,
	value,
	pointer,
	depth,
}: NodeProps & { value: Record<string, unknown> }) {
	const { root, editing } = useBuilder();
	const known = Object.keys(schema.properties ?? {});
	const required = new Set(schema.required ?? []);
	const keys = [
		...known.filter((k) => k in value),
		...Object.keys(value).filter((k) => !known.includes(k)),
	];
	if (!keys.length)
		return editing ? (
			<AddProperty schema={schema} value={value} pointer={pointer} />
		) : (
			<span className="bv-none">No settings</span>
		);
	return (
		<dl className="bv-rows">
			{keys.map((k) => {
				const ptr = child(pointer, k);
				const cs = childSchema(root, schema, k, value);
				const cv = value[k];
				const kind = kindOf(root, branchFor(root, cs, cv), cv);
				const label = titleOf(cs, k);
				if (SIMPLE.includes(kind)) {
					return (
						<div key={k} className="bv-row" id={`f:${ptr}`} data-path={ptr}>
							<dt title={cs.description}>
								{label}
								<Marks pointer={ptr} />
							</dt>
							<dd>
								<span className="flex items-start gap-1.5">
									<span className="min-w-0 flex-1">
										<NodeView schema={cs} value={cv} pointer={ptr} depth={depth + 1} />
									</span>
									{!required.has(k) && (
										<ItemActions pointer={ptr} noun={label.toLowerCase() || 'setting'} />
									)}
								</span>
								<Issues pointer={ptr} />
							</dd>
						</div>
					);
				}
				return (
					<div key={k} className="bv-block" id={`f:${ptr}`} data-path={ptr}>
						<div className="bv-bl" title={cs.description}>
							{label}
							{Array.isArray(cv) && <span className="ct">{cv.length}</span>}
							<Marks pointer={ptr} />
							{!required.has(k) && (
								<span className="ml-auto">
									<ItemActions pointer={ptr} noun={label.toLowerCase() || 'setting'} />
								</span>
							)}
						</div>
						<Issues pointer={ptr} />
						<NodeView schema={cs} value={cv} pointer={ptr} depth={depth + 1} />
					</div>
				);
			})}
			{editing && (
				<div className="bv-row">
					<AddProperty schema={schema} value={value} pointer={pointer} />
				</div>
			)}
		</dl>
	);
}

interface CardProps {
	pointer: string;
	title: ReactNode;
	summary?: string;
	depth: number;
	defaultOpen: boolean;
	children?: ReactNode;
	/** Nothing to expand: render the header only. */
	flat?: boolean;
	/** Edit controls, shown beside the header. */
	actions?: ReactNode;
}

export function Card({ pointer, title, summary, defaultOpen, children, flat, actions }: CardProps) {
	const { isOpen, toggle, issueWithin, changedWithin } = useBuilder();
	const open = !flat && isOpen(pointer, defaultOpen);
	return (
		<div
			className={cx(
				'bv-card',
				open && 'open',
				changedWithin.has(pointer) && 'chg',
				issueWithin.has(pointer) && 'err',
			)}
			id={`f:${pointer}`}
			data-path={pointer}
		>
			<div className="bv-chrow">
				<button
					type="button"
					className="bv-ch"
					aria-expanded={flat ? undefined : open}
					onClick={flat ? undefined : () => toggle(pointer, defaultOpen)}
					disabled={flat}
				>
					{!flat && <Icon name="back" size={12} className="bv-chev" />}
					<b>{title}</b>
					{summary && <span className="bv-sum">{summary}</span>}
					<span className="ml-auto flex items-center gap-1">
						<Marks pointer={pointer} />
					</span>
				</button>
				{actions}
			</div>
			{open && (
				<div className="bv-cb">
					<Issues pointer={pointer} />
					{children}
				</div>
			)}
		</div>
	);
}

const openByDefault = (depth: number, count: number) => depth === 0 && count <= 4;

/** A list of objects: one card each, titled by x-ui.itemTitle. */
function Cards({ schema, value, pointer, depth }: NodeProps & { value: unknown[] }) {
	const { root, editing, edit } = useBuilder();
	const itemSchema = resolve(root, schema.items);
	const idKey = identityKey(root, itemSchema);
	const noun = (titleOf(itemSchema) || 'item').toLowerCase();
	return (
		<div className="bv-cards">
			{value.map((item, i) => {
				const ptr = child(pointer, i);
				const s = branchFor(root, itemSchema, item);
				const hint = { ...ui(schema), ...ui(s) };
				const named = item as Record<string, unknown> | null;
				const title =
					fill(hint.itemTitle, item) ||
					String(named?.code ?? named?.name ?? named?.id ?? '') ||
					`${titleOf(s) || 'Item'} ${i + 1}`;
				return (
					<Card
						key={i}
						pointer={ptr}
						title={title}
						summary={fill(ui(s).summary, item)}
						depth={depth}
						defaultOpen={openByDefault(depth, value.length)}
						actions={
							<ItemActions
								listPointer={pointer}
								index={i}
								count={value.length}
								pointer={ptr}
								noun={noun}
							/>
						}
					>
						<NodeView schema={s} value={item} pointer={ptr} depth={depth + 1} />
					</Card>
				);
			})}
			{editing && (
				<AddRow
					label={`Add ${noun}`}
					needsName={!!idKey}
					placeholder={idKey ? `New ${noun} ${idKey}` : undefined}
					onAdd={(name) => {
						const base = defaultFor(root, itemSchema);
						const value =
							idKey && base && typeof base === 'object' && !Array.isArray(base)
								? { ...(base as object), [idKey]: name }
								: base;
						edit({ op: 'add', path: pointer, value });
					}}
				/>
			)}
		</div>
	);
}

/** True when a keyed entry's value is small enough to show inline on its chip. */
function compact(v: unknown): boolean {
	if (v === undefined || v === null) return true;
	if (typeof v !== 'object') return true;
	if (Array.isArray(v)) return v.every((x) => typeof x !== 'object');
	const entries = Object.entries(v as Record<string, unknown>);
	return entries.length <= 2 && entries.every(([, x]) => typeof x !== 'object');
}

function inlineDetail(schema: Schema, v: unknown, root: Schema): string {
	if (v === undefined || v === null) return '';
	if (typeof v !== 'object') return String(v);
	if (Array.isArray(v)) return v.join(', ');
	return Object.entries(v as Record<string, unknown>)
		.map(([k, x]) => {
			const t = titleOf(childSchema(root, schema, k, v), k);
			return x === true ? t : x === false ? '' : `${t}: ${String(x)}`;
		})
		.filter(Boolean)
		.join(' · ');
}

/**
 * A list of single-key maps (`- name: {…}`), optionally mixed with bare codes (`- active`).
 * Small entries render as chips; entries with substance render as cards titled by their key.
 */
function KeyedList({ schema, value, pointer, depth }: NodeProps & { value: unknown[] }) {
	const { root, editing, edit, doc } = useBuilder();
	const itemSchema = resolve(root, schema.items);
	const entries = value.map((item, i) => {
		const ptr = child(pointer, i);
		if (!isSingleKeyMap(item))
			return {
				ptr,
				key: typeof item === 'object' ? '' : String(item),
				v: undefined,
				item,
				bare: typeof item !== 'object',
			};
		const key = Object.keys(item)[0];
		return { ptr, key, v: item[key], item, bare: false };
	});
	const hint = { ...ui(itemSchema), ...ui(schema) };
	const noun =
		(hint.keyTitle ?? titleOf(itemSchema) ?? 'entry').replace(/ name$/i, '').toLowerCase() ||
		'entry';
	const existing = new Set(entries.map((e) => e.key));
	const keyOptions = hint.keyRef
		? collectionKeys(doc, hint.keyRef).filter((k) => !existing.has(k))
		: undefined;
	const adder = editing && (
		<AddRow
			label={`Add ${noun}`}
			needsName
			placeholder={hint.keyRef ? 'Choose…' : `New ${noun}`}
			options={keyOptions}
			onAdd={(name) => {
				if (hint.bareAllowed) return edit({ op: 'add', path: pointer, value: name });
				const branch = branchFor(root, itemSchema, { [name]: {} });
				const vs = childSchema(root, branch, name, { [name]: {} });
				edit({ op: 'add', path: pointer, value: { [name]: defaultFor(root, vs) } });
			}}
		/>
	);
	const allCompact = entries.every((e) => e.bare || compact(e.v));
	if (allCompact && !editing) {
		return (
			<ul className="bv-keyed">
				{entries.map((e, i) => {
					const s = e.bare
						? undefined
						: childSchema(root, branchFor(root, itemSchema, e.item), e.key, e.item);
					const detail = s ? inlineDetail(s, e.v, root) : '';
					return (
						<li key={i} id={`f:${e.ptr}`} data-path={e.ptr}>
							<span className={cx('bv-chip', hint.keyRef && 'ref')}>{e.key || '—'}</span>
							{detail && <span className="bv-sum">{detail}</span>}
							<Marks pointer={e.ptr} />
							<Issues pointer={e.ptr} />
						</li>
					);
				})}
			</ul>
		);
	}
	return (
		<div className="bv-cards">
			{entries.map((e, i) => {
				const branch = branchFor(root, itemSchema, e.item);
				const s = e.bare ? branch : childSchema(root, branch, e.key, e.item);
				const title = fill(hint.itemTitle, e.v, e.key) || e.key || `Item ${i + 1}`;
				const body =
					e.bare || isEmpty(e.v) ? null : (
						<div id={`f:${child(e.ptr, e.key)}`} data-path={child(e.ptr, e.key)}>
							<NodeView schema={s} value={e.v} pointer={child(e.ptr, e.key)} depth={depth + 1} />
						</div>
					);
				return (
					<Card
						key={i}
						pointer={e.ptr}
						title={title}
						summary={fill(ui(s).summary, e.v, e.key) || (body ? '' : e.bare ? '' : 'No settings')}
						depth={depth}
						defaultOpen={openByDefault(depth, entries.length)}
						flat={!body}
						actions={
							<ItemActions
								listPointer={pointer}
								index={i}
								count={entries.length}
								pointer={e.ptr}
								noun={noun}
							/>
						}
					>
						{body}
					</Card>
				);
			})}
			{adder}
		</div>
	);
}

/** An object keyed by name (additionalProperties): one card per entry. */
function MapCards({
	schema,
	value,
	pointer,
	depth,
}: NodeProps & { value: Record<string, unknown> }) {
	const { root, editing, edit, doc } = useBuilder();
	const keys = Object.keys(value);
	const hint = ui(schema);
	const noun = (hint.keyTitle ?? 'entry').replace(/ name$/i, '').toLowerCase();
	const keyOptions = hint.keyRef
		? collectionKeys(doc, hint.keyRef).filter((k) => !(k in value))
		: undefined;
	const adder = editing && (
		<AddRow
			label={`Add ${noun}`}
			needsName
			placeholder={hint.keyRef ? 'Choose…' : `New ${noun}`}
			options={keyOptions}
			onAdd={(name) =>
				edit({
					op: 'add',
					path: child(pointer, name),
					value: defaultFor(root, childSchema(root, schema, name, value)),
				})
			}
		/>
	);
	if (!keys.length) return editing ? adder : <span className="bv-none">None yet</span>;
	return (
		<div className="bv-cards">
			{keys.map((k) => {
				const ptr = child(pointer, k);
				const s = childSchema(root, schema, k, value);
				const v = value[k];
				const empty = isEmpty(v);
				return (
					<Card
						key={k}
						pointer={ptr}
						title={fill(ui(schema).itemTitle ?? '{key}', v, k) || k}
						summary={fill(ui(s).summary, v, k) || (empty ? 'No settings' : '')}
						depth={depth}
						defaultOpen={openByDefault(depth, keys.length)}
						flat={empty && !editing}
						actions={
							editing && (
								<span className="bv-acts">
									<RenameKey pointer={ptr} current={k} />
									<ItemActions pointer={ptr} noun={noun} />
								</span>
							)
						}
					>
						<NodeView schema={s} value={v} pointer={ptr} depth={depth + 1} />
					</Card>
				);
			})}
			{adder}
		</div>
	);
}

/** Rename a map key in place. */
function RenameKey({ pointer, current }: { pointer: string; current: string }) {
	const { edit } = useBuilder();
	const [open, setOpen] = useState(false);
	const [name, setName] = useState(current);
	if (!open)
		return (
			<button type="button" className="bv-txtbtn" onClick={() => setOpen(true)}>
				Rename
			</button>
		);
	const commit = () => {
		if (name.trim() && name.trim() !== current)
			edit({ op: 'rename', path: pointer, to: name.trim() });
		setOpen(false);
	};
	return (
		<input
			className="input h-6 w-[150px] text-[12px]"
			value={name}
			autoFocus
			aria-label={`Rename ${current}`}
			onChange={(e) => setName(e.target.value)}
			onBlur={commit}
			onKeyDown={(e) => {
				if (e.key === 'Enter') commit();
				if (e.key === 'Escape') setOpen(false);
			}}
		/>
	);
}
