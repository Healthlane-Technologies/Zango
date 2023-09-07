import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { PlatformAppRoutes } from '../pages/app/routes';
import { PlatformRoutes } from '../pages/platform/routes';
import { PlatformUserManagementRoutes } from '../pages/platformUserManagement/routes';
import toast, { Toaster } from 'react-hot-toast';

export const AppRoutes = () => {
	const location = useLocation();
	let pathnameArray = location.pathname.split('/').filter((each) => each);

	return (
		<>
			<Routes>
				<Route path="/platform/apps/*" element={<PlatformRoutes />}></Route>
				<Route
					path="/platform/user-managements/*"
					element={<PlatformUserManagementRoutes />}
				></Route>
				<Route path="/platform/apps/:appId/*" element={<PlatformAppRoutes />} />
				<Route path="*" element={<Navigate to="./platform/apps" />} />
			</Routes>
			<Toaster
				containerStyle={{
					left:
						pathnameArray.indexOf('apps') > -1 && pathnameArray.length > 2
							? '102px'
							: '16px',
				}}
			/>
		</>
	);
};
