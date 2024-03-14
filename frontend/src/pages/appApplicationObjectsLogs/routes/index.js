import { Navigate, Route, Routes } from 'react-router-dom';
import AppApplicationObjectsLogs from '../components/AppApplicationObjectsLogs/index.js';

export const AppApplicationObjectsLogsRoutes = () => {
	return (
		<Routes>
			<Route path="" element={<AppApplicationObjectsLogs />} />
			<Route path="*" element={<Navigate to="." />} />
		</Routes>
	);
};
