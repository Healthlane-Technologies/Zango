import { Navigate, Route, Routes } from 'react-router-dom';
import AppConfiguration from '../components/AppConfiguration';
import AuthConfigurationPage from '../components/AuthConfigurationPage';
import AuthConfigurationForm from '../components/AuthConfigurationForm';

export const AppConfigurationRoutes = () => {
	return (
		<Routes>
			<Route path="" element={<AppConfiguration />} />
			<Route path="auth" element={<AuthConfigurationPage />} />
			<Route path="auth/configure" element={<AuthConfigurationForm />} />
			<Route path="*" element={<Navigate to="." />} />
		</Routes>
	);
};
