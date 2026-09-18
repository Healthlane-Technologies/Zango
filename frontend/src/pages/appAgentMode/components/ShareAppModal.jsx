/**
 * Hand the finished app to someone else.
 *
 * A URL on its own is useless here — the app requires a login, and the only
 * accounts that exist are the temporary ones the build created. So the link
 * and the credentials travel together, in one block that can be pasted into
 * an email, plus a mailto: that pre-fills the whole thing.
 */
import { useState } from 'react';
import StandardModal from '../../../components/StandardModal';

function credentialLines(testUsers) {
	return (testUsers || [])
		.filter((u) => u.password)
		.map((u) => `  ${u.role || 'User'}: ${u.email} / ${u.password}`);
}

export function shareText(appName, url, testUsers) {
	const lines = [`Here's the ${appName || 'app'} we just built:`, ''];
	if (url) lines.push(url, '');
	const creds = credentialLines(testUsers);
	if (creds.length) {
		lines.push('Sign in with one of these temporary accounts:', ...creds, '');
		lines.push('Please change the password after the first sign-in.');
	}
	return lines.join('\n');
}

export default function ShareAppModal({ show, closeModal, appName, run }) {
	const [copied, setCopied] = useState(false);
	const url = run?.app_access?.url || '';
	const testUsers = run?.test_users || [];

	const body = shareText(appName, url, testUsers);

	const copy = async () => {
		try {
			await navigator.clipboard.writeText(body);
			setCopied(true);
			setTimeout(() => setCopied(false), 2000);
		} catch {
			// Clipboard access is denied outside a secure context. The text is
			// selectable on screen, so this is a convenience, not the only way.
			setCopied(false);
		}
	};

	const mailto = `mailto:?subject=${encodeURIComponent(
		`${appName || 'Your new app'} is ready`
	)}&body=${encodeURIComponent(body)}`;

	return (
		<StandardModal
			label="Share this app"
			show={show}
			closeModal={closeModal}
			size="lg"
			ModalBody={
				<div className="flex flex-col gap-[16px] px-6 py-5">
					<div>
						<div className="mb-[6px] font-lato text-[11px] font-bold uppercase tracking-[0.06em] text-[#6B7280]">
							Link
						</div>
						{url ? (
							<a
								href={url}
								target="_blank"
								rel="noreferrer"
								className="break-all font-mono text-[12px] text-[#346BD4] hover:underline"
							>
								{url}
							</a>
						) : (
							<p className="font-lato text-[13px] text-[#B45309]">
								This app has no domain yet, so there is no link to share. Add
								one under App Settings and it will appear here.
							</p>
						)}
					</div>

					<div>
						<div className="mb-[6px] font-lato text-[11px] font-bold uppercase tracking-[0.06em] text-[#6B7280]">
							Temporary sign-ins
						</div>
						{testUsers.length ? (
							<table className="w-full font-mono text-[11.5px]">
								<tbody>
									{testUsers.map((u) => (
										<tr key={u.email} className="border-b border-[#F1F3F5]">
											<td className="py-[4px] pr-[10px] text-[#374151]">
												{u.email}
											</td>
											<td className="py-[4px] pr-[10px] text-[#6B7280]">
												{u.role}
											</td>
											<td className="select-all py-[4px] text-[#111827]">
												{u.password || u.status}
											</td>
										</tr>
									))}
								</tbody>
							</table>
						) : (
							<p className="font-lato text-[13px] text-[#6B7280]">
								No test accounts were created for this build.
							</p>
						)}
						<p className="mt-[8px] font-lato text-[12px] text-[#B45309]">
							These are temporary passwords. Whoever you send them to should
							change theirs at first sign-in.
						</p>
					</div>

					<div>
						<div className="mb-[6px] font-lato text-[11px] font-bold uppercase tracking-[0.06em] text-[#6B7280]">
							What gets sent
						</div>
						<pre className="max-h-[180px] select-all overflow-y-auto whitespace-pre-wrap rounded-[8px] border border-[#E5E7EB] bg-[#F8FAFC] p-[10px] font-mono text-[11.5px] leading-[17px] text-[#374151]">
							{body}
						</pre>
					</div>
				</div>
			}
			ModalFooter={
				<div className="flex justify-end gap-[8px]">
					<button
						onClick={copy}
						className="rounded-[6px] border border-[#DDE2E5] px-[14px] py-[7px] font-lato text-[13px] font-medium text-[#212429] hover:bg-[#F0F3F4]"
					>
						{copied ? 'Copied' : 'Copy'}
					</button>
					<a
						href={mailto}
						className="rounded-[8px] bg-gradient-to-br from-[#5048ED] to-[#346BD4] px-[16px] py-[8px] font-lato text-[13px] font-medium text-white hover:opacity-90"
					>
						Open in email
					</a>
				</div>
			}
		/>
	);
}
