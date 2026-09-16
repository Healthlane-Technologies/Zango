import { useNavigate, useParams } from 'react-router-dom';
import BuildWithAITab from '../BuildWithAITab';
import GeneralTab from '../GeneralTab';
import LogConnectorsTab from '../LogConnectorsTab';

// Extensible — add { key, label, icon, component } here when a new
// settings tab is added.
const TABS = [
	{
		key: 'general',
		label: 'General',
		description: 'Domains and defaults applied to every newly launched app.',
		icon: (
			<svg
				xmlns="http://www.w3.org/2000/svg"
				width="16"
				height="16"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				strokeWidth="2"
			>
				<circle cx="12" cy="12" r="3" />
				<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
			</svg>
		),
		Component: GeneralTab,
	},
	{
		key: 'log-connectors',
		label: 'Log Connectors',
		description: 'Where Platform Logs fetches App / Celery output from.',
		icon: (
			<svg
				xmlns="http://www.w3.org/2000/svg"
				width="16"
				height="16"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				strokeWidth="2"
			>
				<polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
			</svg>
		),
		Component: LogConnectorsTab,
	},
	{
		key: 'build-with-ai',
		label: 'Build with AI',
		description: 'Models, credentials and limits for the requirement and build agents.',
		icon: (
			<svg
				xmlns="http://www.w3.org/2000/svg"
				width="16"
				height="16"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				strokeWidth="1.6"
				strokeLinejoin="round"
			>
				<path d="M12 2L13.09 8.26L18 6L14.74 10.91L21 12L14.74 13.09L18 18L13.09 15.74L12 22L10.91 15.74L6 18L9.26 13.09L3 12L9.26 10.91L6 6L10.91 8.26L12 2Z" />
			</svg>
		),
		Component: BuildWithAITab,
	},
];

export default function PlatformSettings() {
	const { tab = TABS[0].key } = useParams();
	const navigate = useNavigate();

	const active = TABS.find((t) => t.key === tab) || TABS[0];
	const Active = active.Component;

	return (
		<div className="flex min-h-0 grow flex-col overflow-hidden bg-[#F6F7FB]">
			<header className="flex-shrink-0 border-b border-[#E3E6EF] bg-white px-[32px] py-[18px]">
				<h1 className="text-[20px] font-semibold tracking-[-0.02em] text-[#0B0D14]">
					Settings
				</h1>
				<p className="mt-[3px] text-[12.5px] text-[#5A607A]">
					Platform-wide configuration. Changes apply to every app.
				</p>
			</header>

			<div className="flex min-h-0 grow">
				{/* Left sidebar */}
				<aside className="w-[240px] flex-shrink-0 overflow-y-auto border-r border-[#E3E6EF] bg-white px-[12px] py-[18px]">
					<div className="mb-[8px] px-[10px] text-[9.5px] font-semibold uppercase tracking-[0.08em] text-[#8389A3]">
						Configuration
					</div>
					<nav className="flex flex-col gap-[2px]">
						{TABS.map((t) => {
							const isActive = t.key === active.key;
							return (
								<button
									key={t.key}
									type="button"
									onClick={() => navigate(`/platform/settings/${t.key}`)}
									className={`group relative flex items-center gap-[10px] rounded-[6px] px-[10px] py-[8px] text-left text-[12.5px] font-medium transition-all duration-150 ${
										isActive
											? 'bg-[#EEF1FE] text-[#3938B5]'
											: 'text-[#5A607A] hover:bg-[#F0F2F7] hover:text-[#0B0D14]'
									}`}
								>
									{isActive && (
										<span
											className="absolute left-0 top-1/2 h-[16px] w-[3px] -translate-y-1/2 rounded-[2px] bg-[#5961E5]"
											aria-hidden="true"
										/>
									)}
									<span
										className={`flex h-[16px] w-[16px] items-center justify-center transition-colors ${
											isActive ? 'text-[#5961E5]' : 'text-[#8389A3]'
										}`}
									>
										{t.icon}
									</span>
									<span className="flex-1">{t.label}</span>
								</button>
							);
						})}
					</nav>
				</aside>

				{/* Tab content with fade-in on switch */}
				<main
					key={active.key}
					className="flex min-h-0 min-w-0 grow flex-col overflow-y-auto animate-tab-fade"
				>
					<div className="flex-shrink-0 border-b border-[#E3E6EF] bg-white px-[32px] py-[14px]">
						<div className="text-[14px] font-semibold text-[#0B0D14]">
							{active.label}
						</div>
						<div className="mt-[1px] text-[11.5px] text-[#5A607A]">
							{active.description}
						</div>
					</div>
					<div className="px-[32px] py-[24px]">
						<Active />
					</div>
				</main>
			</div>

			<style>{`
				@keyframes tab-fade {
					from { opacity: 0; transform: translateY(4px); }
					to   { opacity: 1; transform: translateY(0); }
				}
				.animate-tab-fade { animation: tab-fade 220ms cubic-bezier(0.22, 1, 0.36, 1) both; }
				@media (prefers-reduced-motion: reduce) {
					.animate-tab-fade { animation: none; }
				}
			`}</style>
		</div>
	);
}
