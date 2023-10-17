import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { PlatformAppRoutes } from '../pages/app/routes';
import { PlatformRoutes } from '../pages/platform/routes';
import { PlatformUserManagementRoutes } from '../pages/platformUserManagement/routes';
import toast, { Toaster } from 'react-hot-toast';
import { useEffect } from 'react';
import useApi from '../hooks/useApi';
import { setAppPanelInitialData } from '../pages/platform/slice';
import { useDispatch } from 'react-redux';

export const AppRoutes = () => {
	const location = useLocation();
	let pathnameArray = location.pathname.split('/').filter((each) => each);
	const dispatch = useDispatch();

	const triggerApi = useApi();

	useEffect(() => {
		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/appInitialData`,
				type: 'GET',
				loader: true,
			});

			if (success && response) {
				dispatch(setAppPanelInitialData(response?.app_data));
			}
		};

		makeApiCall();
	}, []);

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
