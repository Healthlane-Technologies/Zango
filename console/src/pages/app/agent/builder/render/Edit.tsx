// Editors for the schema-driven renderer. Each writes through `edit` (a SpecEdit on the
// yaml Document), so the YAML keeps its comments and ordering.

import { useState, type KeyboardEvent, type ReactNode } from 'react';
import { cx, Icon, Switch } from '@/ui';
import { useBuilder } from '../context';
import { child, valueAt } from '../pointer';
import { branchFor, jsType, resolve, titleOf, ui, type Schema } from '../schema';

// ---- values ---------------------------------------------------------------------------

function typesOf(s: Schema): string[] {
	if (Array.isArray(s.type)) return s.type;
	if (s.type) return [s.type];
	if (s.properties || s.additionalProperties !== undefined) return ['object'];
	if (s.items) return ['array'];
	return [];
}

export function enumOptions(s: Schema): Array<{ value: unknown; label: string }> | null {
	if (s.enum) return s.enum.map((v) => ({ value: v, label: String(v) }));
	if (s.oneOf?.length && s.oneOf.every((o) => 'const' in o))
		return s.oneOf.map((o) => ({ value: o.const, label: o.title ?? String(o.const) }));
	return null;
}

/** The identities in a referenced collection: map keys, bare codes, single keys, or code/name. */
export function collectionKeys(doc: unknown, pointer: string | undefined): string[] {
	if (!pointer) return [];
	const target = valueAt(doc, pointer);
	if (Array.isArray(target))
		return target
			.map((item) => {
				if (item === null || typeof item !== 'object') return item === null ? '' : String(item);
				const o = item as Record<string, unknown>;
				const keys = Object.keys(o);
				if (keys.length === 1 && typeof o[keys[0]] === 'object') return keys[0];
				return String(o.code ?? o.name ?? o.id ?? keys[0] ?? '');
			})
			.filter(Boolean);
	if (target && typeof target === 'object') return Object.keys(target as object);
	return [];
}

/** A sensible empty value for `s`: required properties filled, everything else left out. */
export function defaultFor(root: Schema, node: Schema | undefined, depth = 0): unknown {
	const s = resolve(root, node);
	if ('default' in s) return s.default;
	const opts = enumOptions(s);
	if (opts?.length) return opts[0].value;
	const branches = s.anyOf ?? (s.oneOf && !enumOptions(s) ? s.oneOf : undefined);
	if (branches?.length) {
		const object = branches.map((b) => resolve(root, b)).find((b) => typesOf(b).includes('object'));
		return defaultFor(root, object ?? branches[0], depth);
	}
	const t = typesOf(s)[0];
	if (t === 'object') {
		const out: Record<string, unknown> = {};
		if (depth < 3)
			for (const key of s.required ?? [])
				out[key] = defaultFor(root, s.properties?.[key], depth + 1);
		return out;
	}
	if (t === 'array') return [];
	if (t === 'boolean') return false;
	if (t === 'integer' || t === 'number') return 0;
	return '';
}

/** The property an item is known by (code, name, id), if its schema has one. */
export function identityKey(root: Schema, item: Schema): string | undefined {
	const s = branchFor(root, item, {});
	const props = s.properties ?? {};
	return ['code', 'name', 'id', 'key'].find((k) => k in props);
}

// ---- small controls -------------------------------------------------------------------

function IconButton({
	icon,
	label,
	onClick,
	disabled,
	danger,
	className,
}: {
	icon: 'up' | 'x' | 'plus';
	label: string;
	onClick: () => void;
	disabled?: boolean;
	danger?: boolean;
	className?: string;
}) {
	return (
		<button
			type="button"
			className={cx('bv-ib', danger && 'danger', className)}
			aria-label={label}
			title={label}
			disabled={disabled}
			onClick={(e) => {
				e.stopPropagation();
				onClick();
			}}
		>
			<Icon name={icon} size={12} weight={2.2} />
		</button>
	);
}

