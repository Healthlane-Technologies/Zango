import { Navigate, Route, Routes } from 'react-router-dom';
import Layout from '../../../components/Layout';
import PlatformLogConnectors from '../components/PlatformLogConnectors';

const PlatformLogConnectorsRoutes = () => {
	return (
		<Layout>
			<Routes>
				<Route path="" element={<PlatformLogConnectors />} />
				<Route path="*" element={<Navigate to="." />} />
			</Routes>
		</Layout>
	);
};

export default PlatformLogConnectorsRoutes;
