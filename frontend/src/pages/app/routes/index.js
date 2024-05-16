import { useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { Navigate, Route, Routes, useParams } from 'react-router-dom';
import useApi from '../../../hooks/useApi';
import { AppApplicationObjectsLogsRoutes } from '../../appApplicationObjectsLogs/routes';
import { AppConfigurationRoutes } from '../../appConfiguration/routes';
import { setAppConfigurationData } from '../../appConfiguration/slice';
import { AppFrameworkObjectsLogsRoutes } from '../../appFrameworkObjectsLogs/routes';
import { AppPackagesManagementRoutes } from '../../appPackagesManagement/routes';
import { AppPermissionsManagementRoutes } from '../../appPermissionsManagement/routes';
import { AppPoliciesManagementRoutes } from '../../appPoliciesManagement/routes';
import { AppTaskManagementRoutes } from '../../appTaskManagement/routes';
import { AppThemeConfigurationRoutes } from '../../appThemeConfiguration/routes';
import { AppUserManagementRoutes } from '../../appUserManagement/routes';
import { AppUserRolesRoutes } from '../../appUserRoles/routes';
import Layout from '../components/Layout';

export const PlatformAppRoutes = () => {
	let { appId } = useParams();

	const dispatch = useDispatch();

	function updateAppConfigurationData(value) {
		dispatch(setAppConfigurationData(value));
	}

	const triggerApi = useApi();

	useEffect(() => {
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

		makeApiCall();
	}, []);

	return (
		<Layout>
			<Routes>
				<Route path="/user-roles//*" element={<AppUserRolesRoutes />} />
				<Route
					path="/user-management//*"
					element={<AppUserManagementRoutes />}
				/>
				<Route path="/app-settings//*" element={<div>App Settings</div>} />
				<Route
					path="/app-settings/app-configuration//*"
					element={<AppConfigurationRoutes />}
				/>
				<Route
					path="/app-settings/app-theme-configuration//*"
					element={<AppThemeConfigurationRoutes />}
				/>
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
				<Route
					path="/audit-logs/application-objects-logs//*"
					element={<AppApplicationObjectsLogsRoutes />}
				/>
				<Route
					path="/audit-logs/framework-objects-logs//*"
					element={<AppFrameworkObjectsLogsRoutes />}
				/>
				<Route
					path="*"
					element={<Navigate to="./app-settings/app-configuration//*" />}
				/>
			</Routes>
		</Layout>
	);
};
