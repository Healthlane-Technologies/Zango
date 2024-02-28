import { Navigate, Route, Routes } from 'react-router-dom';
import Layout from '../components/Layout';
import PlatformUserManagement from '../components/PlatformUserManagement';

export const PlatformUserManagementRoutes = () => {
	return (
		<Layout>
			<Routes>
				<Route path="" element={<PlatformUserManagement />} />
				<Route path="*" element={<Navigate to="." />} />
			</Routes>
		</Layout>
	);
};
