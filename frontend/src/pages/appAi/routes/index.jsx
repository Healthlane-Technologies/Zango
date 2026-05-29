import { Navigate, Route, Routes } from 'react-router-dom';
import AppAi from '../components/AppAi';

export function AppAiRoutes() {
	return (
		<Routes>
			<Route path="/" element={<AppAi />} />
			<Route path="*" element={<Navigate to="/" />} />
		</Routes>
	);
}
