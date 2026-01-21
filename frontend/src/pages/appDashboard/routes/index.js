import { Navigate, Route, Routes } from 'react-router-dom';
import AppDashboard from '../components/AppDashboard';

const AppDashboardRoutes = () => {
	return (
		<Routes>
			<Route path="" element={<AppDashboard />} />
			<Route path="*" element={<Navigate to="." />} />
		</Routes>
	);
};

export default AppDashboardRoutes;