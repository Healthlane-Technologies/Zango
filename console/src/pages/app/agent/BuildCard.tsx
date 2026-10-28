import { useState } from 'react';
import type { BuildCardStatus } from '@/api/agentMode';
import { Icon, cx } from '@/ui';

export const CARD_LABEL = { building: 'Still building', finishing: 'Ready', ready: 'Ready' } as const;

/** A build's word to the person who made the app (studio_status.user_status): progress, never failures. */
export function BuildCard({ status, actions = true }: { status: BuildCardStatus; actions?: boolean }) {
	const [allRoles, setAllRoles] = useState(false);
	const roles = allRoles ? status.roles : status.roles.slice(0, 4);
	const t = status.tried;
	return (
		<div className={cx('bc', `bc-${status.state}`)}>
			<div className="bc-top">
				<span className="bc-pill">
					<span className="dot" />
					{CARD_LABEL[status.state]}
				</span>
				<h3>{status.headline}</h3>
				<p>{status.body}</p>
				{actions && status.state !== 'building' && status.app_url && (
					<div className="bc-acts">
						<a className="btn btn-p" href={status.app_url} target="_blank" rel="noreferrer">
							Open the app <Icon name="ext" size={13} />
						</a>
					</div>
				)}
			</div>
			{status.finishing && (
				<div className="bc-row bc-fin">
					{status.active && <span className="spin" />}
					<span>{status.finishing}</span>
				</div>
			)}
			{roles.length > 0 && (
				<div className="bc-row bc-roles">
					<h4>What each role can do</h4>
					<dl>
						{roles.map((r) => (
							<div key={r.role}>
								<dt>{r.role}</dt>
								<dd>
									{r.steps.slice(0, 5).map((s) => (
										<span key={s}>
											<Icon name="check" size={11} weight={2.6} /> {s}
										</span>
									))}
									{r.steps.length > 5 && <span className="bc-n">and {r.steps.length - 5} more</span>}
								</dd>
							</div>
						))}
					</dl>
					{status.roles.length > 4 && !allRoles && (
						<button type="button" className="bc-more" onClick={() => setAllRoles(true)}>
							Show {status.roles.length - 4} more roles
						</button>
					)}
				</div>
			)}
			{(t.steps > 0 || status.state === 'building') && (
				<div className="bc-foot">
					<span>
						{t.steps > 0
							? `We tried ${t.steps} steps as ${t.roles} roles${t.screens ? ` and compared ${t.screens} screens with your preview` : ''}.`
							: 'Nothing for you to do while we finish.'}
					</span>
				</div>
			)}
		</div>
	);
}
