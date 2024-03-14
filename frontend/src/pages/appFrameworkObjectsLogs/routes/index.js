import { Navigate, Route, Routes } from 'react-router-dom';
import AppFrameworkObjectsLogs from '../components/AppFrameworkObjectsLogs/index.js';

export const AppFrameworkObjectsLogsRoutes = () => {
	return (
		<Routes>
			<Route path="" element={<AppFrameworkObjectsLogs />} />
			<Route path="*" element={<Navigate to="." />} />
		</Routes>
	);
};
