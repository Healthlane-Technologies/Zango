import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import useApi from '../../../../hooks/useApi';
import BreadCrumbs from '../../../app/components/BreadCrumbs';
import { ReactComponent as SettingsIcon } from '../../../../assets/images/svg/app-settings-icon.svg';
import { ReactComponent as ShieldIcon } from '../../../../assets/images/svg/app-policy-icon.svg';
import { ReactComponent as PaletteIcon } from '../../../../assets/images/svg/add-theme-icon.svg';
import { ReactComponent as UserRoleIcon } from '../../../../assets/images/svg/app-user-role-icon.svg';
import { ReactComponent as AppSecretsIcon } from '../../../../assets/images/svg/app-secrets-icon.svg';
import {
	selectAppConfigurationData,
	selectRerenderPage,
	setAppConfigurationData,
} from '../../slice';
import {
	selectAppThemeConfigurationData,
	setAppThemeConfigurationData,
	selectRerenderPage as selectThemeRerenderPage,
} from '../../../appThemeConfiguration/slice';
import {
	selectAppSecretsData,
	setAppSecretsData,
	selectRerenderPage as selectSecretsRerenderPage,
} from '../../../appSecretsRoutes/slice/Index';
import AppConfiguration from '../AppConfiguration';
import ModernAuthConfig from '../AppConfiguration/AuthConfiguration/ModernAuthConfig';
import AppThemeConfiguration from '../../../appThemeConfiguration/components/AppThemeConfiguration';
import ModernUserRolesConfiguration from '../../../appUserRoles/components/ModernUserRolesConfiguration';
import Secrets from '../../../appSecretsRoutes/components/Secrets/Index';

const tabs = [
	{
		id: 'basic',
		label: 'Basic Information',
		icon: () => (
			<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
				<path d="M8 8C9.10457 8 10 7.10457 10 6C10 4.89543 9.10457 4 8 4C6.89543 4 6 4.89543 6 6C6 7.10457 6.89543 8 8 8Z" fillOpacity="0.3"/>
				<path d="M8 9C5.79086 9 4 10.7909 4 13H12C12 10.7909 10.2091 9 8 9Z" fillOpacity="0.3"/>
				<path d="M8 1.5C4.41015 1.5 1.5 4.41015 1.5 8C1.5 11.5899 4.41015 14.5 8 14.5C11.5899 14.5 14.5 11.5899 14.5 8C14.5 4.41015 11.5899 1.5 8 1.5Z" stroke="currentColor" strokeWidth="1.2" fill="none"/>
			</svg>
		),
		description: 'App details and settings',
	},
	{
		id: 'themes',
		label: 'Themes',
		icon: () => (
			<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
				<circle cx="8" cy="8" r="5" fillOpacity="0.3"/>
				<path d="M8 3C5.24 3 3 5.24 3 8C3 10.76 5.24 13 8 13C10.76 13 13 10.76 13 8C13 5.24 10.76 3 8 3Z" stroke="currentColor" strokeWidth="1.2" fill="none"/>
				<path d="M8 3V8L11 11" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
			</svg>
		),
		description: 'Colors & typography',
	},
	{
		id: 'roles',
		label: 'User Roles',
		icon: () => (
			<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
				<circle cx="6" cy="5" r="2" fillOpacity="0.3"/>
				<path d="M9 11H3C3 9.34 4.34 8 6 8C7.66 8 9 9.34 9 11Z" fillOpacity="0.3"/>
				<circle cx="11" cy="5" r="1.5" stroke="currentColor" strokeWidth="1.2" fill="none"/>
				<path d="M13 10C13 8.9 12.1 8 11 8C10.7 8 10.4 8.1 10.2 8.2" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
			</svg>
		),
		description: 'Roles & permissions',
	},
	{
		id: 'auth',
		label: 'Authentication',
		icon: () => (
			<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
				<path d="M8 2L3 5V8C3 11.04 4.88 13.64 8 14C11.12 13.64 13 11.04 13 8V5L8 2Z" fillOpacity="0.3"/>
				<path d="M8 2L3 5V8C3 11.04 4.88 13.64 8 14C11.12 13.64 13 11.04 13 8V5L8 2Z" stroke="currentColor" strokeWidth="1.2" fill="none"/>
				<path d="M6 8L7.5 9.5L10 7" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
			</svg>
		),
		description: 'Login methods & security',
	},
	{
		id: 'secrets',
		label: 'Secrets',
		icon: () => <AppSecretsIcon />,
		description: 'Manage app secrets',
	},
];

