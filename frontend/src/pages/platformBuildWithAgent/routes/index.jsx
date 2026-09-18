import { Navigate, Route, Routes } from 'react-router-dom';
import Layout from '../../../components/Layout';
import BuildWithAgent from '../components/BuildWithAgent';

/**
 * Mounted outside /platform/apps/ on purpose: `/platform/apps/:appId` is a
 * more specific route than `/platform/apps/*`, so a sibling path there would
 * be matched as an app id.
 */
const BuildWithAgentRoutes = () => {
	return (
		<Layout>
			<Routes>
				<Route path="" element={<BuildWithAgent />} />
				{/* The scaffold id in the URL is what makes a launch resumable. */}
				<Route path=":scaffoldId" element={<BuildWithAgent />} />
				<Route path="*" element={<Navigate to="." />} />
			</Routes>
		</Layout>
	);
};

export default BuildWithAgentRoutes;
