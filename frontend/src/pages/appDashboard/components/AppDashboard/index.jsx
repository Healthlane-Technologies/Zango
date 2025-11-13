import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import useApi from '../../../../hooks/useApi';
import BreadCrumbs from '../../../app/components/BreadCrumbs';
import { selectAppConfigurationData } from '../../../appConfiguration/slice';
import BasicInfoCard from '../ConfigurationCards/BasicInfoCard';
import AuthConfigCard from '../ConfigurationCards/AuthConfigCard';
import ThemeConfigCard from '../ConfigurationCards/ThemeConfigCard';
import UsersRolesCard from '../ConfigurationCards/UsersRolesCard';
import DashboardHeader from './DashboardHeader';
import QuickStats from './QuickStats';

export default function AppDashboard() {
	const { appId } = useParams();
	const dispatch = useDispatch();
	const triggerApi = useApi();
	
	const appConfigurationData = useSelector(selectAppConfigurationData);

	useEffect(() => {
		// Fetch dashboard data
		const fetchDashboardData = async () => {
			// For now, we'll use existing endpoints
			// Later, we'll create a unified dashboard endpoint
			
			// Fetch app configuration if not already loaded
			if (!appConfigurationData) {
				const { response, success } = await triggerApi({
					url: `/api/v1/apps/${appId}?include_dropdown_options=true`,
					type: 'GET',
					loader: true,
				});
			}
		};

		fetchDashboardData();
	}, [appId]);

	return (
		<div className="flex grow flex-col">
			{/* Breadcrumbs */}
			<div className="px-[40px] py-[12px]">
				<BreadCrumbs />
			</div>

			{/* Dashboard Content */}
			<div className="flex grow flex-col gap-[24px] overflow-y-auto px-[40px] pb-[40px]">
				{/* Dashboard Header */}
				<DashboardHeader appData={appConfigurationData} />
				
				{/* Quick Stats */}
				<QuickStats />

				{/* Configuration Cards Grid */}
				<div className="grid grid-cols-1 gap-[20px] lg:grid-cols-2 xl:grid-cols-2">
					<BasicInfoCard appData={appConfigurationData} />
					<AuthConfigCard appId={appId} />
					<ThemeConfigCard appId={appId} />
					<UsersRolesCard appId={appId} />
				</div>
			</div>
		</div>
	);
}