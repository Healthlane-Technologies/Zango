/**
 * Agent Mode shell.
 *
 * Two phases: gather and approve a requirement, then commit to a build.
 * Nothing is written to the app until a requirement has been approved.
 *
 * Deliberately spare chrome. This screen is a conversation on one side and
 * the app being built on the other, and both want the room — so there is no
 * left menu, no breadcrumb trail, and the header is one line naming the app
 * you are working on.
 */
import { useCallback, useEffect, useState } from 'react';
import { Navigate, Route, Routes, useNavigate, useParams } from 'react-router-dom';
import useApi from '../../../hooks/useApi';
import BuildThread from './BuildThread';
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
	const navigate = useNavigate();
	const triggerApi = useApi();
	const [availability, setAvailability] = useState(null);
	const [app, setApp] = useState(null);

	const load = useCallback(async () => {
		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/agent-mode/availability/`,
			type: 'GET', loader: false, showErrorModal: false,
		});
		if (success && response) setAvailability(response);
	}, [appId]);

	// Outside the app shell there is no PlatformAppRoutes to have fetched this,
	// and the header has nothing to name the app with otherwise.
	const loadApp = useCallback(async () => {
		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}`,
			type: 'GET', loader: false, showErrorModal: false,
		});
		if (success && response?.app) setApp(response.app);
	}, [appId]);

	useEffect(() => { load(); loadApp(); }, [appId]);

	const blocked = availability && !availability.available;

	return (
		<div className="flex h-full flex-col overflow-hidden bg-[#F8FAFC]">
			<div className="flex flex-shrink-0 items-center justify-between gap-[16px] border-b border-[#E5E7EB] bg-white px-[24px] py-[12px]">
				<div className="flex min-w-0 items-center gap-[10px]">
					<div className="flex h-[30px] w-[30px] shrink-0 items-center justify-center rounded-[7px] bg-gradient-to-br from-[#5048ED] to-[#346BD4] shadow">
						<svg width="17" height="17" viewBox="0 0 24 24" fill="none">
							<path
								d="M12 2L13.09 8.26L18 6L14.74 10.91L21 12L14.74 13.09L18 18L13.09 15.74L12 22L10.91 15.74L6 18L9.26 13.09L3 12L9.26 10.91L6 6L10.91 8.26L12 2Z"
								stroke="white" strokeWidth="1.5" strokeLinejoin="round" fill="none"
							/>
						</svg>
					</div>
					<h1 className="truncate font-source-sans-pro text-[19px] font-semibold leading-[26px] text-[#111827]">
						{app?.name || ' '}
					</h1>
					<span className="shrink-0 rounded-full bg-[#EEF2FF] px-[8px] py-[2px] font-lato text-[10px] font-bold uppercase tracking-[0.05em] text-[#3730A3]">
						Build with AI
					</span>
				</div>
				{/* The only way back: without the left menu this screen would
				    otherwise be a dead end. */}
				<button
					onClick={() => navigate(`/platform/apps/${appId}/app-settings/app-configuration/`)}
					className="shrink-0 rounded-[6px] border border-[#DDE2E5] px-[12px] py-[5px] font-lato text-[12.5px] font-medium text-[#6B7280] hover:bg-[#F0F3F4] hover:text-[#111827]"
				>
					App panel
				</button>
			</div>

			{blocked ? (
				<div className="mx-[24px] mt-[12px] rounded-[8px] border border-[#FCD34D] bg-[#FFFBEB] px-[16px] py-[10px]">
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

			<div className="flex min-h-0 grow flex-col px-[16px] py-[12px]">
				<Routes>
					<Route path="/" element={<BuildThread />} />
					{/* Every version lives in the one thread now; a link to a
					    single requirement lands there. */}
					<Route path="requirements/:requirementId" element={<Navigate to=".." replace />} />
					<Route path="runs/:runId" element={<RunProgress />} />
				</Routes>
			</div>
		</div>
	);
}
