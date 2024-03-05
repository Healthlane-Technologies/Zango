import { Navigate, Route, Routes } from 'react-router-dom';
import AppThemeConfiguration from '../components/AppThemeConfiguration/index.js';

export const AppThemeConfigurationRoutes = () => {
	return (
		<Routes>
			<Route path="" element={<AppThemeConfiguration />} />
			<Route path="*" element={<Navigate to="." />} />
		</Routes>
	);
};
