import type { ReactNode } from 'react';
import { cx } from '@/ui';

// Local parts for Overview and Settings.

/** Small metric tile: label, value, optional footnote. */
export function StatTile({
	label,
	value,
	sub,
	loading,
}: {
	label: string;
	value: ReactNode;
	sub?: ReactNode;
	loading?: boolean;
}) {
	return (
		<div className="card px-4 py-3">
			<div className="text-[12px] text-t3">{label}</div>
			<div className="num mt-1 text-[20px] font-semibold tracking-tight text-t1">
				{loading ? <span className="sk" style={{ width: 48, height: 20 }} /> : value}
			</div>
			{sub && <div className="mt-0.5 text-[12px] text-t3">{sub}</div>}
		</div>
	);
}

const HEX_RE = /^#[0-9a-fA-F]{6}$/;

/** Native colour swatch plus a hex text input. */
export function ColorField({
	label,
	value,
	onChange,
}: {
	label: string;
	value: string;
	onChange: (v: string) => void;
}) {
	return (
		<div className="field">
			<label>{label}</label>
			<div
				className={cx(
					'flex h-8 items-center gap-2 rounded-[7px] border bg-panel pl-1 pr-2 shadow-card',
					HEX_RE.test(value) ? 'border-border' : 'border-red',
				)}
			>
				<input
					type="color"
					aria-label={`${label} colour`}
					value={HEX_RE.test(value) ? value : '#000000'}
					onChange={(e) => onChange(e.target.value)}
					className="h-6 w-7 cursor-pointer rounded border-0 bg-transparent p-0"
				/>
				<input
					value={value}
					onChange={(e) => onChange(e.target.value)}
					aria-label={`${label} hex`}
					className="mono min-w-0 flex-1 border-0 bg-transparent text-t1 focus:outline-none"
				/>
			</div>
		</div>
	);
}

export function Swatch({ color, title }: { color?: string; title?: string }) {
	return (
		<span
			title={title ?? color}
			className="inline-block h-5 w-5 rounded-[5px] border border-border"
			style={{ background: color ?? 'transparent' }}
		/>
	);
}

/** Section heading inside a settings card body. */
export function SectionNote({ children }: { children: ReactNode }) {
	return <p className="mb-4 text-t3">{children}</p>;
}
