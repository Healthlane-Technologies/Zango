import { Navigate, Route, Routes } from 'react-router-dom';
import { PlatformAppRoutes } from '../pages/app/routes';
import { PlatformRoutes } from '../pages/platform/routes';

export const AppRoutes = () => {
	return (
		<Routes>
			<Route path="/platform/*" element={<PlatformRoutes />}></Route>
			<Route path="/platform/apps/:appId/*" element={<PlatformAppRoutes />} />
			<Route path="*" element={<Navigate to="./platform" />} />
		</Routes>
	);
};
