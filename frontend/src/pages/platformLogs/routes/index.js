import { Navigate, Route, Routes } from 'react-router-dom';
import Layout from '../../../components/Layout';
import PlatformLogs from '../components/PlatformLogs';

const PlatformLogsRoutes = () => {
	return (
		<Layout>
			<Routes>
				<Route path="" element={<PlatformLogs />} />
				<Route path="*" element={<Navigate to="." />} />
			</Routes>
		</Layout>
	);
};

export default PlatformLogsRoutes;
