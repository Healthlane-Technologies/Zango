import { useState } from 'react';
import type { RunDetail, TestUser } from '@/api/agentRuns';
import { Button, Card, Icon, Modal } from '@/ui';

const CONTACT_EMAIL = 'support@zelthy.com';

function useCopy() {
	const [copied, setCopied] = useState<string | null>(null);
	const copy = async (key: string, value: string) => {
		try {
			await navigator.clipboard.writeText(value);
			setCopied(key);
			setTimeout(() => setCopied((c) => (c === key ? null : c)), 1500);
		} catch {
			// Clipboard is denied outside a secure context; the value is selectable on screen.
		}
	};
	return { copied, copy };
}

/** The share text: a link is useless without a sign-in, so they travel together. */
export function shareText(appName: string, url: string, users: TestUser[]): string {
	const lines = [`Here's the ${appName || 'app'} we just built:`, ''];
	if (url) lines.push(url, '');
	const creds = users
		.filter((u) => u.password)
		.map((u) => `  ${u.role || 'User'}: ${u.email} / ${u.password}`);
	if (creds.length) {
		lines.push('Sign in with one of these temporary accounts:', ...creds, '');
		lines.push('These are demo accounts — please do not reuse the password.');
	}
	return lines.join('\n');
}

function SignIns({ users, copy, copied }: { users: TestUser[] } & ReturnType<typeof useCopy>) {
	return (
		<div className="overflow-hidden rounded-lg border border-border">
			<table className="rp-mini table-fixed">
				<thead>
					<tr>
						<th className="w-[26%]">Role</th>
						<th className="w-[42%]">Email</th>
						<th>Password</th>
						<th className="w-[64px]" />
					</tr>
				</thead>
				<tbody>
					{users.map((u) => (
						<tr key={u.email}>
							<td className="truncate">{u.role || '—'}</td>
							<td className="mono truncate">{u.email}</td>
							<td className="mono truncate">
								{u.password ? (
									<span className="select-all">{u.password}</span>
								) : (
									<span className="text-t3">
										{u.status === 'exists' ? 'Existing account' : u.status}
									</span>
								)}
							</td>
							<td className="ra">
								{u.password && (
									<Button size="xs" onClick={() => copy(`pw-${u.email}`, u.password!)}>
										{copied === `pw-${u.email}` ? 'Copied' : 'Copy'}
									</Button>
								)}
							</td>
						</tr>
					))}
				</tbody>
			</table>
		</div>
	);
}

/**
 * The app exists: the link, the sign-ins the build created, and Share / Deploy. Opening the
 * app needs a login, so the credentials sit next to the link rather than inside Share.
 */
export function AppReady({ appName, run, quiet = false }: { appName: string; run: RunDetail; quiet?: boolean }) {
	const url = run.app_access?.url ?? '';
	const users = run.test_users ?? [];
	const clip = useCopy();
	const [sharing, setSharing] = useState(false);
	const [deploying, setDeploying] = useState(false);

	return (
		<Card className="p-4">
			<div className="mb-3 flex items-center gap-2">
				{quiet ? (
					// the status card above says how the app is; this card is how to try it
					<b className="text-t1">Try it</b>
				) : (
					<>
						<span className="rp-okc">
							<Icon name="check" size={11} weight={3} />
						</span>
						<b className="text-t1">Your app is ready</b>
						{run.status === 'partial' && (
							<span className="text-[12px] text-amber-t">· some finishing steps reported errors</span>
						)}
					</>
				)}
			</div>
			{url ? (
				<>
					<div className="mb-3 flex items-center gap-2">
						<span className="mono min-w-0 flex-1 select-all truncate text-t1">{url}</span>
						<Button size="xs" onClick={() => clip.copy('url', url)}>
							{clip.copied === 'url' ? 'Copied' : 'Copy'}
						</Button>
					</div>
					{users.length > 0 && <SignIns users={users} {...clip} />}
					<div className="mt-3 flex flex-wrap items-center gap-2">
						<a className="btn btn-p btn-sm" href={url} target="_blank" rel="noreferrer">
							<Icon name="ext" />
							Open the app
						</a>
						<Button size="sm" icon="users" onClick={() => setSharing(true)}>
							Share
						</Button>
						<Button size="sm" icon="rocket" onClick={() => setDeploying(true)}>
							Deploy
						</Button>
					</div>
				</>
			) : (
				<p className="text-amber-t">
					The app was built but has no domain yet, so there's nothing to open. Add one under
					Settings and it will appear here.
				</p>
			)}

			<ShareModal
				open={sharing}
				onOpenChange={setSharing}
				appName={appName}
				url={url}
				users={users}
			/>
			<DeployModal open={deploying} onOpenChange={setDeploying} appName={appName} url={url} />
		</Card>
	);
}

