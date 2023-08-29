import { useSelector, useDispatch } from 'react-redux';
import { openIsAddCustomPermissionModalOpen } from '../../slice';
import BreadCrumbs from '../BreadCrumbs';
import Table from '../Table';
import EditCustomPermissionModal from '../Models/EditCustomPermissionModal';
import DeleteCustomPermissionModal from '../Models/DeleteCustomPermissionModal';
import AddCustomPermissionModal from '../Models/AddCustomPermissionModal';
import { ReactComponent as AddUserIcon } from '../../../../assets/images/svg/add-user-icon.svg';

export default function AppPermissionsManagement() {
	const dispatch = useDispatch();

	const handleAddNewUser = () => {
		dispatch(openIsAddCustomPermissionModalOpen());
	};
	return (
		<>
			<div className="flex grow flex-col gap-[20px]">
				<div className="flex items-center justify-between py-[24px] pl-[40px] pr-[48px]">
					<BreadCrumbs />
					<button
						type="button"
						onClick={handleAddNewUser}
						className="flex gap-[8px] rounded-[4px] bg-primary px-[16px] py-[7px]"
					>
						<span className="font-lato text-[14px] font-bold leading-[20px] text-[#FFFFFF]">
							Custom Permission
						</span>
						<AddUserIcon />
					</button>
				</div>
				<div className="flex grow flex-col overflow-x-auto">
					<Table
						tableData={[
							{
								permission_name: 'Permission Name 1',
								permission_id: 5045,
								permission_type: 'DataModel',
								permission_description: 'Permission Description 1',
							},
							{
								permission_name: 'Permission Name 1',
								permission_id: 5045,
								permission_type: 'DataModel',
								permission_description: 'Permission Description 1',
							},
							{
								permission_name: 'Permission Name 1',
								permission_id: 5045,
								permission_type: 'DataModel',
								permission_description: 'Permission Description 1',
							},
							{
								permission_name: 'Permission Name 1',
								permission_id: 5045,
								permission_type: 'DataModel',
								permission_description: 'Permission Description 1',
							},
							{
								permission_name: 'Permission Name 1',
								permission_id: 5045,
								permission_type: 'DataModel',
								permission_description: 'Permission Description 1',
							},
							{
								permission_name: 'Permission Name 1',
								permission_id: 5045,
								permission_type: 'DataModel',
								permission_description: 'Permission Description 1',
							},
							{
								permission_name: 'Permission Name 1',
								permission_id: 5045,
								permission_type: 'DataModel',
								permission_description: 'Permission Description 1',
							},
							{
								permission_name: 'Permission Name 1',
								permission_id: 5045,
								permission_type: 'DataModel',
								permission_description: 'Permission Description 1',
							},
						]}
					/>
				</div>
			</div>
			<AddCustomPermissionModal />
			<EditCustomPermissionModal />
			<DeleteCustomPermissionModal />
		</>
	);
}
