import { useSelector, useDispatch } from 'react-redux';
import { openIsAddPolicyModalOpen } from '../../slice';
import BreadCrumbs from '../BreadCrumbs';
import Table from '../Table';
import EditPolicyModal from '../Models/EditPolicyModal';
import DeletePolicyModal from '../Models/DeletePolicyModal';
import AddPolicyModal from '../Models/AddPolicyModal';
import { ReactComponent as AddUserIcon } from '../../../../assets/images/svg/add-user-icon.svg';
import ViewPolicyModal from '../Models/ViewPolicyModal';

export default function AppPoliciesManagement() {
	const dispatch = useDispatch();

	const handleAddPolicy = () => {
		dispatch(openIsAddPolicyModalOpen());
	};
	return (
		<>
			<div className="flex grow flex-col gap-[20px]">
				<div className="flex items-center justify-between py-[24px] pl-[40px] pr-[48px]">
					<BreadCrumbs />
					<button
						type="button"
						onClick={handleAddPolicy}
						className="flex gap-[8px] rounded-[4px] bg-primary px-[16px] py-[7px]"
					>
						<span className="font-lato text-[14px] font-bold leading-[20px] text-[#FFFFFF]">
							Add Policy
						</span>
						<AddUserIcon />
					</button>
				</div>
				<div className="flex grow flex-col overflow-x-auto">
					<Table
						tableData={[
							{
								policy_name: 'Policy Name 1',
								policy_id: 5045,
								configuration: 'DataModel',
								policy_description: 'Policy Description 1',
							},
							{
								policy_name: 'Policy Name 1',
								policy_id: 5045,
								configuration: 'DataModel',
								policy_description: 'Policy Description 1',
							},
							{
								policy_name: 'Policy Name 1',
								policy_id: 5045,
								configuration: 'DataModel',
								policy_description: 'Policy Description 1',
							},
							{
								policy_name: 'Policy Name 1',
								policy_id: 5045,
								configuration: 'DataModel',
								policy_description: 'Policy Description 1',
							},
							{
								policy_name: 'Policy Name 1',
								policy_id: 5045,
								configuration: 'DataModel',
								policy_description: 'Policy Description 1',
							},
							{
								policy_name: 'Policy Name 1',
								policy_id: 5045,
								configuration: 'DataModel',
								policy_description: 'Policy Description 1',
							},
							{
								policy_name: 'Policy Name 1',
								policy_id: 5045,
								configuration: 'DataModel',
								policy_description: 'Policy Description 1',
							},
							{
								policy_name: 'Policy Name 1',
								policy_id: 5045,
								configuration: 'DataModel',
								policy_description: 'Policy Description 1',
							},
						]}
					/>
				</div>
			</div>
			<AddPolicyModal />
			<EditPolicyModal />
			<DeletePolicyModal />
			<ViewPolicyModal />
		</>
	);
}
