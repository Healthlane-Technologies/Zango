import { Navigate, Route, Routes } from 'react-router-dom';
import AppAuditLogs from '../components/AppAuditLogs/index.js';

export const AppAuditLogsRoutes = () => {
	return (
		<Routes>
			<Route path="" element={<AppAuditLogs />} />
			<Route path="*" element={<Navigate to="." />} />
		</Routes>
	);
};
