import { Navigate, Route, Routes } from 'react-router-dom';
import { AppConfigurationRoutes } from '../../appConfiguration/routes';
import { AppThemeConfigurationRoutes } from '../../appThemeConfiguration/routes';
import { AppUserManagementRoutes } from '../../appUserManagement/routes';
import Layout from '../components/Layout';

export const PlatformAppRoutes = () => {
	return (
		<Layout>
			<Routes>
				<Route path="/user-roles/" element={<div>User Roles</div>} />
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
					path="/permission-management/"
					element={<div>Permission Management</div>}
				/>
				<Route
					path="/tasks-management/"
					element={<div>Tasks Management</div>}
				/>
				<Route path="*" element={<Navigate to="./user-roles/" />} />
			</Routes>
		</Layout>
	);
};