/** Up / down / remove for an item of a list (or remove only, for a map entry). */
export function ItemActions({
	listPointer,
	index,
	count,
	pointer,
	noun = 'item',
}: {
	listPointer?: string;
	index?: number;
	count?: number;
	pointer: string;
	noun?: string;
}) {
	const { edit, editing } = useBuilder();
	if (!editing) return null;
	const inList = listPointer !== undefined && index !== undefined && count !== undefined;
	return (
		<span className="bv-acts">
			{inList && (
				<>
					<IconButton
						icon="up"
						label={`Move ${noun} up`}
						disabled={index === 0}
						onClick={() => edit({ op: 'move', path: listPointer, from: index, to: index - 1 })}
					/>
					<IconButton
						icon="up"
						className="rotate-180"
						label={`Move ${noun} down`}
						disabled={index === count - 1}
						onClick={() => edit({ op: 'move', path: listPointer, from: index, to: index + 1 })}
					/>
				</>
			)}
			<IconButton
				icon="x"
				danger
				label={`Remove ${noun}`}
				onClick={() => edit({ op: 'remove', path: pointer })}
			/>
		</span>
	);
}

/** "+ Add …" with an optional name/key input. */
export function AddRow({
	label,
	placeholder,
	needsName,
	options,
	onAdd,
}: {
	label: string;
	placeholder?: string;
	needsName?: boolean;
	/** Offer these names in a select instead of free text. */
	options?: string[];
	onAdd: (name: string) => void;
}) {
	const [open, setOpen] = useState(false);
	const [name, setName] = useState('');
	if (!needsName)
		return (
			<button type="button" className="bv-add" onClick={() => onAdd('')}>
				<Icon name="plus" size={12} weight={2.2} />
				{label}
			</button>
		);
	if (!open)
		return (
			<button type="button" className="bv-add" onClick={() => setOpen(true)}>
				<Icon name="plus" size={12} weight={2.2} />
				{label}
			</button>
		);
	const commit = () => {
		const v = name.trim();
		if (!v) return;
		onAdd(v);
		setName('');
		setOpen(false);
	};
	return (
		<span className="bv-addform">
			{options ? (
				<select
					className="select h-7 w-auto py-0 text-[12px]"
					value={name}
					autoFocus
					onChange={(e) => setName(e.target.value)}
					aria-label={placeholder ?? label}
				>
					<option value="">{placeholder ?? 'Choose…'}</option>
					{options.map((o) => (
						<option key={o} value={o}>
							{o}
						</option>
					))}
				</select>
			) : (
				<input
					className="input h-7 w-[200px] text-[12px]"
					value={name}
					autoFocus
					placeholder={placeholder}
					aria-label={placeholder ?? label}
					onChange={(e) => setName(e.target.value)}
					onKeyDown={(e: KeyboardEvent) => {
						if (e.key === 'Enter') commit();
						if (e.key === 'Escape') setOpen(false);
					}}
				/>
			)}
			<button type="button" className="btn btn-p btn-xs" onClick={commit} disabled={!name.trim()}>
				Add
			</button>
			<button type="button" className="btn btn-g btn-xs" onClick={() => setOpen(false)}>
				Cancel
			</button>
		</span>
	);
}

// ---- field editors --------------------------------------------------------------------

/** One scalar field: text, number, switch, enum select, or a reference picker. */
export function ScalarEditor({
	schema,
	value,
	pointer,
}: {
	schema: Schema;
	value: unknown;
	pointer: string;
}) {
	const { edit, doc } = useBuilder();
	const set = (v: unknown) => edit({ op: 'set', path: pointer, value: v });
	const types = typesOf(schema);
	const label = titleOf(schema) || 'Value';

	if (typeof value === 'boolean' || (value == null && types[0] === 'boolean'))
		return <Switch checked={!!value} onChange={set} label={label} />;

	const options = enumOptions(schema);
	const refs = ui(schema).ref ? collectionKeys(doc, ui(schema).ref) : null;
	if (options || refs) {
		const list = options ?? refs!.map((r) => ({ value: r, label: r }));
		const known = list.some((o) => o.value === value);
		return (
			<select
				className="select h-8 w-auto min-w-[160px] max-w-full"
				aria-label={label}
				value={known ? String(value) : '__cur'}
				onChange={(e) =>
					set(list.find((o) => String(o.value) === e.target.value)?.value ?? e.target.value)
				}
			>
				{!known && (
					<option value="__cur">
						{value == null || value === '' ? 'Choose…' : `${String(value)} (not listed)`}
					</option>
				)}
				{list.map((o) => (
					<option key={String(o.value)} value={String(o.value)}>
						{o.label}
					</option>
				))}
			</select>
		);
	}

	if (
		typeof value === 'number' ||
		(value == null && (types[0] === 'integer' || types[0] === 'number'))
	)
		return (
			<input
				className="input h-8 w-[140px]"
				type="number"
				aria-label={label}
				value={value == null ? '' : String(value)}
				onChange={(e) => {
					const n = e.target.value === '' ? null : Number(e.target.value);
					if (n === null || !Number.isNaN(n)) set(n);
				}}
			/>
		);

	return (
		<input
			className="input h-8"
			aria-label={label}
			value={value == null ? '' : String(value)}
			onChange={(e) => set(e.target.value)}
		/>
	);
}

