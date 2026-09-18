import { Route, Routes } from 'react-router-dom';
import Layout from '../../../components/Layout';
import AgentMode from '../components/AgentMode';

/**
 * Mounted outside the app panel's shell on purpose.
 *
 * Every other app screen sits behind the left menu because you are
 * administering an app that already exists. Here you are talking to an agent
 * and watching something get built — a nav rail of settings pages is not what
 * you need, and the conversation and the app itself want every pixel.
 */
export function AgentModeRoutes() {
	// AgentMode owns its own nested routing (list / requirement / run).
	return (
		<Layout>
			<Routes>
				<Route path="/*" element={<AgentMode />} />
			</Routes>
		</Layout>
	);
}
