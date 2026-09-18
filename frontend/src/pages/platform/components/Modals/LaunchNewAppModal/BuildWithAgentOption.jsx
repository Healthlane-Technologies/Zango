/**
 * The third way to launch an app: describe it and let the agent do the rest.
 *
 * Deliberately the first thing in the modal, and deliberately not a form —
 * there is nothing to fill in here. Everything the other two options ask for
 * (a name, a description, a template) is what the agent works out from one
 * sentence on the next screen.
 */
import { useNavigate } from 'react-router-dom';

export default function BuildWithAgentOption({ closeModal }) {
	const navigate = useNavigate();

	return (
		<button
			type="button"
			data-cy="build_with_agent_option"
			onClick={() => {
				closeModal();
				navigate('/platform/build-with-agent');
			}}
			className="group flex w-full items-start gap-[12px] rounded-[10px] border border-[#DDE2E5] bg-gradient-to-br from-[#F5F4FF] to-[#F2F7FF] p-[16px] text-left transition-colors hover:border-[#5048ED]"
		>
			<span className="mt-[2px] flex h-[32px] w-[32px] shrink-0 items-center justify-center rounded-[8px] bg-gradient-to-br from-[#5048ED] to-[#346BD4] shadow-lg">
				<svg width="18" height="18" viewBox="0 0 24 24" fill="none">
					<path
						d="M12 2L13.09 8.26L18 6L14.74 10.91L21 12L14.74 13.09L18 18L13.09 15.74L12 22L10.91 15.74L6 18L9.26 13.09L3 12L9.26 10.91L6 6L10.91 8.26L12 2Z"
						stroke="white"
						strokeWidth="1.5"
						strokeLinejoin="round"
						fill="none"
					/>
				</svg>
			</span>
			<span className="flex min-w-0 grow flex-col gap-[2px]">
				<span className="font-lato text-[14px] font-bold leading-[20px] text-[#111827]">
					Build with Agent
				</span>
				<span className="font-lato text-[13px] leading-[19px] text-[#6B7280]">
					Say what you need in plain words. The agent names the app, launches
					it, and builds it with you.
				</span>
			</span>
			<span className="mt-[4px] shrink-0 font-lato text-[16px] text-[#5048ED] transition-transform group-hover:translate-x-[2px]">
				→
			</span>
		</button>
	);
}
