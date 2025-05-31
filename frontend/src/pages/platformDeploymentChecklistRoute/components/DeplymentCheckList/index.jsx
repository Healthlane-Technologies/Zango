
import ChecklistTable from './ChecklistTable';

export default function DeploymentChecklist() {

	return (
		<>
			<div className="flex grow flex-col gap-[40px]">
				<div className="flex grow flex-col gap-[20px] p-[24px]">
					<div className="flex items-end gap-[24px]">
						<h3
							data-cy="app_name_details_view"
							className="font-source-sans-pro text-[22px] font-semibold leading-[28px] text-[#000000]"
						>
							Deplyment Checklist
						</h3>
					</div>
					<ChecklistTable />
				</div>
			</div>
		</>
	);
}
