import BreadCrumbs from '../BreadCrumbs';
import { useSelector, useDispatch } from 'react-redux';
import {
	openIsAddNewUserModalOpen,
	selectPlatformUserManagementData,
	setPlatformUserManagementData,
} from '../../slice';
import AddNewUserModal from '../Models/AddNewUserModal';
import { ReactComponent as AddUserIcon } from '../../../../assets/images/svg/add-user-icon.svg';
import Table from '../Table';
import EditUserDetailsModal from '../Models/EditUserDetailsModal';
import DeactivateUserModal from '../Models/DeactivateUserModal';
import { useEffect } from 'react';
import useApi from '../../../../hooks/useApi';

export default function PlatformUserManagement() {
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
				url: `/api/v1/auth/platform-users/`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				updatePlatformUserManagementData(response);
			}
		};

		makeApiCall();
	}, []);

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
		</>
	);
}
