import { useCallback, useEffect, useState } from 'react';
import useApi from '../../../../hooks/useApi';
import ConnectorCard from '../../../platformLogConnectors/components/ConnectorCard';
import ConnectorEditModal from '../../../platformLogConnectors/components/ConnectorEditModal';

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

export default function LogConnectorsTab() {
	const triggerApi = useApi();
	const [environment, setEnvironment] = useState('');
	const [rows, setRows] = useState([]);
	const [availableTypes, setAvailableTypes] = useState([]);
	const [editing, setEditing] = useState(null);
	const [loaded, setLoaded] = useState(false);

	const load = useCallback(async () => {
		const { response, success } = await triggerApi({
			url: '/api/v1/platform/logs/connectors/',
			type: 'GET',
			loader: false,
		});
		if (success && response) {
			setEnvironment(response.environment);
			setRows(response.rows || []);
			setAvailableTypes(response.available_types || []);
		}
		setLoaded(true);
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
		<div className="flex flex-col gap-[18px]">
			<header className="flex items-start gap-[14px] rounded-[12px] border border-[rgba(89,97,229,0.18)] bg-gradient-to-b from-[#EEF1FE] to-white p-[16px]">
				<div className="flex h-[40px] w-[40px] flex-shrink-0 items-center justify-center rounded-[8px] bg-[#5961E5] text-white shadow-sm">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="20"
						height="20"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						strokeWidth="2"
					>
						<path d="M12 2v4M12 18v4M2 12h4M18 12h4" />
						<circle cx="12" cy="12" r="6" />
					</svg>
				</div>
				<div className="flex-1">
					<h3 className="text-[13.5px] font-semibold text-[#0B0D14]">
						Connector-based architecture
					</h3>
					<p className="mt-[2px] text-[12px] text-[#2C3047]">
						One connector per component, configured once at platform level.
						Every app reads from the same source, filtered to its own lines.
					</p>
					{environment && (
						<div className="mt-[8px] inline-flex items-center gap-[6px] rounded-full bg-[#FEF6E7] px-[10px] py-[3px] text-[11px] font-medium text-[#8A5A07]">
							<span className="h-[6px] w-[6px] rounded-full bg-[#DA9011]" />
							Environment: {environment}
						</div>
					)}
				</div>
			</header>

			<div className="grid grid-cols-1 gap-[14px] md:grid-cols-3">
				{ALL_COMPONENTS.map((c, idx) => (
					<div
						key={c}
						className="card-fade"
						style={{ animationDelay: `${idx * 50}ms` }}
					>
						<ConnectorCard
							component={c}
							meta={COMPONENT_META[c]}
							row={rowFor(c)}
							onEdit={() => handleEdit(c)}
						/>
					</div>
				))}
			</div>

			{loaded && rows.length === 0 && (
				<div className="rounded-[10px] border border-dashed border-[#D4D8E5] bg-white p-[24px] text-center">
					<div className="text-[13px] font-semibold text-[#0B0D14]">
						No connectors yet
					</div>
					<div className="mt-[2px] text-[11.5px] text-[#5A607A]">
						Click "+ Configure" on any component card above to wire one up.
					</div>
				</div>
			)}

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

			<style>{`
				@keyframes card-fade {
					from { opacity: 0; transform: translateY(6px); }
					to   { opacity: 1; transform: translateY(0); }
				}
				.card-fade { animation: card-fade 280ms cubic-bezier(0.22, 1, 0.36, 1) both; }
				@media (prefers-reduced-motion: reduce) {
					.card-fade { animation: none; }
				}
			`}</style>
		</div>
	);
}
