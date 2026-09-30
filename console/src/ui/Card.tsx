import type { HTMLAttributes, ReactNode } from 'react';
import { cx } from './cx';

export function Card({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
	return <div className={cx('card', className)} {...rest} />;
}

export function CardHeader({
	title,
	count,
	actions,
}: {
	title: ReactNode;
	count?: ReactNode;
	actions?: ReactNode;
}) {
	return (
		<div className="card-h">
			<h3>{title}</h3>
			{count != null && <span className="ct text-t4">{count}</span>}
			{actions && <div className="r">{actions}</div>}
		</div>
	);
}

export function CardBody({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
	return <div className={cx('card-b', className)} {...rest} />;
}

export function Banner({ children }: { children: ReactNode }) {
	return <div className="banner">{children}</div>;
}
