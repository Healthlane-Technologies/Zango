import { Navigate, Route, Routes } from 'react-router-dom';
import AppPermissionsManagement from '../components/AppPermissionsManagement/index.js';

export const AppPermissionsManagementRoutes = () => {
	return (
		<Routes>
			<Route path="" element={<AppPermissionsManagement />} />
			<Route path="*" element={<Navigate to="." />} />
		</Routes>
	);
};
