import { Navigate, Route, Routes } from 'react-router-dom';
import AppDownloads from '../components/AppDownloads';

export const AppDownloadsRoutes = () => {
	return (
		<Routes>
			<Route path="" element={<AppDownloads />} />
			<Route path="*" element={<Navigate to="." />} />
		</Routes>
	);
};
