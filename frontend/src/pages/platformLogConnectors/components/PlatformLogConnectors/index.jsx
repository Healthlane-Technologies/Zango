import { useCallback, useEffect, useState } from 'react';
import useApi from '../../../../hooks/useApi';
import ConnectorCard from '../ConnectorCard';
import ConnectorEditModal from '../ConnectorEditModal';

const COMPONENT_META = {
	app: {
		label: 'App',
		sub: 'Django · gunicorn stdout',
		accent: 'indigo',
	},
	celery: {
		label: 'Celery worker',
		sub: 'Worker tasks · async',
		accent: 'teal',
	},
	celery_beat: {
		label: 'Celery beat',
		sub: 'Scheduler',
		accent: 'amber',
	},
};

const ALL_COMPONENTS = ['app', 'celery', 'celery_beat'];

export default function PlatformLogConnectors() {
	const triggerApi = useApi();
	const [environment, setEnvironment] = useState('');
	const [rows, setRows] = useState([]);
	const [availableTypes, setAvailableTypes] = useState([]);
	const [editing, setEditing] = useState(null); // { component, row | null }

	const load = useCallback(async () => {
		const { response, success } = await triggerApi({
			url: '/api/v1/platform/logs/connectors/',
			type: 'GET',
			loader: true,
		});
		if (success && response) {
			setEnvironment(response.environment);
			setRows(response.rows || []);
			setAvailableTypes(response.available_types || []);
		}
	}, [triggerApi]);

	useEffect(() => {
		load();
	}, [load]);

	const rowFor = (component) =>
		rows.find((r) => r.component === component) || null;

	const handleEdit = (component) => {
		setEditing({ component, row: rowFor(component) });
	};

	const handleClose = () => setEditing(null);

	const handleSaved = () => {
		setEditing(null);
		load();
	};

	return (
		<div className="flex grow flex-col gap-[20px] p-[24px]">
			<header>
				<h1 className="text-[20px] font-semibold tracking-[-0.02em] text-[#0B0D14]">
					Log connectors
				</h1>
				<p className="mt-[4px] text-[13px] text-[#5A607A]">
					One connector per component per environment. Configured once at platform
					level — every app reads from the same source, filtered to its own lines.
				</p>
				{environment && (
					<div className="mt-[8px] inline-flex items-center gap-[6px] rounded-full bg-[#FEF6E7] px-[10px] py-[3px] text-[11px] font-medium text-[#8A5A07]">
						<span className="h-[6px] w-[6px] rounded-full bg-[#DA9011]" />
						Environment: {environment}
					</div>
				)}
			</header>

			<div className="grid grid-cols-1 gap-[14px] md:grid-cols-3">
				{ALL_COMPONENTS.map((c) => (
					<ConnectorCard
						key={c}
						component={c}
						meta={COMPONENT_META[c]}
						row={rowFor(c)}
						onEdit={() => handleEdit(c)}
					/>
				))}
			</div>

			{editing && (
				<ConnectorEditModal
					environment={environment}
					component={editing.component}
					row={editing.row}
					availableTypes={availableTypes}
					onClose={handleClose}
					onSaved={handleSaved}
				/>
			)}
		</div>
	);
}
