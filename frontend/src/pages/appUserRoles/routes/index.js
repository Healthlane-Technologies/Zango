import { Navigate, Route, Routes } from 'react-router-dom';
import AppUserRoles from '../components/AppUserRoles/index.js';

export const AppUserRolesRoutes = () => {
	return (
		<Routes>
			<Route path="" element={<AppUserRoles />} />
			<Route path="*" element={<Navigate to="." />} />
		</Routes>
	);
};
