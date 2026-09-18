/**
 * The app exists — here is everything you would want to do with it.
 *
 * Once a build succeeds this replaces the requirement summary entirely: what
 * the app does is now better answered by opening it than by reading a recap
 * of the spec, so the panel becomes the things you would actually do next.
 *
 * Opening the app is useless without a way in — it requires a login and the
 * only accounts that exist are the temporary ones the build just created — so
 * every one of them sits next to the link rather than buried in Share.
 */
import { useState } from 'react';
import DeployAppModal from './DeployAppModal';
import ShareAppModal from './ShareAppModal';

const COLUMNS = [
	{ label: 'Role', width: 'w-[26%]' },
	{ label: 'Email', width: 'w-[40%]' },
	{ label: 'Password', width: 'w-auto' },
];

function CopyButton({ value }) {
	const [copied, setCopied] = useState(false);

	const copy = async () => {
		try {
			await navigator.clipboard.writeText(value);
			setCopied(true);
			setTimeout(() => setCopied(false), 1500);
		} catch {
			// Denied outside a secure context. The value is selectable on
			// screen, so this is a convenience rather than the only way to it.
			setCopied(false);
		}
	};

	return (
		<button
			onClick={copy}
			className="shrink-0 rounded-[5px] border border-[#DDE2E5] bg-white px-[7px] py-[2px] font-lato text-[11px] text-[#6B7280] hover:bg-[#F0F3F4]"
		>
			{copied ? 'Copied' : 'Copy'}
		</button>
	);
}

function CopyField({ label, value }) {
	return (
		<div className="flex items-center gap-[8px]">
			<span className="w-[62px] shrink-0 font-lato text-[11px] uppercase tracking-[0.05em] text-[#9CA3AF]">
				{label}
			</span>
			<span className="min-w-0 grow select-all truncate font-mono text-[12px] text-[#111827]">
				{value}
			</span>
			<CopyButton value={value} />
		</div>
	);
}

function ActionTile({ title, description, onClick }) {
	return (
		<button
			onClick={onClick}
			className="flex min-w-0 flex-col items-start gap-[2px] rounded-[9px] border border-[#E5E7EB] bg-white p-[11px] text-left transition-colors hover:border-[#9CA3AF]"
		>
			<span className="font-lato text-[13px] font-semibold leading-[18px] text-[#111827]">
				{title}
			</span>
			<span className="font-lato text-[11.5px] leading-[16px] text-[#6B7280]">
				{description}
			</span>
		</button>
	);
}

export default function AppReadyCard({ appName, run }) {
	const [sharing, setSharing] = useState(false);
	const [deploying, setDeploying] = useState(false);

	const url = run?.app_access?.url || '';
	// A build that ended in sync errors still produced a running app — say so
	// rather than hiding the link behind a perfect-run check.
	const partial = run?.status === 'partial';
	const signIns = run?.test_users || [];

	return (
		<>
			<div className="p-[16px]">
				{url ? (
					<div className="rounded-[10px] border border-[#E5E7EB] bg-white p-[12px]">
						<CopyField label="Link" value={url} />

						{signIns.length ? (
							<div className="mt-[10px] overflow-hidden rounded-[8px] border border-[#EDEFF1]">
								<table className="w-full table-fixed">
									<thead>
										<tr className="bg-[#FAFAFA]">
											{COLUMNS.map((c) => (
												<th
													key={c.label}
													className={`${c.width} px-[9px] py-[5px] text-left font-lato text-[10.5px] font-bold uppercase tracking-[0.05em] text-[#9CA3AF]`}
												>
													{c.label}
												</th>
											))}
											<th className="w-[52px]" />
										</tr>
									</thead>
									<tbody>
										{signIns.map((u) => (
											<tr key={u.email} className="border-t border-[#F1F3F5]">
												<td className="truncate px-[9px] py-[6px] font-lato text-[12px] text-[#374151]">
													{u.role || '—'}
												</td>
												<td className="truncate px-[9px] py-[6px] font-mono text-[11.5px] text-[#111827]">
													{u.email}
												</td>
												<td className="truncate px-[9px] py-[6px] font-mono text-[11.5px] text-[#111827]">
													<span className="select-all">{u.password || u.status}</span>
												</td>
												<td className="px-[9px] py-[6px] text-right">
													{u.password ? <CopyButton value={u.password} /> : null}
												</td>
											</tr>
										))}
									</tbody>
								</table>
							</div>
						) : null}

						<div className="mt-[11px] flex flex-wrap items-center gap-[8px]">
							<a
								href={url}
								target="_blank"
								rel="noreferrer"
								className="rounded-[7px] bg-gradient-to-br from-[#5048ED] to-[#346BD4] px-[15px] py-[7px] font-lato text-[13px] font-medium text-white hover:opacity-90"
							>
								Open the app ↗
							</a>
							{signIns.length ? (
								<span className="font-lato text-[11.5px] leading-[16px] text-[#6B7280]">
									Temporary passwords — change them at first sign-in
								</span>
							) : null}
						</div>
					</div>
				) : (
					<p className="font-lato text-[13px] leading-[19px] text-[#B45309]">
						The app was built, but it has no domain yet — so there is nothing to
						open. Add one under App Settings and it will appear here.
					</p>
				)}

				{partial ? (
					<p className="mt-[10px] font-lato text-[12px] leading-[18px] text-[#B45309]">
						Some finishing steps reported errors, so parts of it may not work
						yet. The build detail in the conversation says which.
					</p>
				) : null}

				<div className="mt-[12px] grid grid-cols-2 gap-[8px]">
					<ActionTile
						title="Share"
						description="Link and sign-ins, ready to email"
						onClick={() => setSharing(true)}
					/>
					<ActionTile
						title="Deploy"
						description="Take it live with the Zelthy team"
						onClick={() => setDeploying(true)}
					/>
				</div>
			</div>

			<ShareAppModal
				show={sharing}
				closeModal={() => setSharing(false)}
				appName={appName}
				run={run}
			/>
			<DeployAppModal
				show={deploying}
				closeModal={() => setDeploying(false)}
				appName={appName}
				run={run}
			/>
		</>
	);
}
