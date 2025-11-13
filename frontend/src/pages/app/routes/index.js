import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Navigate, Route, Routes, useParams } from 'react-router-dom';
import Layout from '../../../components/Layout';
import useApi from '../../../hooks/useApi';
import { AppConfigurationRoutes } from '../../appConfiguration/routes';
import { setAppConfigurationData } from '../../appConfiguration/slice';
import { AppPackagesManagementRoutes } from '../../appPackagesManagement/routes';
import { AppPermissionsManagementRoutes } from '../../appPermissionsManagement/routes';
import { AppPoliciesManagementRoutes } from '../../appPoliciesManagement/routes';
import { AppTaskManagementRoutes } from '../../appTaskManagement/routes';
import { AppThemeConfigurationRoutes } from '../../appThemeConfiguration/routes';
import AppUserManagementRoutes from '../../appUserManagement/routes';
import AppUserRolesRoutes from '../../appUserRoles/routes';
import AppDashboardRoutes from '../../appDashboard/routes';
import { selectAppPanelInitialData } from '../../platform/slice';
import Chatbot from '../components/Chatbot';
import DragablePopover from '../components/Chatbot/DragablePopover';
import SideMenu from '../components/SideMenu';
import { AppReleasesRoutes } from '../../appReleasesRoutes/routes/Index';
import appCodeRoutes from '../../appCode/routes';
import { AppLogsRoutes } from '../../appLogs/routes';

const PlatformAppRoutes = () => {
	let { appId } = useParams();

	const dispatch = useDispatch();

	const appPanelInitialData = useSelector(selectAppPanelInitialData);

	function updateAppConfigurationData(value) {
		dispatch(setAppConfigurationData(value));
	}

	const triggerApi = useApi();

	const makeApiCall = async () => {
		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}?include_dropdown_options=true`,
			type: 'GET',
			loader: true,
		});
		if (success && response) {
			updateAppConfigurationData(response);
		}
	};

	useEffect(() => {
		makeApiCall();
	}, []);

	const CodeAssist = appPanelInitialData?.is_codeassist_enabled ? (
		<>
			<div className="absolute bottom-[8px] left-[96px] z-[51]">
				<DragablePopover />
			</div>
			<Chatbot />
		</>
	) : null;

	return (
		<Layout SideMenu={<SideMenu />} CodeAssist={CodeAssist}>
			<Routes>
				<Route path="/dashboard/*" element={<AppDashboardRoutes />} />
				<Route path="/user-roles//*" element={<AppUserRolesRoutes />} />
				<Route
					path="/user-management//*"
					element={<AppUserManagementRoutes />}
				/>
				<Route
					path="/app-settings/*"
					element={<Navigate to="./app-configuration/*" />}
				/>
				<Route
					path="/app-settings/app-configuration/*"
					element={<AppConfigurationRoutes />}
				/>
				<Route
					path="/app-settings/app-theme-configuration//*"
					element={<Navigate to="../app-configuration/#themes" />}
				/>
				{appCodeRoutes.map((route, index) => (
					<Route key={index} path={route.path.replace(`/app/:appId`, '')} element={route.element} />
				))}
				<Route
					path="/permission-management/permissions//*"
					element={<AppPermissionsManagementRoutes />}
				/>
				<Route
					path="/permission-management/policies//*"
					element={<AppPoliciesManagementRoutes />}
				/>
				<Route
					path="/tasks-management//*"
					element={<AppTaskManagementRoutes />}
				/>
				<Route
					path="/packages-management//*"
					element={<AppPackagesManagementRoutes />}
				/>
				<Route path="/logs/*" element={<AppLogsRoutes />} />
				<Route path="/Releases//*" element={<AppReleasesRoutes />} />
				<Route
					path="*"
					element={<Navigate to="./dashboard/*" />}
				/>
			</Routes>
		</Layout>
	);
};

export default PlatformAppRoutes;
