import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import useApi from '../../../../hooks/useApi';
import BreadCrumbs from '../../../app/components/BreadCrumbs';
import {
	selectAppCodebaseData,
	setAppCodebaseData,
} from '../../slice';
import CodeSummary from '../CodeSummary';
import DataModels from '../DataModels';
import Routes from '../Routes';
import Policies from '../Policies';
import Packages from '../Packages';
import AsyncTasks from '../AsyncTasks';

const tabs = [
	{
		id: 'summary',
		label: 'Summary',
		icon: () => (
			<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
				<rect x="2" y="2" width="5" height="5" rx="1" fillOpacity="0.3"/>
				<rect x="9" y="2" width="5" height="5" rx="1" fillOpacity="0.3"/>
				<rect x="2" y="9" width="5" height="5" rx="1" fillOpacity="0.3"/>
				<rect x="9" y="9" width="5" height="5" rx="1" fillOpacity="0.3"/>
			</svg>
		),
		description: 'Overview of the codebase structure',
	},
	{
		id: 'datamodels',
		label: 'Data Models',
		icon: () => (
			<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
				<path d="M8 2C11.314 2 14 3.343 14 5V11C14 12.657 11.314 14 8 14C4.686 14 2 12.657 2 11V5C2 3.343 4.686 2 8 2Z" fillOpacity="0.3"/>
				<ellipse cx="8" cy="5" rx="6" ry="3" stroke="currentColor" strokeWidth="1.2" fill="none"/>
				<path d="M2 5V11C2 12.657 4.686 14 8 14C11.314 14 14 12.657 14 11V5" stroke="currentColor" strokeWidth="1.2"/>
				<path d="M2 8C2 9.657 4.686 11 8 11C11.314 11 14 9.657 14 8" stroke="currentColor" strokeWidth="1.2"/>
			</svg>
		),
		description: 'Explore data models across modules',
	},
	{
		id: 'routes',
		label: 'Routes',
		icon: () => (
			<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
				<path d="M2 8H14" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
				<path d="M8 2V14" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
				<circle cx="8" cy="8" r="2" fillOpacity="0.3"/>
				<circle cx="3" cy="8" r="1.5" fillOpacity="0.3"/>
				<circle cx="13" cy="8" r="1.5" fillOpacity="0.3"/>
				<circle cx="8" cy="3" r="1.5" fillOpacity="0.3"/>
				<circle cx="8" cy="13" r="1.5" fillOpacity="0.3"/>
			</svg>
		),
		description: 'Application and package routes',
	},
	{
		id: 'policies',
		label: 'Policies',
		icon: () => (
			<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
				<path d="M8 2L3 5V8C3 11.04 4.88 13.64 8 14C11.12 13.64 13 11.04 13 8V5L8 2Z" fillOpacity="0.3"/>
				<path d="M8 2L3 5V8C3 11.04 4.88 13.64 8 14C11.12 13.64 13 11.04 13 8V5L8 2Z" stroke="currentColor" strokeWidth="1.2" fill="none"/>
				<path d="M6 8L7.5 9.5L10 7" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
			</svg>
		),
		description: 'Security policies in modules',
	},
	{
		id: 'packages',
		label: 'Packages',
		icon: () => (
			<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
				<path d="M8 1L2 4V8L8 11L14 8V4L8 1Z" fillOpacity="0.3"/>
				<path d="M8 1L2 4V8L8 11L14 8V4L8 1Z" stroke="currentColor" strokeWidth="1.2" fill="none"/>
				<path d="M2 4L8 7L14 4" stroke="currentColor" strokeWidth="1.2"/>
				<path d="M8 7V11" stroke="currentColor" strokeWidth="1.2"/>
			</svg>
		),
		description: 'Installed and available packages',
	},
	{
		id: 'asynctasks',
		label: 'Async Tasks',
		icon: () => (
			<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
				<circle cx="8" cy="8" r="6" fillOpacity="0.3" stroke="currentColor" strokeWidth="1.2" fill="none"/>
				<path d="M8 4V8L10.5 10.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
				<circle cx="8" cy="8" r="1" fill="currentColor"/>
			</svg>
		),
		description: 'Background tasks and scheduled jobs',
	},
];

