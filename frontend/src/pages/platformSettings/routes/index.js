import { Navigate, Route, Routes } from 'react-router-dom';
import Layout from '../../../components/Layout';
import PlatformSettings from '../components/PlatformSettings';

const PlatformSettingsRoutes = () => {
	return (
		<Layout>
			<Routes>
				<Route path="" element={<Navigate to="general" replace />} />
				<Route path=":tab" element={<PlatformSettings />} />
				<Route path="*" element={<Navigate to="general" replace />} />
			</Routes>
		</Layout>
	);
};

export default PlatformSettingsRoutes;
