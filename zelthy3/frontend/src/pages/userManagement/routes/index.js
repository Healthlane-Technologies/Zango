import { Navigate, Route, Routes } from 'react-router-dom';
import UserManagement from '../components/UserManagement.jsx/index.js';

export const UserManagementRoutes = () => {
	return (
		<Routes>
			<Route path="" element={<UserManagement />} />
			<Route path="*" element={<Navigate to="." />} />
		</Routes>
	);
};
