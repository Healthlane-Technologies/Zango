import { Navigate, Route, Routes } from 'react-router-dom';
import Layout from '../components/Layout';
import Platform from '../components/Platform';

export const PlatformRoutes = () => {
	return (
		<Layout>
			<Routes>
				<Route path="" element={<Platform />} />
				<Route path="*" element={<Navigate to="." />} />
			</Routes>
		</Layout>
	);
};
