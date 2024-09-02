import { Navigate, Route, Routes } from 'react-router-dom';
import Releases from '../components/Releases/Index';

export const AppReleasesRoutes = () => {
	return (
		<Routes>
			<Route path="" element={<Releases />} />
			<Route path="*" element={<Navigate to="." />} />
		</Routes>
	);
};
