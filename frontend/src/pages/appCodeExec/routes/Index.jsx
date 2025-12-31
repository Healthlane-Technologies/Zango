import CodeExec from '../components/CodeExec/Index';
import CodeExecForm from '../components/CodeExecForm/Index';

const appCodeExecRoutes = [
	{
		path: '/app/:appId/codeexec',
		element: <CodeExec />,
	},
	{
		path: '/app/:appId/codeexec/new',
		element: <CodeExecForm />,
	},
	{
		path: '/app/:appId/codeexec/edit',
		element: <CodeExecForm />,
	},
];

export default appCodeExecRoutes;
