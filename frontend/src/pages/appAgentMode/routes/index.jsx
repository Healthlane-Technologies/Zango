import { Route, Routes } from 'react-router-dom';
import AgentMode from '../components/AgentMode';

export function AgentModeRoutes() {
	// AgentMode owns its own nested routing (list / requirement / run).
	return (
		<Routes>
			<Route path="/*" element={<AgentMode />} />
		</Routes>
	);
}
