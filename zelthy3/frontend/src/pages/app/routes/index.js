import { Navigate, Route, Routes } from 'react-router-dom';
import { UserManagementRoutes } from '../../userManagement/routes';
import AppDetails from '../components/AppDetails';
import Layout from '../components/Layout';

export const PlatformAppRoutes = () => {
	return (
		<Layout>
			<Routes>
				<Route path="" element={<AppDetails />} />
				<Route path="/user-roles/" element={<AppDetails />} />
				<Route path="/user-management/" element={<UserManagementRoutes />} />
				<Route path="/app-settings/" element={<AppDetails />} />
				<Route path="/permission-management/" element={<AppDetails />} />
				<Route path="/tasks-management/" element={<AppDetails />} />
				<Route path="*" element={<Navigate to="." />} />
			</Routes>
		</Layout>
	);
};
