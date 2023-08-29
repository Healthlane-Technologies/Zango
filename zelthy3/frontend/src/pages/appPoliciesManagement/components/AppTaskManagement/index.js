import BreadCrumbs from '../BreadCrumbs';
import Table from '../Table';
import UpdatePolicyModal from '../Models/EditPolicyModal';
import RemoveAllPoliciesModal from '../Models/DeletePolicyModal';

export default function AppTaskManagement() {
	return (
		<>
			<div className="flex grow flex-col gap-[20px]">
				<div className="flex items-center justify-between py-[24px] pl-[40px] pr-[48px]">
					<BreadCrumbs />
				</div>
				<div className="flex grow flex-col overflow-x-auto">
					<Table
						tableData={[
							{
								task_name: 'Task 1',
								task_id: 5045,
								policy: ['Policy 1', 'Policy 2'],
							},
							{
								task_name: 'Task 1',
								task_id: 5045,
								policy: ['Policy 1', 'Policy 2'],
							},
							{
								task_name: 'Task 1',
								task_id: 5045,
								policy: ['Policy 1', 'Policy 2'],
							},
							{
								task_name: 'Task 1',
								task_id: 5045,
								policy: ['Policy 1', 'Policy 2'],
							},
							{
								task_name: 'Task 1',
								task_id: 5045,
								policy: ['Policy 1', 'Policy 2'],
							},
						]}
					/>
				</div>
			</div>
			<UpdatePolicyModal />
			<RemoveAllPoliciesModal />
		</>
	);
}
