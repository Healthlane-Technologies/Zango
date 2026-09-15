/**
 * Agent Mode shell.
 *
 * Two phases: gather and approve a requirement, then commit to a build.
 * Nothing is written to the app until a requirement has been approved.
 */
import { useCallback, useEffect, useState } from 'react';
import { Route, Routes, useParams } from 'react-router-dom';
import BreadCrumbs from '../../app/components/BreadCrumbs';
import useApi from '../../../hooks/useApi';
import RequirementChat from './RequirementChat';
import RequirementList from './RequirementList';
import RunProgress from './RunProgress';

const REASON_TEXT = {
	feature_disabled: 'Build with AI is disabled. Set AGENT_MODE_ENABLED=True.',
	sdk_not_installed: 'The Claude Agent SDK is not installed on the server.',
	cli_not_found: 'The Claude Code binary could not be found.',
	no_credentials: 'No Anthropic API key is configured for the platform.',
	skill_plugin_missing: 'The Zango skill plugin is missing from the install.',
	workspace_missing: 'This app has no workspace directory on disk.',
	app_suspended: 'This app is suspended.',
	no_worker: 'No Celery worker is consuming the agent_mode queue.',
};

export default function AgentMode() {
	const { appId } = useParams();
	const triggerApi = useApi();
	const [availability, setAvailability] = useState(null);

	const load = useCallback(async () => {
		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/agent-mode/availability/`,
			type: 'GET', loader: false, showErrorModal: false,
		});
		if (success && response) setAvailability(response);
	}, [appId]);

	useEffect(() => { load(); }, [appId]);

	const blocked = availability && !availability.available;

	return (
		<div className="flex h-full flex-col overflow-hidden bg-[#F8FAFC]">
			<div className="flex-shrink-0 border-b border-[#E5E7EB] bg-white px-[40px] py-[20px]">
				<BreadCrumbs />
				<div className="mt-[8px] flex items-center gap-[12px]">
					<div className="flex h-[40px] w-[40px] items-center justify-center rounded-[8px] bg-gradient-to-br from-[#5048ED] to-[#346BD4] shadow-lg">
						<svg width="22" height="22" viewBox="0 0 24 24" fill="none">
							<path
								d="M12 2L13.09 8.26L18 6L14.74 10.91L21 12L14.74 13.09L18 18L13.09 15.74L12 22L10.91 15.74L6 18L9.26 13.09L3 12L9.26 10.91L6 6L10.91 8.26L12 2Z"
								stroke="white" strokeWidth="1.5" strokeLinejoin="round" fill="none"
							/>
						</svg>
					</div>
					<div>
						<h1 className="font-source-sans-pro text-[24px] font-semibold leading-[32px] text-[#111827]">
							Build with AI
						</h1>
						<p className="font-lato text-[14px] leading-[20px] text-[#6B7280]">
							Agree the requirement, then let Zango Agent build it into this app
						</p>
					</div>
				</div>
			</div>

			{blocked ? (
				<div className="mx-[40px] mt-[20px] rounded-[8px] border border-[#FCD34D] bg-[#FFFBEB] px-[16px] py-[12px]">
					<p className="font-lato text-[13px] font-semibold text-[#92400E]">
						Build with AI is not ready for this app
					</p>
					<ul className="mt-[4px] list-disc pl-[18px]">
						{availability.reasons.map((r) => (
							<li key={r} className="font-lato text-[13px] text-[#92400E]">
								{REASON_TEXT[r] || r}
							</li>
						))}
					</ul>
				</div>
			) : null}

			<div className="flex min-h-0 grow flex-col px-[40px] py-[24px]">
				<Routes>
					<Route path="/" element={<RequirementList availability={availability} />} />
					<Route path="requirements/:requirementId" element={<RequirementChat />} />
					<Route path="runs/:runId" element={<RunProgress />} />
				</Routes>
			</div>
		</div>
	);
}
