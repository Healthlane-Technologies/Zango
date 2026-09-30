// ChipSelect: a multi-select for short lists, used by the Users and Authentication screens.
import type { ReactNode } from 'react';
import { Icon, cx } from '@/ui';

export interface ChipOption<V extends string | number> {
	value: V;
	label: ReactNode;
}

/** Toggleable chips for picking several values from a short list. */
export function ChipSelect<V extends string | number>({
	options,
	value,
	onChange,
	label,
	disabled,
}: {
	options: ChipOption<V>[];
	value: V[];
	onChange: (v: V[]) => void;
	label: string;
	disabled?: boolean;
}) {
	return (
		<div className="flex flex-wrap gap-1.5" role="group" aria-label={label}>
			{options.map((o) => {
				const on = value.includes(o.value);
				return (
					<button
						key={o.value}
						type="button"
						aria-pressed={on}
						disabled={disabled}
						onClick={() => onChange(on ? value.filter((v) => v !== o.value) : [...value, o.value])}
						className={cx(
							'inline-flex h-7 items-center gap-1.5 rounded-md border px-2.5 text-[12.5px] font-medium transition-colors disabled:cursor-default disabled:opacity-50',
							on
								? 'border-accent bg-accent-soft text-accent-t'
								: 'border-border bg-panel text-t2 hover:border-border-2',
						)}
					>
						{on && <Icon name="check" size={13} weight={2.4} />}
						{o.label}
					</button>
				);
			})}
		</div>
	);
}
