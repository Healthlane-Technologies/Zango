import { Navigate, Route, Routes } from 'react-router-dom';

export const PlatformAppRoutes = () => {
	return (
		<Routes>
			<Route path="" element={<div>Platform App</div>} />
			<Route path=":appId" element={<div>Platform App Details</div>} />
			<Route path="*" element={<Navigate to="." />} />
		</Routes>
	);
};
