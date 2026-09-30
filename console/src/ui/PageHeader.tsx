import type { ReactNode } from 'react';

export function Page({ children, wide }: { children: ReactNode; wide?: boolean }) {
	return (
		<div className="page fi" style={wide ? { maxWidth: 1280 } : undefined}>
			{children}
		</div>
	);
}

export function PageHeader({
	title,
	description,
	actions,
}: {
	title: ReactNode;
	description?: ReactNode;
	actions?: ReactNode;
}) {
	return (
		<div className="ph">
			<div className="min-w-0">
				<h1>{title}</h1>
				{description && <p>{description}</p>}
			</div>
			{actions && <div className="r">{actions}</div>}
		</div>
	);
}
