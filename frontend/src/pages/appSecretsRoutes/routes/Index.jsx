import { Navigate, Route, Routes } from 'react-router-dom';
import Secrets from '../components/Secrets/Index';

export const AppSecretsRoutes = () => {
	return (
		<Routes>
			<Route path="" element={<Secrets />} />
			<Route path="*" element={<Navigate to="." />} />
		</Routes>
	);
};
