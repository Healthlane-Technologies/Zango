import type { ReactNode } from 'react';
import { Icon, cx } from '@/ui';

// Local parts for the New app flow, after the prototype's vNew (.section, .srcopt, .summary).

/** Numbered form section: badge, title and hint, then an indented body. */
export function Section({
	n,
	title,
	hint,
	children,
}: {
	n: number;
	title: string;
	hint?: ReactNode;
	children: ReactNode;
}) {
	return (
		<section className="border-t border-border py-[22px] first:border-t-0 first:pt-0">
			<div className="mb-[14px] flex gap-[14px]">
				<span className="mt-[1px] grid h-[22px] w-[22px] shrink-0 place-items-center rounded-full border border-border-2 text-[11.5px] font-semibold text-t3">
					{n}
				</span>
				<div>
					<h3 className="text-[14px]">{title}</h3>
					{hint && <p className="mt-[1px] text-t3">{hint}</p>}
				</div>
			</div>
			<div className="pl-[36px]">{children}</div>
		</section>
	);
}

/** One radio-card choice in the "Starting point" picker. */
export function SourceOption({
	selected,
	title,
	description,
	onSelect,
	disabled,
}: {
	selected: boolean;
	title: string;
	description: string;
	onSelect: () => void;
	disabled?: boolean;
}) {
	return (
		<button
			type="button"
			role="radio"
			aria-checked={selected}
			disabled={disabled}
			onClick={onSelect}
			className={cx(
				'flex items-start gap-[10px] rounded-[9px] border bg-panel p-3 text-left shadow-card transition-[border-color,box-shadow] disabled:cursor-default disabled:opacity-50',
				selected
					? 'border-accent shadow-[0_0_0_3px_var(--ring)]'
					: 'border-border hover:border-border-2',
			)}
		>
			<span
				className={cx(
					'mt-[1px] h-4 w-4 shrink-0 rounded-full',
					selected ? 'border-[5px] border-accent' : 'border-[1.5px] border-border-2',
				)}
			/>
			<span>
				<b className="block font-[550] text-t1">{title}</b>
				<small className="text-[12px] text-t3">{description}</small>
			</span>
		</button>
	);
}

export function SummaryRow({ label, children }: { label: string; children: ReactNode }) {
	return (
		<div className="flex justify-between gap-3 border-b border-border-soft py-[7px] last:border-0">
			<span className="shrink-0 text-t3">{label}</span>
			<b className="min-w-0 truncate text-right font-medium text-t1">{children}</b>
		</div>
	);
}

export type StepState = 'pending' | 'running' | 'done' | 'failed';

/** One line of the launch checklist. */
export function Step({
	state,
	label,
	detail,
}: {
	state: StepState;
	label: ReactNode;
	detail?: ReactNode;
}) {
	return (
		<li className="flex items-start gap-[10px] py-[6px]">
			<span
				className={cx(
					'mt-[2px] grid h-4 w-4 shrink-0 place-items-center rounded-full',
					state === 'done' && 'bg-green text-white',
					state === 'running' && 'text-accent',
					state === 'pending' && 'border-[1.5px] border-border-2',
					state === 'failed' && 'bg-red text-white',
				)}
				aria-hidden
			>
				{state === 'done' && <Icon name="check" size={10} weight={3} />}
				{state === 'running' && <span className="spin" />}
				{state === 'failed' && <Icon name="x" size={10} weight={3} />}
			</span>
			<span className="min-w-0">
				<span
					className={cx(
						state === 'pending' ? 'text-t4' : 'text-t1',
						state === 'running' && 'font-[550]',
					)}
				>
					{label}
				</span>
				{detail && <span className="mono ml-1.5 text-t3">{detail}</span>}
			</span>
			<span className="sr-only">{state}</span>
		</li>
	);
}
