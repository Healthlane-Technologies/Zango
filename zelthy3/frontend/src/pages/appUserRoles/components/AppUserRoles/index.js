import BreadCrumbs from '../BreadCrumbs';
import { useSelector, useDispatch } from 'react-redux';
import { openIsAddNewUserRolesModalOpen } from '../../slice';
import AddNewUserRolesModal from '../Models/AddNewUserRolesModal';
import { ReactComponent as AddUserIcon } from '../../../../assets/images/svg/add-user-icon.svg';
import Table from '../Table';
import EditUserRolesDetailsModal from '../Models/EditUserDetailsRolesModal';
import DeactivateUserRolesModal from '../Models/DeactivateUserRolesModal';
import { useState } from 'react';

export default function AppUserRoles() {
	const [isEmpty, setisEmpty] = useState(false);
	const dispatch = useDispatch();

	const handleAddNewUser = () => {
		dispatch(openIsAddNewUserRolesModalOpen());
	};
	return (
		<>
			<div className="flex grow flex-col gap-[20px]">
				<div className="flex items-center justify-between py-[12px] pl-[40px] pr-[48px]">
					<BreadCrumbs />
					{isEmpty ? null : (
						<button
							type="button"
							onClick={handleAddNewUser}
							className="flex gap-[8px] rounded-[4px] bg-primary px-[16px] py-[7px]"
						>
							<span className="font-lato text-[14px] font-bold leading-[20px] text-[#FFFFFF]">
								New User Role
							</span>
							<AddUserIcon />
						</button>
					)}
				</div>
				<div className="flex grow flex-col overflow-x-auto">
					{isEmpty ? (
						<div className="flex grow flex-col items-center justify-center gap-[56px]">
							<div className="flex flex-col items-center justify-center gap-[8px]">
								<h3 className="first-app-text font-source-sans-pro text-[64px] font-[700] leading-[72px]">
									set-up user role(s)
								</h3>
								<p className="font-source-sans-pro text-[18px] font-semibold leading-[24px] text-[#212429]">
									description to be added
								</p>
							</div>
							<button
								type="button"
								onClick={handleAddNewUser}
								className="flex gap-[8px] rounded-[4px] bg-primary px-[16px] py-[7px]"
							>
								<span className="font-lato text-[14px] font-bold leading-[20px] text-[#FFFFFF]">
									Create New User Role
								</span>
								<AddUserIcon />
							</button>
						</div>
					) : (
						<Table
							tableData={[
								{
									roles_access: 'Role 1',
									policy: ['Policy 1', 'Policy 2'],
									status: 'active',
									number_of_users: 82,
								},
								{
									roles_access: 'Role 1',
									policy: ['Policy 2', 'Policy 4'],
									status: 'active',
									number_of_users: 12,
								},
								{
									roles_access: 'Role 1',
									policy: ['Policy 3', 'Policy 4', 'Policy 5', 'Policy 1'],
									status: 'inactive',
									number_of_users: 4,
								},
								{
									roles_access: 'Role 1',
									policy: ['Policy 1', 'Policy 2'],
									status: 'active',
									number_of_users: 112,
								},
							]}
						/>
					)}
				</div>
			</div>
			<AddNewUserRolesModal />
			<EditUserRolesDetailsModal />
			<DeactivateUserRolesModal />
		</>
	);
}
