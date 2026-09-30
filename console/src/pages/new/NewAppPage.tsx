import { useQueryClient } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { scaffoldKeys } from '@/api/scaffolds';
import { LaunchProgress } from './LaunchProgress';
import { NewAppForm } from './NewAppForm';

/**
 * New app: describe it, then follow the launch until the app's Agent tab takes over.
 * The scaffold id lives in `?scaffold=`, so a reload mid-launch rejoins the same launch
 * instead of starting a second app.
 */
export function NewAppPage() {
	const [params, setParams] = useSearchParams();
	const qc = useQueryClient();
	const scaffoldId = params.get('scaffold');

	if (scaffoldId) {
		return (
			<LaunchProgress
				key={scaffoldId}
				uuid={scaffoldId}
				onStartOver={() => setParams({}, { replace: true })}
			/>
		);
	}
	return (
		<NewAppForm
			onStarted={(s) => {
				qc.setQueryData(scaffoldKeys.detail(s.uuid), s);
				setParams({ scaffold: s.uuid }, { replace: true });
			}}
		/>
	);
}
