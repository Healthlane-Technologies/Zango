/**
 * The standalone /runs/:runId screen.
 *
 * The build normally lives inside the requirement chat now — that is where
 * the user approved it and where the conversation continues. This route stays
 * for the cases the chat cannot cover: a direct link to an older run, and a
 * run started from a raw prompt with no requirement behind it.
 */
import { useNavigate, useParams } from 'react-router-dom';
import RunLive from './RunLive';

export default function RunProgress() {
	const { appId, runId } = useParams();
	const navigate = useNavigate();

	return (
		<div className="flex min-h-0 grow flex-col gap-[10px]">
			<RunLive
				appId={appId}
				runId={runId}
				onSwitchRun={(uuid) => navigate(`../runs/${uuid}`)}
			/>
			<div className="flex shrink-0 justify-end">
				<button
					onClick={() => navigate('..')}
					className="rounded-[6px] border border-[#DDE2E5] bg-white px-[14px] py-[7px] font-lato text-[13px] font-medium text-[#212429] hover:bg-[#F0F3F4]"
				>
					Back to requirements
				</button>
			</div>
		</div>
	);
}
