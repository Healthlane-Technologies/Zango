import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import BreadCrumbs from '../../app/components/BreadCrumbs';
import Providers from './Providers';
import Agents from './Agents';
import Prompts from './Prompts';
import Tools from './Tools';
import InvocationLogs from './InvocationLogs';

const tabs = [
	{
		id: 'agents',
		label: 'Agents',
		icon: () => (
			<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
				<circle cx="8" cy="5" r="3" fillOpacity="0.3" stroke="currentColor" strokeWidth="1.2" fill="none"/>
				<path d="M3 14C3 11.239 5.239 9 8 9C10.761 9 13 11.239 13 14" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
			</svg>
		),
	},
	{
		id: 'providers',
		label: 'Providers',
		icon: () => (
			<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
				<path d="M8 1L2 4V8L8 11L14 8V4L8 1Z" fillOpacity="0.3"/>
				<path d="M8 1L2 4V8L8 11L14 8V4L8 1Z" stroke="currentColor" strokeWidth="1.2" fill="none"/>
				<path d="M2 4L8 7L14 4" stroke="currentColor" strokeWidth="1.2"/>
				<path d="M8 7V11" stroke="currentColor" strokeWidth="1.2"/>
			</svg>
		),
	},
	{
		id: 'prompts',
		label: 'Prompts',
		icon: () => (
			<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
				<path d="M3 3H13V11H8L5 14V11H3V3Z" fillOpacity="0.3"/>
				<path d="M3 3H13V11H8L5 14V11H3V3Z" stroke="currentColor" strokeWidth="1.2" fill="none" strokeLinejoin="round"/>
			</svg>
		),
	},
	{
		id: 'tools',
		label: 'Tools',
		icon: () => (
			<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
				<path d="M10.5 1.5L14.5 5.5L5.5 14.5H1.5V10.5L10.5 1.5Z" fillOpacity="0.3"/>
				<path d="M10.5 1.5L14.5 5.5L5.5 14.5H1.5V10.5L10.5 1.5Z" stroke="currentColor" strokeWidth="1.2" fill="none" strokeLinejoin="round"/>
			</svg>
		),
	},
	{
		id: 'guardrails',
		label: 'Guardrails',
		icon: () => (
			<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
				<path d="M8 2L3 5V8C3 11.04 4.88 13.64 8 14C11.12 13.64 13 11.04 13 8V5L8 2Z" fillOpacity="0.3"/>
				<path d="M8 2L3 5V8C3 11.04 4.88 13.64 8 14C11.12 13.64 13 11.04 13 8V5L8 2Z" stroke="currentColor" strokeWidth="1.2" fill="none"/>
			</svg>
		),
	},
	{
		id: 'invocation-logs',
		label: 'Invocation Logs',
		icon: () => (
			<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
				<path d="M2 4H14M2 7H14M2 10H14M2 13H9" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
			</svg>
		),
	},
];

export default function AppAi() {
	const location = useLocation();
	const navigate = useNavigate();

	const getActiveTab = () => {
		const hash = location.hash.replace('#', '');
		return tabs.find((tab) => tab.id === hash) ? hash : 'agents';
	};

	const [activeTab, setActiveTab] = useState(getActiveTab());

	useEffect(() => {
		setActiveTab(getActiveTab());
	}, [location]);

	const handleTabChange = (tabId) => {
		navigate(`#${tabId}`, { replace: true });
		setActiveTab(tabId);
	};

	return (
		<div className="flex min-h-screen grow flex-col bg-[#F8FAFC]">
			{/* Header */}
			<div className="bg-white border-b border-[#E5E7EB] px-[40px] py-[20px]">
				<div className="flex items-center justify-between">
					<div>
						<BreadCrumbs />
						<div className="flex items-center gap-[12px] mt-[8px]">
							<div className="flex h-[40px] w-[40px] items-center justify-center rounded-[8px] bg-gradient-to-br from-[#F59E0B] to-[#D97706] shadow-lg">
								<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
									<path d="M12 2L13.09 8.26L18 6L14.74 10.91L21 12L14.74 13.09L18 18L13.09 15.74L12 22L10.91 15.74L6 18L9.26 13.09L3 12L9.26 10.91L6 6L10.91 8.26L12 2Z" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
								</svg>
							</div>
							<div>
								<h1 className="font-source-sans-pro text-[24px] font-semibold leading-[32px] text-[#111827]">
									Agent Studio
								</h1>
								<p className="font-lato text-[14px] leading-[20px] text-[#6B7280]">
									Setup and Manage compliant agents | Build intelligent agentic apps
								</p>
							</div>
						</div>
					</div>
				</div>
			</div>

			{/* Tab Navigation */}
			<div className="bg-white border-b border-[#E5E7EB] px-[40px]">
				<div className="flex gap-[32px]">
					{tabs.map((tab) => {
						const Icon = tab.icon;
						const isActive = activeTab === tab.id;

						return (
							<button
								key={tab.id}
								onClick={() => handleTabChange(tab.id)}
								className={`flex items-center gap-[8px] py-[16px] px-[4px] border-b-[3px] transition-all ${
									isActive
										? 'border-[#346BD4] text-[#346BD4]'
										: 'border-transparent text-[#6B7280] hover:text-[#111827]'
								}`}
							>
								<Icon />
								<span className="font-lato text-[14px] font-medium">
									{tab.label}
								</span>
							</button>
						);
					})}
				</div>
			</div>

			{/* Content */}
			<div className="flex-1 overflow-auto">
				{activeTab === 'providers' && (
					<div className="px-[40px] py-[32px] bg-[#F8FAFC] min-h-[calc(100vh-200px)]">
						<Providers />
					</div>
				)}

{activeTab === 'agents' && (
					<div className="px-[40px] py-[32px] bg-[#F8FAFC] min-h-[calc(100vh-200px)]">
						<Agents />
					</div>
				)}

				{activeTab === 'prompts' && (
					<div className="px-[40px] py-[32px] bg-[#F8FAFC] min-h-[calc(100vh-200px)]">
						<Prompts />
					</div>
				)}

				{activeTab === 'tools' && (
					<div className="px-[40px] py-[32px] bg-[#F8FAFC] min-h-[calc(100vh-200px)]">
						<Tools />
					</div>
				)}

				{activeTab === 'guardrails' && (
					<div className="px-[40px] py-[32px] bg-[#F8FAFC] min-h-[calc(100vh-200px)]">
						<p className="text-[#6B7280] font-lato text-[14px]">Guardrails coming soon.</p>
					</div>
				)}

				{activeTab === 'invocation-logs' && (
					<div className="px-[40px] py-[32px] bg-[#F8FAFC] min-h-[calc(100vh-200px)]">
						<InvocationLogs />
					</div>
				)}
			</div>
		</div>
	);
}