export default function AppCode() {
	const location = useLocation();
	const navigate = useNavigate();
	const { appId } = useParams();
	const dispatch = useDispatch();
	const triggerApi = useApi();

	// Get the active tab from URL hash or default to 'summary'
	const getActiveTab = () => {
		const hash = location.hash.replace('#', '');
		return tabs.find(tab => tab.id === hash) ? hash : 'summary';
	};

	const [activeTab, setActiveTab] = useState(getActiveTab());
	const appCodebaseData = useSelector(selectAppCodebaseData);

	// Update active tab when location changes
	useEffect(() => {
		setActiveTab(getActiveTab());
	}, [location]);

	// Handle tab change
	const handleTabChange = (tabId) => {
		navigate(`#${tabId}`, { replace: true });
		setActiveTab(tabId);
	};

	// Fetch app codebase data
	useEffect(() => {
		const fetchAppCodebase = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/codebase/`,
				type: 'GET',
				loader: true,
			});
			if (success && response?.app_codebase) {
				dispatch(setAppCodebaseData(response.app_codebase));
			}
		};

		fetchAppCodebase();
	}, [appId]);

	if (!appCodebaseData) {
		return null;
	}

	return (
		<div className="flex min-h-screen grow flex-col bg-[#F8FAFC]">
			{/* Header */}
			<div className="bg-white border-b border-[#E5E7EB] px-[40px] py-[20px]">
				<div className="flex items-center justify-between">
					<div>
						<BreadCrumbs />
						<div className="flex items-center gap-[12px] mt-[8px]">
							<div className="flex h-[40px] w-[40px] items-center justify-center rounded-[8px] bg-gradient-to-br from-[#5048ED] to-[#346BD4] shadow-lg">
								<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
									<path d="M14 2L14 8C14 8.55228 14.4477 9 15 9L21 9" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
									<path d="M17 21H7C5.89543 21 5 20.1046 5 19V5C5 3.89543 5.89543 3 7 3H14L19 8V19C19 20.1046 18.1046 21 17 21Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
									<path d="M9 13H15" stroke="white" strokeWidth="2" strokeLinecap="round"/>
									<path d="M9 17H12" stroke="white" strokeWidth="2" strokeLinecap="round"/>
								</svg>
							</div>
							<div>
								<h1 className="font-source-sans-pro text-[24px] font-semibold leading-[32px] text-[#111827]">
									Code
								</h1>
								<p className="font-lato text-[14px] leading-[20px] text-[#6B7280]">
									Explore and understand your application's codebase structure
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
			<div className="flex-1 overflow-auto">
				{activeTab === 'summary' && (
					<div className="px-[40px] py-[32px] bg-[#F8FAFC] min-h-[calc(100vh-200px)]">
						<CodeSummary data={appCodebaseData} />
					</div>
				)}
				
				{activeTab === 'datamodels' && (
					<div className="px-[40px] py-[32px] bg-[#F8FAFC] min-h-[calc(100vh-200px)]">
						<DataModels data={appCodebaseData} />
					</div>
				)}
				
				{activeTab === 'routes' && (
					<div className="px-[40px] py-[32px] bg-[#F8FAFC] min-h-[calc(100vh-200px)]">
						<Routes data={appCodebaseData} />
					</div>
				)}
				
				{activeTab === 'policies' && (
					<div className="px-[40px] py-[32px] bg-[#F8FAFC] min-h-[calc(100vh-200px)]">
						<Policies data={appCodebaseData} />
					</div>
				)}
				
				{activeTab === 'packages' && (
					<div className="px-[40px] py-[32px] bg-[#F8FAFC] min-h-[calc(100vh-200px)]">
						<Packages data={appCodebaseData} />
					</div>
				)}
				
				{activeTab === 'asynctasks' && (
					<div className="px-[40px] py-[32px] bg-[#F8FAFC] min-h-[calc(100vh-200px)]">
						<AsyncTasks />
					</div>
				)}
			</div>
		</div>
	);
}