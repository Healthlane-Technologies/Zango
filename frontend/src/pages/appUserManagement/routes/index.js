import { Navigate, Route, Routes } from 'react-router-dom';
import AppUserManagement from '../components/AppUserManagement/index.js';

const AppUserManagementRoutes = () => {
	return (
		<Routes>
			<Route path="" element={<AppUserManagement />} />
			<Route path="*" element={<Navigate to="." />} />
		</Routes>
	);
};

export default AppUserManagementRoutes;