export function TextEditor({
	schema,
	value,
	pointer,
}: {
	schema: Schema;
	value: unknown;
	pointer: string;
}) {
	const { edit } = useBuilder();
	return (
		<textarea
			className="textarea text-[12.5px]"
			rows={3}
			aria-label={titleOf(schema) || 'Text'}
			value={value == null ? '' : String(value)}
			onChange={(e) => edit({ op: 'set', path: pointer, value: e.target.value })}
		/>
	);
}

/** A list of short values as removable chips, with an add control. */
export function TagsEditor({
	schema,
	value,
	pointer,
}: {
	schema: Schema;
	value: unknown[];
	pointer: string;
}) {
	const { edit, doc, root } = useBuilder();
	const item = resolve(root, schema.items);
	const options = enumOptions(item);
	const refs = ui(schema).ref ?? ui(item).ref;
	const pool = options?.map((o) => String(o.value)) ?? (refs ? collectionKeys(doc, refs) : null);
	const unused = pool?.filter((p) => !value.map(String).includes(p));
	const numeric = typesOf(item)[0] === 'integer' || typesOf(item)[0] === 'number';
	return (
		<span className="bv-tags edit">
			{value.map((v, i) => (
				<span key={i} className={cx('bv-chip', refs && 'ref')}>
					{String(v)}
					<button
						type="button"
						className="bv-chipx"
						aria-label={`Remove ${String(v)}`}
						onClick={() => edit({ op: 'remove', path: child(pointer, i) })}
					>
						<Icon name="x" size={10} weight={2.4} />
					</button>
				</span>
			))}
			<AddRow
				label="Add"
				needsName
				placeholder={pool ? 'Choose…' : 'Type and press Enter'}
				options={unused ?? undefined}
				onAdd={(v) => edit({ op: 'add', path: pointer, value: numeric ? Number(v) : v })}
			/>
		</span>
	);
}

/** For an object: "+ Add a setting" offering the schema's properties it doesn't have yet. */
export function AddProperty({
	schema,
	value,
	pointer,
}: {
	schema: Schema;
	value: Record<string, unknown>;
	pointer: string;
}) {
	const { edit, root, editing } = useBuilder();
	if (!editing) return null;
	const props = schema.properties ?? {};
	const missing = Object.keys(props).filter(
		(k) => !(k in value) && !ui(resolve(root, props[k])).hidden,
	);
	if (!missing.length) return null;
	const byTitle = new Map(missing.map((k) => [titleOf(resolve(root, props[k]), k), k]));
	return (
		<AddRow
			label="Add a setting"
			needsName
			placeholder="Choose a setting…"
			options={[...byTitle.keys()]}
			onAdd={(title) => {
				const key = byTitle.get(title) ?? title;
				edit({ op: 'add', path: child(pointer, key), value: defaultFor(root, props[key]) });
			}}
		/>
	);
}

/** A field that exists in the schema but isn't set: shows an editor that creates it. */
export function isScalarSchema(root: Schema, s: Schema): boolean {
	const t = typesOf(branchFor(root, s, undefined));
	return !t.length || ['string', 'number', 'integer', 'boolean'].includes(t[0]);
}

export function Hint({ children }: { children: ReactNode }) {
	return <span className="bv-hint">{children}</span>;
}

export { jsType };
