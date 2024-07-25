import { Navigate, Route, Routes } from 'react-router-dom';
import AppAccessLogs from '../components/AppAccessLogs/index.js';

export const AppAccessLogsRoutes = () => {
	return (
		<Routes>
			<Route path="" element={<AppAccessLogs />} />
			<Route path="*" element={<Navigate to="." />} />
		</Routes>
	);
};
