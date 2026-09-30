import { Fragment, type ReactNode } from 'react';
import { Link, useMatches, type UIMatch } from 'react-router-dom';
import { useApp } from '@/api/apps';

/** Set on a route's `handle` to give it a breadcrumb. */
export interface CrumbHandle {
	crumb: (match: UIMatch) => ReactNode;
}

function hasCrumb(m: UIMatch): m is UIMatch<unknown, CrumbHandle> {
	return typeof (m.handle as CrumbHandle | undefined)?.crumb === 'function';
}

export function AppCrumb({ uuid }: { uuid: string }) {
	const { data } = useApp(uuid);
	return <>{data?.name ?? '…'}</>;
}

export function Breadcrumbs() {
	const crumbs = useMatches()
		.filter(hasCrumb)
		// An index route shares its parent's pathname; keep only the deeper crumb for a path once.
		.filter(
			(m, i, all) =>
				!all
					.slice(i + 1)
					.some((n) => n.pathname === m.pathname && n.handle.crumb === m.handle.crumb),
		);
	return (
		<nav className="crumbs" aria-label="Breadcrumb">
			{crumbs.map((m, i) => {
				const last = i === crumbs.length - 1;
				const label = m.handle.crumb(m);
				return (
					<Fragment key={m.id}>
						{i > 0 && <span className="sep">/</span>}
						{last ? <b>{label}</b> : <Link to={m.pathname}>{label}</Link>}
					</Fragment>
				);
			})}
		</nav>
	);
}
