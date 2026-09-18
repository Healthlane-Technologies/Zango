/**
 * Going live is a conversation, not a button.
 *
 * What the agent built runs on this environment with temporary accounts. A
 * production deployment needs a domain, real users, data migration and a
 * support arrangement — none of which this panel can decide. So this is
 * deliberately a hand-off to the Zelthy team rather than a self-serve action
 * that would imply otherwise.
 */
import StandardModal from '../../../components/StandardModal';

const CONTACT_EMAIL = 'support@zelthy.com';

export default function DeployAppModal({ show, closeModal, appName, run }) {
	const url = run?.app_access?.url || '';
	const subject = `Deploy ${appName || 'my app'} to production`;
	const body = [
		`I'd like to take ${appName || 'this app'} live.`,
		'',
		url ? `Built here: ${url}` : '',
		'',
		'Happy to talk through domain, users and data whenever suits.',
	]
		.filter((line) => line !== null)
		.join('\n');

	return (
		<StandardModal
			label="Deploy to production"
			show={show}
			closeModal={closeModal}
			ModalBody={
				<div className="flex flex-col gap-[14px] px-6 py-5">
					<p className="font-lato text-[13.5px] leading-[20px] text-[#374151]">
						What you have now is a working app on this environment, with
						temporary sign-ins. Taking it live is a short conversation — the
						Zelthy team will set it up with you.
					</p>
					<div className="rounded-[8px] border border-[#E5E7EB] bg-[#F8FAFC] p-[12px]">
						<div className="mb-[8px] font-lato text-[11px] font-bold uppercase tracking-[0.06em] text-[#6B7280]">
							What they'll sort out with you
						</div>
						<ul className="flex flex-col gap-[6px]">
							{[
								'Your own domain and certificate',
								'Real user accounts, roles and sign-in',
								'Moving across any data you already hold',
								'Backups, monitoring and support',
							].map((item) => (
								<li
									key={item}
									className="flex items-start gap-[8px] font-lato text-[13px] leading-[19px] text-[#374151]"
								>
									<span className="mt-[7px] h-[4px] w-[4px] shrink-0 rounded-full bg-[#9CA3AF]" />
									{item}
								</li>
							))}
						</ul>
					</div>
					<p className="font-lato text-[13px] leading-[19px] text-[#6B7280]">
						Nothing changes here in the meantime — keep building and sharing
						this version while you talk.
					</p>
				</div>
			}
			ModalFooter={
				<div className="flex items-center justify-between gap-[8px]">
					<span className="font-lato text-[12px] text-[#6B7280]">
						{CONTACT_EMAIL}
					</span>
					<span className="flex gap-[8px]">
						<button
							onClick={closeModal}
							className="rounded-[6px] border border-[#DDE2E5] px-[14px] py-[7px] font-lato text-[13px] font-medium text-[#212429] hover:bg-[#F0F3F4]"
						>
							Not yet
						</button>
						<a
							href={`mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent(
								subject
							)}&body=${encodeURIComponent(body)}`}
							className="rounded-[8px] bg-gradient-to-br from-[#5048ED] to-[#346BD4] px-[16px] py-[8px] font-lato text-[13px] font-medium text-white hover:opacity-90"
						>
							Contact the Zelthy team
						</a>
					</span>
				</div>
			}
		/>
	);
}
