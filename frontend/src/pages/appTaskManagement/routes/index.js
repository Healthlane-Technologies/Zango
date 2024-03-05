import { Navigate, Route, Routes } from 'react-router-dom';
import AppTaskManagement from '../components/AppTaskManagement/index.js';

export const AppTaskManagementRoutes = () => {
	return (
		<Routes>
			<Route path="" element={<AppTaskManagement />} />
			<Route path="*" element={<Navigate to="." />} />
		</Routes>
	);
};
