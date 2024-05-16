import { useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import { useDispatch } from 'react-redux';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import useApi from '../hooks/useApi';
import PlatformAppRoutes from '../pages/app/routes';
import PlatformRoutes from '../pages/platform/routes';
import { setAppPanelInitialData } from '../pages/platform/slice';
import PlatformUserManagementRoutes from '../pages/platformUserManagement/routes';

export const AppRoutes = () => {
	const location = useLocation();
	const dispatch = useDispatch();
	const triggerApi = useApi();
	let pathnameArray = location.pathname.split('/').filter((each) => each);

	useEffect(() => {
		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/auth/app-initalization-details/`,
				type: 'GET',
				loader: true,
			});

			if (success && response) {
				dispatch(setAppPanelInitialData(response?.app_data));
			}
		};

		makeApiCall();
	}, [triggerApi, dispatch]);

	// TODO: pages structure for app and platform pages
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
