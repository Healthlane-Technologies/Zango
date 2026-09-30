// Read-only, schema-driven view of a spec value. Every node carries id="f:<pointer>" so the
// checks list and the changed chip can scroll to it; F3 swaps these views for editors.

import { memo, type ReactNode } from 'react';
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
	const { root } = useBuilder();
	const s = branchFor(root, schema, value);
	switch (kindOf(root, s, value)) {
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
	const { root } = useBuilder();
	const known = Object.keys(schema.properties ?? {});
	const keys = [
		...known.filter((k) => k in value),
		...Object.keys(value).filter((k) => !known.includes(k)),
	];
	if (!keys.length) return <span className="bv-none">No settings</span>;
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
								<NodeView schema={cs} value={cv} pointer={ptr} depth={depth + 1} />
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
						</div>
						<Issues pointer={ptr} />
						<NodeView schema={cs} value={cv} pointer={ptr} depth={depth + 1} />
					</div>
				);
			})}
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
}

export function Card({ pointer, title, summary, defaultOpen, children, flat }: CardProps) {
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
	const { root } = useBuilder();
	const itemSchema = resolve(root, schema.items);
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
					>
						<NodeView schema={s} value={item} pointer={ptr} depth={depth + 1} />
					</Card>
				);
			})}
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
	const { root } = useBuilder();
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
	const allCompact = entries.every((e) => e.bare || compact(e.v));
	if (allCompact) {
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
					>
						{body}
					</Card>
				);
			})}
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
	const { root } = useBuilder();
	const keys = Object.keys(value);
	if (!keys.length) return <span className="bv-none">None yet</span>;
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
						flat={empty}
					>
						<NodeView schema={s} value={v} pointer={ptr} depth={depth + 1} />
					</Card>
				);
			})}
		</div>
	);
}
