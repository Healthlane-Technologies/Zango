import type { ReactNode } from 'react';
import { cx } from './cx';

export type Tone = 'green' | 'amber' | 'violet' | 'accent' | 'gray' | 'line' | 'red';

// Full class names, not `bd-${tone}`: Tailwind drops component-layer classes it can't find literally.
const toneClass: Record<Tone, string> = {
	green: 'bd-green',
	amber: 'bd-amber',
	violet: 'bd-violet',
	accent: 'bd-accent',
	gray: 'bd-gray',
	line: 'bd-line',
	red: 'bd-red',
};

interface BadgeProps {
	tone?: Tone;
	/** Leading status dot. */
	dot?: boolean;
	/** Leading spinner, for in-progress states. */
	busy?: boolean;
	children: ReactNode;
	className?: string;
}

export function Badge({ tone = 'gray', dot, busy, children, className }: BadgeProps) {
	return (
		<span className={cx('badge', toneClass[tone], className)}>
			{busy ? (
				<span className="spin" style={{ width: 9, height: 9 }} />
			) : (
				dot && <span className="d" />
			)}
			{children}
		</span>
	);
}
