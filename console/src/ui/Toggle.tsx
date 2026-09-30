import { useId, type InputHTMLAttributes, type ReactNode } from 'react';
import { cx } from './cx';

interface SwitchProps {
	checked: boolean;
	onChange: (v: boolean) => void;
	disabled?: boolean;
	/** Accessible name when there's no visible label. */
	label?: string;
	id?: string;
	labelledBy?: string;
	describedBy?: string;
}

/** Bare on/off switch. Use SwitchField or SwitchRow for a labelled one. */
export function Switch({
	checked,
	onChange,
	disabled,
	label,
	id,
	labelledBy,
	describedBy,
}: SwitchProps) {
	return (
		<button
			id={id}
			type="button"
			role="switch"
			aria-checked={checked}
			aria-label={label}
			aria-labelledby={labelledBy}
			aria-describedby={describedBy}
			disabled={disabled}
			onClick={() => onChange(!checked)}
			className={cx(
				'relative h-[18px] w-[30px] shrink-0 rounded-full transition-colors disabled:cursor-default disabled:opacity-50',
				checked ? 'bg-accent' : 'bg-border-2',
			)}
		>
			<span
				className={cx(
					'absolute left-[2px] top-[2px] h-[14px] w-[14px] rounded-full bg-white shadow-[0_1px_2px_rgba(0,0,0,.2)] transition-transform duration-200 ease-out',
					checked && 'translate-x-[12px]',
				)}
			/>
		</button>
	);
}

/** Switch with its label and hint to the right. */
export function SwitchField({
	checked,
	onChange,
	label,
	hint,
	disabled,
}: {
	checked: boolean;
	onChange: (v: boolean) => void;
	label: ReactNode;
	hint?: ReactNode;
	disabled?: boolean;
}) {
	const id = useId();
	return (
		<div className={cx('flex items-start gap-3', disabled && 'opacity-50')}>
			<span className="mt-[1px]">
				<Switch
					id={id}
					checked={checked}
					onChange={onChange}
					disabled={disabled}
					describedBy={hint ? `${id}-hint` : undefined}
				/>
			</span>
			<label htmlFor={id} className="cursor-pointer">
				<span className="block font-[550] text-t1">{label}</span>
				{hint && (
					<span id={`${id}-hint`} className="block text-[12px] text-t3">
						{hint}
					</span>
				)}
			</label>
		</div>
	);
}

/** Settings row: title and description on the left, switch on the right; `children` show beneath when on. */
export function SwitchRow({
	title,
	description,
	checked,
	onChange,
	disabled,
	children,
}: {
	title: ReactNode;
	description?: ReactNode;
	checked: boolean;
	onChange: (v: boolean) => void;
	disabled?: boolean;
	children?: ReactNode;
}) {
	const id = useId();
	return (
		<div className="border-t border-border-soft py-[10px] first:border-t-0">
			<div className="flex items-start gap-3">
				<label htmlFor={id} className="min-w-0 flex-1 cursor-pointer">
					<b id={`${id}-t`} className="block font-[550] text-t1">
						{title}
					</b>
					{description && (
						<small id={`${id}-d`} className="text-[12px] text-t3">
							{description}
						</small>
					)}
				</label>
				<Switch
					id={id}
					checked={checked}
					onChange={onChange}
					disabled={disabled}
					labelledBy={`${id}-t`}
					describedBy={description ? `${id}-d` : undefined}
				/>
			</div>
			{checked && children && <div className="mt-3 grid gap-3 pb-1">{children}</div>}
		</div>
	);
}

/** Checkbox with a label and optional hint. Takes normal input props (`checked`, `onChange`, …). */
export function Checkbox({
	label,
	hint,
	className,
	...rest
}: { label: ReactNode; hint?: ReactNode } & Omit<InputHTMLAttributes<HTMLInputElement>, 'type'>) {
	return (
		<label className={cx('flex cursor-pointer items-start gap-2.5 py-1', className)}>
			<input
				type="checkbox"
				className="mt-[3px] h-[14px] w-[14px] shrink-0 accent-[var(--accent)]"
				{...rest}
			/>
			<span className="min-w-0">
				<span className="text-t1">{label}</span>
				{hint && <span className="block text-[12px] text-t3">{hint}</span>}
			</span>
		</label>
	);
}
