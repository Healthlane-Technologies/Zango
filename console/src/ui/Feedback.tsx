import type { CSSProperties, ReactNode } from 'react';

export function EmptyState({
	title,
	children,
	action,
}: {
	title: ReactNode;
	children?: ReactNode;
	action?: ReactNode;
}) {
	return (
		<div className="empty">
			<b>{title}</b>
			{children && <div>{children}</div>}
			{action && <div className="mt-4 flex justify-center">{action}</div>}
		</div>
	);
}

export function Skeleton({
	width = '100%',
	height = 12,
	style,
}: {
	width?: CSSProperties['width'];
	height?: number;
	style?: CSSProperties;
}) {
	return <span className="sk" style={{ width, height, ...style }} />;
}

export function Spinner() {
	return <span className="spin" />;
}

/** Inline error for a failed query, with an optional retry. */
export function ErrorState({ error, onRetry }: { error: Error; onRetry?: () => void }) {
	return (
		<div className="empty">
			<b>Something went wrong</b>
			<div className="text-red-t">{error.message}</div>
			{onRetry && (
				<button className="btn btn-s btn-sm mt-4" onClick={onRetry}>
					Try again
				</button>
			)}
		</div>
	);
}
