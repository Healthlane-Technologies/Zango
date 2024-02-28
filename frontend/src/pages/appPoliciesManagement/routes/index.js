import { Navigate, Route, Routes } from 'react-router-dom';
import AppPoliciesManagement from '../components/AppPoliciesManagement/index.js';

export const AppPoliciesManagementRoutes = () => {
	return (
		<Routes>
			<Route path="" element={<AppPoliciesManagement />} />
			<Route path="*" element={<Navigate to="." />} />
		</Routes>
	);
};
