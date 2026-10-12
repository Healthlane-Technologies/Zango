import type { ReactNode } from 'react';
import { NavLink } from 'react-router-dom';
import { cx } from './cx';
import { Icon } from './Icon';

export interface Option<V extends string> {
	value: V;
	label: ReactNode;
}

export function Segmented<V extends string>({
	options,
	value,
	onChange,
	label,
}: {
	options: Option<V>[];
	value: V;
	onChange: (v: V) => void;
	label: string;
}) {
	return (
		<div className="seg" role="radiogroup" aria-label={label}>
			{options.map((o) => (
				<button
					key={o.value}
					type="button"
					role="radio"
					aria-checked={o.value === value}
					className={cx(o.value === value && 'on')}
					onClick={() => onChange(o.value)}
				>
					{o.label}
				</button>
			))}
		</div>
	);
}

export interface TabItem<V extends string> {
	value: V;
	label: ReactNode;
	count?: number;
	disabled?: boolean;
	/** A small dot: something on this tab needs the user. */
	attention?: boolean;
}

/** Tabs held in local state. */
export function Tabs<V extends string>({
	items,
	value,
	onChange,
	className,
}: {
	items: TabItem<V>[];
	value: V;
	onChange: (v: V) => void;
	className?: string;
}) {
	return (
		<div className={cx('tabs', className)} role="tablist">
			{items.map((t) => (
				<button
					key={t.value}
					type="button"
					role="tab"
					aria-selected={t.value === value}
					disabled={t.disabled}
					className={cx(t.value === value && 'on')}
					onClick={() => onChange(t.value)}
				>
					{t.label}
					{t.count != null && <span className="ct">{t.count}</span>}
					{t.attention && <span className="tab-dot" title="Needs your attention" />}
				</button>
			))}
		</div>
	);
}

/** Tabs that are routes; the active tab follows the URL. */
export function RouteTabs({
	items,
	className,
}: {
	items: Array<{ to: string; label: ReactNode; end?: boolean }>;
	className?: string;
}) {
	return (
		<nav className={cx('tabs', className)}>
			{items.map((t) => (
				<NavLink
					key={t.to}
					to={t.to}
					end={t.end}
					className={({ isActive }) => cx(isActive && 'on')}
				>
					{t.label}
				</NavLink>
			))}
		</nav>
	);
}

export function SearchInput({
	value,
	onChange,
	placeholder = 'Search',
	autoFocus,
}: {
	value: string;
	onChange: (v: string) => void;
	placeholder?: string;
	autoFocus?: boolean;
}) {
	return (
		<label className="tsearch">
			<Icon name="search" />
			<input
				value={value}
				onChange={(e) => onChange(e.target.value)}
				placeholder={placeholder}
				autoComplete="off"
				autoFocus={autoFocus}
				aria-label={placeholder}
			/>
		</label>
	);
}

export function Toolbar({ children }: { children: ReactNode }) {
	return <div className="toolbar">{children}</div>;
}

export interface SelectOption {
	id: string | number | null;
	label?: string | null;
}

/** Compact toolbar select over API dropdown options. Options with an empty or null id are dropped. */
export function FilterSelect({
	label,
	allLabel,
	value,
	onChange,
	options,
}: {
	label: string;
	/** The "no filter" choice, e.g. "All actions". */
	allLabel: string;
	value: string;
	onChange: (v: string) => void;
	options: SelectOption[] | undefined;
}) {
	return (
		<select
			className="select w-auto min-w-[140px]"
			aria-label={label}
			value={value}
			onChange={(e) => onChange(e.target.value)}
		>
			<option value="">{allLabel}</option>
			{(options ?? [])
				.filter((o) => o.id !== null && o.id !== '')
				.map((o) => (
					<option key={String(o.id)} value={String(o.id)}>
						{o.label ?? String(o.id)}
					</option>
				))}
		</select>
	);
}
