import { Navigate, Route, Routes } from 'react-router-dom';
import AppPackagesManagement from '../components/AppPackagesManagement/index.js';

export const AppPackagesManagementRoutes = () => {
	return (
		<Routes>
			<Route path="" element={<AppPackagesManagement />} />
			<Route path="*" element={<Navigate to="." />} />
		</Routes>
	);
};
