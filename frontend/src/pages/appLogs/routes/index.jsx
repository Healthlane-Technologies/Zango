import { Navigate, Route, Routes } from 'react-router-dom';
import AppLogs from '../components/AppLogs';

export function AppLogsRoutes() {
	return (
		<Routes>
			<Route path="/" element={<AppLogs />} />
			<Route path="*" element={<Navigate to="/" />} />
		</Routes>
	);
}