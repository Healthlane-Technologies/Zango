import { Navigate, Route, Routes } from 'react-router-dom';
import UnifiedAppSettings from '../components/UnifiedAppSettings';
import AuthConfigurationForm from '../components/AuthConfigurationForm';

export const AppConfigurationRoutes = () => {
	return (
		<Routes>
			<Route path="" element={<UnifiedAppSettings />} />
			<Route path="auth/configure" element={<AuthConfigurationForm />} />
			<Route path="*" element={<Navigate to="." />} />
		</Routes>
	);
};
