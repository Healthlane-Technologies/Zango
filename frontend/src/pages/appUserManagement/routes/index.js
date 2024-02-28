import { Navigate, Route, Routes } from 'react-router-dom';
import AppUserManagement from '../components/AppUserManagement/index.js';

export const AppUserManagementRoutes = () => {
	return (
		<Routes>
			<Route path="" element={<AppUserManagement />} />
			<Route path="*" element={<Navigate to="." />} />
		</Routes>
	);
};