export default function UnifiedAppSettings() {
	const location = useLocation();
	const navigate = useNavigate();
	const { appId } = useParams();
	const dispatch = useDispatch();
	const triggerApi = useApi();

	// Get the active tab from URL hash or default to 'basic'
	const getActiveTab = () => {
		const hash = location.hash.replace('#', '');
		return tabs.find(tab => tab.id === hash) ? hash : 'basic';
	};

	const [activeTab, setActiveTab] = useState(getActiveTab());
	
	const rerenderPage = useSelector(selectRerenderPage);
	const themeRerenderPage = useSelector(selectThemeRerenderPage);
	const secretsRerenderPage = useSelector(selectSecretsRerenderPage);
	const appConfigurationData = useSelector(selectAppConfigurationData);
	const appThemeConfigurationData = useSelector(selectAppThemeConfigurationData);
	const appSecretsData = useSelector(selectAppSecretsData);

	// Update active tab when location changes
	useEffect(() => {
		setActiveTab(getActiveTab());
	}, [location]);

	// Handle tab change
	const handleTabChange = (tabId) => {
		navigate(`#${tabId}`, { replace: true });
		setActiveTab(tabId);
	};

	// Fetch app configuration data
	useEffect(() => {
		const fetchAppConfig = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}?include_dropdown_options=true`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				dispatch(setAppConfigurationData(response));
			}
		};

		fetchAppConfig();
	}, [appId, rerenderPage]);

	// Fetch theme configuration data when themes tab is active
	useEffect(() => {
		if (activeTab === 'themes') {
			const fetchThemeConfig = async () => {
				const { response, success } = await triggerApi({
					url: `/api/v1/apps/${appId}/themes/?include_dropdown_options=true`,
					type: 'GET',
					loader: true,
				});
				if (success && response) {
					dispatch(setAppThemeConfigurationData(response));
				}
			};

			fetchThemeConfig();
		}
	}, [appId, activeTab, themeRerenderPage]);

	if (!appConfigurationData) {
		return null;
	}

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
									<path d="M12 15C13.6569 15 15 13.6569 15 12C15 10.3431 13.6569 9 12 9C10.3431 9 9 10.3431 9 12C9 13.6569 10.3431 15 12 15Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
									<path d="M19.4 15C19.2669 15.3016 19.2272 15.6362 19.286 15.9606C19.3448 16.285 19.4995 16.5843 19.73 16.82L19.79 16.88C19.976 17.0657 20.1235 17.2863 20.2241 17.5291C20.3248 17.7719 20.3766 18.0322 20.3766 18.295C20.3766 18.5578 20.3248 18.8181 20.2241 19.0609C20.1235 19.3037 19.976 19.5243 19.79 19.71C19.6043 19.896 19.3837 20.0435 19.1409 20.1441C18.8981 20.2448 18.6378 20.2966 18.375 20.2966C18.1122 20.2966 17.8519 20.2448 17.6091 20.1441C17.3663 20.0435 17.1457 19.896 16.96 19.71L16.9 19.65C16.6643 19.4195 16.365 19.2648 16.0406 19.206C15.7162 19.1472 15.3816 19.1869 15.08 19.32C14.7842 19.4468 14.532 19.6572 14.3543 19.9255C14.1766 20.1938 14.0813 20.5082 14.08 20.83V21C14.08 21.5304 13.8693 22.0391 13.4942 22.4142C13.1191 22.7893 12.6104 23 12.08 23C11.5496 23 11.0409 22.7893 10.6658 22.4142C10.2907 22.0391 10.08 21.5304 10.08 21V20.91C10.0723 20.579 9.96512 20.258 9.77251 19.9887C9.5799 19.7194 9.31074 19.5143 9 19.4C8.69838 19.2669 8.36381 19.2272 8.03941 19.286C7.71502 19.3448 7.41568 19.4995 7.18 19.73L7.12 19.79C6.93425 19.976 6.71368 20.1235 6.47088 20.2241C6.22808 20.3248 5.96783 20.3766 5.705 20.3766C5.44217 20.3766 5.18192 20.3248 4.93912 20.2241C4.69632 20.1235 4.47575 19.976 4.29 19.79C4.10405 19.6043 3.95653 19.3837 3.85588 19.1409C3.75523 18.8981 3.70343 18.6378 3.70343 18.375C3.70343 18.1122 3.75523 17.8519 3.85588 17.6091C3.95653 17.3663 4.10405 17.1457 4.29 16.96L4.35 16.9C4.58054 16.6643 4.73519 16.365 4.794 16.0406C4.85282 15.7162 4.81312 15.3816 4.68 15.08C4.55324 14.7842 4.34276 14.532 4.07447 14.3543C3.80618 14.1766 3.49179 14.0813 3.17 14.08H3C2.46957 14.08 1.96086 13.8693 1.58579 13.4942C1.21071 13.1191 1 12.6104 1 12.08C1 11.5496 1.21071 11.0409 1.58579 10.6658C1.96086 10.2907 2.46957 10.08 3 10.08H3.09C3.42099 10.0723 3.742 9.96512 4.0113 9.77251C4.28059 9.5799 4.48572 9.31074 4.6 9C4.73312 8.69838 4.77282 8.36381 4.714 8.03941C4.65519 7.71502 4.50054 7.41568 4.27 7.18L4.21 7.12C4.02405 6.93425 3.87653 6.71368 3.77588 6.47088C3.67523 6.22808 3.62343 5.96783 3.62343 5.705C3.62343 5.44217 3.67523 5.18192 3.77588 4.93912C3.87653 4.69632 4.02405 4.47575 4.21 4.29C4.39575 4.10405 4.61632 3.95653 4.85912 3.85588C5.10192 3.75523 5.36217 3.70343 5.625 3.70343C5.88783 3.70343 6.14808 3.75523 6.39088 3.85588C6.63368 3.95653 6.85425 4.10405 7.04 4.29L7.1 4.35C7.33568 4.58054 7.63502 4.73519 7.95941 4.794C8.28381 4.85282 8.61838 4.81312 8.92 4.68H9C9.29577 4.55324 9.54802 4.34276 9.72569 4.07447C9.90337 3.80618 9.99872 3.49179 10 3.17V3C10 2.46957 10.2107 1.96086 10.5858 1.58579C10.9609 1.21071 11.4696 1 12 1C12.5304 1 13.0391 1.21071 13.4142 1.58579C13.7893 1.96086 14 2.46957 14 3V3.09C14.0013 3.41179 14.0966 3.72618 14.2743 3.99447C14.452 4.26276 14.7042 4.47324 15 4.6C15.3016 4.73312 15.6362 4.77282 15.9606 4.714C16.285 4.65519 16.5843 4.50054 16.82 4.27L16.88 4.21C17.0657 4.02405 17.2863 3.87653 17.5291 3.77588C17.7719 3.67523 18.0322 3.62343 18.295 3.62343C18.5578 3.62343 18.8181 3.67523 19.0609 3.77588C19.3037 3.87653 19.5243 4.02405 19.71 4.21C19.896 4.39575 20.0435 4.61632 20.1441 4.85912C20.2448 5.10192 20.2966 5.36217 20.2966 5.625C20.2966 5.88783 20.2448 6.14808 20.1441 6.39088C20.0435 6.63368 19.896 6.85425 19.71 7.04L19.65 7.1C19.4195 7.33568 19.2648 7.63502 19.206 7.95941C19.1472 8.28381 19.1869 8.61838 19.32 8.92V9C19.4468 9.29577 19.6572 9.54802 19.9255 9.72569C20.1938 9.90337 20.5082 9.99872 20.83 10H21C21.5304 10 22.0391 10.2107 22.4142 10.5858C22.7893 10.9609 23 11.4696 23 12C23 12.5304 22.7893 13.0391 22.4142 13.4142C22.0391 13.7893 21.5304 14 21 14H20.91C20.5882 14.0013 20.2738 14.0966 20.0055 14.2743C19.7372 14.452 19.5268 14.7042 19.4 15Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
								</svg>
							</div>
							<div>
								<h1 className="font-source-sans-pro text-[24px] font-semibold leading-[32px] text-[#111827]">
									App Settings
								</h1>
								<p className="font-lato text-[14px] leading-[20px] text-[#6B7280]">
									Manage your application configuration, authentication, and themes
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
				{activeTab === 'basic' && <AppConfiguration />}
				{activeTab === 'auth' && <ModernAuthConfig />}
				{activeTab === 'themes' && <AppThemeConfiguration />}
				{activeTab === 'roles' && <ModernUserRolesConfiguration />}
				{activeTab === 'secrets' && <Secrets />}
			</div>
		</div>
	);
}