function ShareModal({
	open,
	onOpenChange,
	appName,
	url,
	users,
}: {
	open: boolean;
	onOpenChange: (o: boolean) => void;
	appName: string;
	url: string;
	users: TestUser[];
}) {
	const { copied, copy } = useCopy();
	const body = shareText(appName, url, users);
	const mailto = `mailto:?subject=${encodeURIComponent(`${appName || 'Your new app'} is ready`)}&body=${encodeURIComponent(body)}`;
	return (
		<Modal
			open={open}
			onOpenChange={onOpenChange}
			title="Share this app"
			subtitle="The link and its temporary sign-ins, ready to paste into an email."
			footer={
				<>
					<Button onClick={() => copy('body', body)}>
						{copied === 'body' ? 'Copied' : 'Copy'}
					</Button>
					<a className="btn btn-p" href={mailto}>
						Open in email
					</a>
				</>
			}
		>
			<div className="grid gap-3">
				{users.length ? (
					<p className="rp-note warn">
						Demo accounts on a demo build sign in as they are, so treat the link and these passwords
						as one thing you're sharing.
					</p>
				) : (
					<p className="text-t3">No test accounts were created for this build.</p>
				)}
				<div>
					<div className="rp-sec">What gets sent</div>
					<pre className="mono max-h-[220px] select-all overflow-auto whitespace-pre-wrap rounded-lg border border-border bg-bg p-3 text-[12px] leading-[1.6] text-t1">
						{body}
					</pre>
				</div>
			</div>
		</Modal>
	);
}

// Going live is a conversation with the Zelthy team, not a self-serve action: a production
// deployment needs a domain, real users, data migration and support that this panel can't decide.
function DeployModal({
	open,
	onOpenChange,
	appName,
	url,
}: {
	open: boolean;
	onOpenChange: (o: boolean) => void;
	appName: string;
	url: string;
}) {
	const subject = `Deploy ${appName || 'my app'} to production`;
	const body = [
		`I'd like to take ${appName || 'this app'} live.`,
		'',
		url ? `Built here: ${url}` : '',
		'',
		'Happy to talk through domain, users and data whenever suits.',
	].join('\n');
	return (
		<Modal
			open={open}
			onOpenChange={onOpenChange}
			title="Deploy to production"
			subtitle={CONTACT_EMAIL}
			footer={
				<>
					<Button onClick={() => onOpenChange(false)}>Not yet</Button>
					<a
						className="btn btn-p"
						href={`mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`}
					>
						Contact the Zelthy team
					</a>
				</>
			}
		>
			<div className="grid gap-3">
				<p>
					What you have now is a working app on this environment, with temporary sign-ins. Taking it
					live is a short conversation — the Zelthy team sets it up with you.
				</p>
				<div className="rounded-lg border border-border bg-bg p-3">
					<div className="rp-sec">What they'll sort out with you</div>
					<ul className="grid gap-1.5">
						{[
							'Your own domain and certificate',
							'Real user accounts, roles and sign-in',
							'Moving across any data you already hold',
							'Backups, monitoring and support',
						].map((item) => (
							<li key={item} className="flex items-start gap-2 text-t1">
								<Icon name="check" size={13} className="mt-[3px] text-green" />
								{item}
							</li>
						))}
					</ul>
				</div>
				<p className="text-t3">
					Nothing changes here in the meantime — keep building and sharing this version while you
					talk.
				</p>
			</div>
		</Modal>
	);
}
