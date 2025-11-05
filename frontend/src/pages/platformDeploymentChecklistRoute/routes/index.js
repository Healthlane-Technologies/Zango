import { Navigate, Route, Routes } from 'react-router-dom';
import DeplymentCheckList from '../components/DeplymentCheckList';
import Layout from '../../../components/Layout';

const DeplymentCheckListRoutes = () => {
	return (
		<Layout>
			<Routes>
				<Route path="" element={<DeplymentCheckList />} />
				<Route path="*" element={<Navigate to="." />} />
			</Routes>
		</Layout>
	);
};

export default DeplymentCheckListRoutes;