import { Navigate, Route, Routes } from 'react-router-dom';
import { AppConfigurationRoutes } from '../../appConfiguration/routes';
import { AppThemeConfigurationRoutes } from '../../appThemeConfiguration/routes';
import { AppUserManagementRoutes } from '../../appUserManagement/routes';
import { AppUserRolesRoutes } from '../../appUserRoles/routes';
import AppTaskManagement from '../../appTaskManagement/components/AppTaskManagement';
import Layout from '../components/Layout';
import { AppPermissionsManagementRoutes } from '../../appPermissionsManagement/routes';
import { AppPoliciesManagementRoutes } from '../../appPoliciesManagement/routes';

export const PlatformAppRoutes = () => {
	return (
		<Layout>
			<Routes>
				<Route path="/user-roles/" element={<AppUserRolesRoutes />} />
				<Route path="/user-management/" element={<AppUserManagementRoutes />} />
				<Route path="/app-settings/" element={<div>App Settings</div>} />
				<Route
					path="/app-settings/app-configuration/"
					element={<AppConfigurationRoutes />}
				/>
				<Route
					path="/app-settings/app-theme-configuration"
					element={<AppThemeConfigurationRoutes />}
				/>
				<Route
					path="/permission-management/permissions"
					element={<AppPermissionsManagementRoutes />}
				/>
				<Route
					path="/permission-management/policies"
					element={<AppPoliciesManagementRoutes />}
				/>
				<Route path="/tasks-management/" element={<AppTaskManagement />} />
				<Route path="*" element={<Navigate to="./user-roles/" />} />
			</Routes>
		</Layout>
	);
};
