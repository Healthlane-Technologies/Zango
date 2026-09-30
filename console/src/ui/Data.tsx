import type { ReactNode } from 'react';

/** Label/value rows in the prototype's `.kv` style. Missing values show as a dash. */
export function KeyValues({ items }: { items: Array<[ReactNode, ReactNode]> }) {
	return (
		<dl className="kv">
			{items.map(([k, v], i) => (
				<div key={i} className="contents">
					<dt>{k}</dt>
					<dd>{v ?? <span className="text-t4">—</span>}</dd>
				</div>
			))}
		</dl>
	);
}

/** Read-only code or JSON block. */
export function CodeBlock({ children, maxHeight = 320 }: { children: string; maxHeight?: number }) {
	return (
		<pre
			className="mono overflow-auto whitespace-pre rounded-lg border border-border bg-bg p-3 text-[12px] leading-[1.6] text-t1"
			style={{ maxHeight }}
		>
			{children}
		</pre>
	);
}

/** Small heading inside a drawer or card body, with an optional action on the right. */
export function SectionTitle({ children, action }: { children: ReactNode; action?: ReactNode }) {
	return (
		<div className="mb-2 mt-6 flex items-center first:mt-0">
			<h4 className="text-[12.5px] font-semibold text-t1">{children}</h4>
			{action && <div className="ml-auto">{action}</div>}
		</div>
	);
}
