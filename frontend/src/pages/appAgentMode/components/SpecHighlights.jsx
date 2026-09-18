/**
 * The requirement at a glance, while it is still being agreed.
 *
 * Reference, not reading. The full spec is one tab away and is what actually
 * gets approved; this answers "what did I ask for again?" without making
 * anyone re-read a page of prose.
 *
 * It stops once the app exists. At that point the panel is the app's own
 * actions, and a summary of the spec is a worse place to look than the thing
 * the spec produced.
 */
import specHighlights from '../specHighlights';

const ACCENTS = {
	entities: '#5048ED',
	roles: '#0F766E',
	stages: '#B45309',
	screens: '#346BD4',
	automatic: '#7C3AED',
	branding: '#BE185D',
	excluded: '#6B7280',
	assumptions: '#6B7280',
};

// These say what the app is *not*. Worth keeping — an explicit "left out" list
// is how the user knows they were heard — but never as loud as the scope.
const MUTED = ['excluded', 'assumptions'];

export default function SpecHighlights({ spec }) {
	const { title, summary, groups } = specHighlights(spec);

	if (!groups.length) {
		return (
			<div className="flex grow items-center justify-center px-[24px] py-[40px] text-center">
				<p className="font-lato text-[13px] leading-[20px] text-[#9CA3AF]">
					The agent is working out what you need.
					<br />
					Once the requirement is clear it will appear here for review.
				</p>
			</div>
		);
	}

	return (
		<div className="flex flex-col gap-[16px] p-[16px]">
			{title ? (
				<div>
					<h3 className="font-source-sans-pro text-[16px] font-semibold leading-[22px] text-[#111827]">
						{title}
					</h3>
					{summary ? (
						<p className="mt-[4px] font-lato text-[13px] leading-[19px] text-[#6B7280]">
							{summary}
						</p>
					) : null}
				</div>
			) : null}

			{groups.map((group) => {
				const muted = MUTED.includes(group.key);
				return (
					<div key={group.key}>
						<div className="mb-[8px] flex items-baseline gap-[8px]">
							<span
								className="font-lato text-[11px] font-bold uppercase tracking-[0.06em]"
								style={{ color: ACCENTS[group.key] || '#6B7280' }}
							>
								{group.label}
							</span>
							{group.items.length > 1 ? (
								<span className="font-lato text-[11px] text-[#9CA3AF]">
									{group.items.length}
								</span>
							) : null}
						</div>
						<div className="flex flex-col gap-[6px]">
							{group.items.map((item, index) => (
								<div
									key={`${item.name}-${index}`}
									className={`rounded-[8px] border px-[10px] py-[7px] ${
										muted
											? 'border-[#F1F3F5] bg-[#FAFAFA]'
											: 'border-[#E5E7EB] bg-white'
									}`}
								>
									<span
										className={`font-lato text-[13px] leading-[19px] ${
											muted ? 'text-[#6B7280]' : 'font-semibold text-[#111827]'
										}`}
									>
										{item.name}
									</span>
									{item.detail ? (
										<p className="mt-[2px] font-lato text-[12px] leading-[18px] text-[#6B7280]">
											{item.detail}
										</p>
									) : null}
								</div>
							))}
						</div>
					</div>
				);
			})}
		</div>
	);
}
