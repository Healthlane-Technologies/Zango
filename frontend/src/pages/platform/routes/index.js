import { Navigate, Route, Routes } from 'react-router-dom';
import Layout from '../../../components/Layout';
import Platform from '../components/Platform';

const PlatformRoutes = () => {
	return (
		<Layout showFooter={true}>
			<Routes>
				<Route path="" element={<Platform />} />
				<Route path="*" element={<Navigate to="." />} />
			</Routes>
		</Layout>
	);
};
export default PlatformRoutes;
