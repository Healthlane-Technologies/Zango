import { Navigate, Route, Routes } from 'react-router-dom';
import AppConfiguration from '../components/AppConfiguration/index.js';

export const AppConfigurationRoutes = () => {
	return (
		<Routes>
			<Route path="" element={<AppConfiguration />} />
			<Route path="*" element={<Navigate to="." />} />
		</Routes>
	);
};
