import { Navigate, Route, Routes } from 'react-router-dom';
import { PlatformAppRoutes } from '../pages/app/routes';
import { PlatformRoutes } from '../pages/platform/routes';
import { PlatformUserManagementRoutes } from '../pages/platformUserManagement/routes';

export const AppRoutes = () => {
	return (
		<Routes>
			<Route path="/platform/apps/*" element={<PlatformRoutes />}></Route>
			<Route
				path="/platform/user-managements/*"
				element={<PlatformUserManagementRoutes />}
			></Route>
			<Route path="/platform/apps/:appId/*" element={<PlatformAppRoutes />} />
			<Route path="*" element={<Navigate to="./platform/apps" />} />
		</Routes>
	);
};
