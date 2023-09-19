import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { ReactComponent as AddUserIcon } from '../../../../assets/images/svg/add-user-icon.svg';
import useApi from '../../../../hooks/useApi';
import {
	openIsAddNewUserModalOpen,
	selectPlatformUserManagementData,
	selectRerenderPage,
	setPlatformUserManagementData,
} from '../../slice';
import ActivateUserModal from '../Models/ActivateUserModal';
import AddNewUserModal from '../Models/AddNewUserModal';
import DeactivateUserModal from '../Models/DeactivateUserModal';
import EditUserDetailsModal from '../Models/EditUserDetailsModal';
import ResetPasswordModal from '../Models/ResetPasswordModal';
import Table from '../Table';

export default function PlatformUserManagement() {
	const rerenderPage = useSelector(selectRerenderPage);

	const platformUserManagementData = useSelector(
		selectPlatformUserManagementData
	);
	const dispatch = useDispatch();

	const handleAddNewUser = () => {
		dispatch(openIsAddNewUserModalOpen());
	};

	function updatePlatformUserManagementData(value) {
		dispatch(setPlatformUserManagementData(value));
	}

	const triggerApi = useApi();

	useEffect(() => {
		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/auth/platform-users/?include_dropdown_options=true`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				updatePlatformUserManagementData(response);
			}
		};

		makeApiCall();
	}, [rerenderPage]);

	return (
		<>
			<div className="flex grow flex-col gap-[20px]">
				<div className="flex items-center justify-between py-[12px] pl-[40px] pr-[48px]">
					<h3 className="font-source-sans-pro text-[22px] font-semibold leading-[28px] tracking-[-0.2px] text-[#000]">
						Platform User Management
					</h3>
					<button
						type="button"
						onClick={handleAddNewUser}
						className="flex gap-[8px] rounded-[4px] bg-primary px-[16px] py-[7px]"
					>
						<span className="font-lato text-[14px] font-bold leading-[20px] text-[#FFFFFF]">
							New User
						</span>
						<AddUserIcon />
					</button>
				</div>
				<div className="flex grow flex-col overflow-x-auto">
					{platformUserManagementData ? (
						<Table tableData={platformUserManagementData?.platform_users} />
					) : null}
				</div>
			</div>
			<AddNewUserModal />
			<EditUserDetailsModal />
			<DeactivateUserModal />
			<ActivateUserModal />
			<ResetPasswordModal />
		</>
	);
}
