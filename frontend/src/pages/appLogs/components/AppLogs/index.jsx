import { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import BreadCrumbs from '../../../app/components/BreadCrumbs';
import AccessLogs from '../AccessLogs';
import ApplicationLogs from '../ApplicationLogs';
import FrameworkLogs from '../FrameworkLogs';

const tabs = [
	{
		id: 'access',
		label: 'Access Logs',
		icon: () => (
			<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
				<path d="M8 8a3 3 0 100-6 3 3 0 000 6zM12.735 14c.618 0 1.093-.561.872-1.139a6.002 6.002 0 00-11.215 0c-.22.578.254 1.139.872 1.139h9.47z" />
			</svg>
		),
		description: 'User login and session activities',
	},
	{
		id: 'application',
		label: 'Application Logs',
		icon: () => (
			<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
				<rect x="2" y="2" width="5" height="5" rx="1" fillOpacity="0.3"/>
				<rect x="9" y="2" width="5" height="5" rx="1" fillOpacity="0.3"/>
				<rect x="2" y="9" width="5" height="5" rx="1" fillOpacity="0.3"/>
				<rect x="9" y="9" width="5" height="5" rx="1" fillOpacity="0.3"/>
			</svg>
		),
		description: 'Changes to application data models',
	},
	{
		id: 'framework',
		label: 'Framework Logs',
		icon: () => (
			<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
				<path d="M8 1L2 4V8L8 11L14 8V4L8 1Z" fillOpacity="0.3"/>
				<path d="M8 1L2 4V8L8 11L14 8V4L8 1Z" stroke="currentColor" strokeWidth="1.2" fill="none"/>
				<path d="M2 4L8 7L14 4" stroke="currentColor" strokeWidth="1.2"/>
				<path d="M8 7V11" stroke="currentColor" strokeWidth="1.2"/>
			</svg>
		),
		description: 'System and framework changes',
	},
];

export default function AppLogs() {
	const location = useLocation();
	const navigate = useNavigate();
	const { appId } = useParams();

	// Get the active tab from URL hash or default to 'access'
	const getActiveTab = () => {
		const hash = location.hash.replace('#', '');
		return tabs.find(tab => tab.id === hash) ? hash : 'access';
	};

	const [activeTab, setActiveTab] = useState(getActiveTab());

	// Update active tab when location changes
	useEffect(() => {
		setActiveTab(getActiveTab());
	}, [location]);

	// Handle tab change
	const handleTabChange = (tabId) => {
		navigate(`#${tabId}`, { replace: true });
		setActiveTab(tabId);
	};

	return (
		<div className="flex flex-col h-full bg-[#F8FAFC] overflow-hidden">
			{/* Header */}
			<div className="bg-white border-b border-[#E5E7EB] px-[40px] py-[20px] flex-shrink-0">
				<div className="flex items-center justify-between">
					<div>
						<BreadCrumbs />
						<div className="flex items-center gap-[12px] mt-[8px]">
							<div className="flex h-[40px] w-[40px] items-center justify-center rounded-[8px] bg-gradient-to-br from-[#5048ED] to-[#346BD4] shadow-lg">
								<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
									<path d="M4 6H20M4 10H20M4 14H20M4 18H12" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
									<circle cx="17" cy="17" r="3" stroke="white" strokeWidth="2"/>
									<path d="M19.5 19.5L21 21" stroke="white" strokeWidth="2" strokeLinecap="round"/>
								</svg>
							</div>
							<div>
								<h1 className="font-source-sans-pro text-[24px] font-semibold leading-[32px] text-[#111827]">
									Logs
								</h1>
								<p className="font-lato text-[14px] leading-[20px] text-[#6B7280]">
									Monitor application activities and system changes
								</p>
							</div>
						</div>
					</div>
				</div>
			</div>

			{/* Tab Navigation */}
			<div className="bg-white border-b border-[#E5E7EB] px-[40px] flex-shrink-0">
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
								<Icon className={`h-[16px] w-[16px] ${isActive ? 'text-[#346BD4]' : 'text-[#6B7280]'}`} />
								<span className="font-lato text-[14px] font-medium">
									{tab.label}
								</span>
							</button>
						);
					})}
				</div>
			</div>

			{/* Content */}
			<div className="flex-1 px-[40px] py-[32px] bg-[#F8FAFC] overflow-y-auto">
				{activeTab === 'access' && <AccessLogs />}
				{activeTab === 'application' && <ApplicationLogs />}
				{activeTab === 'framework' && <FrameworkLogs />}
			</div>
		</div>
	);
}