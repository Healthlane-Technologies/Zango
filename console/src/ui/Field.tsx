import {
	forwardRef,
	useId,
	type InputHTMLAttributes,
	type ReactNode,
	type SelectHTMLAttributes,
	type TextareaHTMLAttributes,
} from 'react';
import { cx } from './cx';

interface FieldProps {
	label: ReactNode;
	hint?: ReactNode;
	error?: string;
	children: (props: {
		id: string;
		'aria-invalid'?: boolean;
		'aria-describedby'?: string;
	}) => ReactNode;
}

/** Label + control + hint/error, with ids wired for accessibility. */
export function Field({ label, hint, error, children }: FieldProps) {
	const id = useId();
	const describedBy = error ? `${id}-err` : hint ? `${id}-hint` : undefined;
	return (
		<div className="field">
			<label htmlFor={id}>{label}</label>
			{children({ id, 'aria-invalid': error ? true : undefined, 'aria-describedby': describedBy })}
			{error ? (
				<span id={`${id}-err`} className="err">
					{error}
				</span>
			) : (
				hint && (
					<span id={`${id}-hint`} className="hint">
						{hint}
					</span>
				)
			)}
		</div>
	);
}

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
	function Input({ className, ...rest }, ref) {
		return <input ref={ref} className={cx('input', className)} {...rest} />;
	},
);

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
	function Select({ className, ...rest }, ref) {
		return <select ref={ref} className={cx('select', className)} {...rest} />;
	},
);

export const Textarea = forwardRef<
	HTMLTextAreaElement,
	TextareaHTMLAttributes<HTMLTextAreaElement>
>(function Textarea({ className, ...rest }, ref) {
	return <textarea ref={ref} className={cx('textarea', className)} {...rest} />;
});

/** Labelled group for controls that aren't a single input (chips, switches, checkbox lists). */
export function FieldGroup({
	label,
	hint,
	children,
}: {
	label: ReactNode;
	hint?: ReactNode;
	children: ReactNode;
}) {
	return (
		<div className="field">
			<span className="text-[12.5px] font-[550] text-t1">{label}</span>
			{children}
			{hint && <span className="hint">{hint}</span>}
		</div>
	);
}
