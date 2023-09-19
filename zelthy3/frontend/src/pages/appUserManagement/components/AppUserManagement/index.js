import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import { ReactComponent as AddUserIcon } from '../../../../assets/images/svg/add-user-icon.svg';
import useApi from '../../../../hooks/useApi';
import {
	openIsAddNewUserModalOpen,
	selectAppUserManagementData,
	selectRerenderPage,
	setAppUserManagementData,
} from '../../slice';
import BreadCrumbs from '../BreadCrumbs';
import ActivateUserModal from '../Models/ActivateUserModal';
import AddNewUserModal from '../Models/AddNewUserModal';
import DeactivateUserModal from '../Models/DeactivateUserModal';
import EditUserDetailsModal from '../Models/EditUserDetailsModal';
import ResetPasswordModal from '../Models/ResetPasswordModal';
import Table from '../Table';

export default function UserManagement() {
	let { appId } = useParams();
	const rerenderPage = useSelector(selectRerenderPage);
	const appUserManagementData = useSelector(selectAppUserManagementData);

	const dispatch = useDispatch();

	const handleAddNewUser = () => {
		dispatch(openIsAddNewUserModalOpen());
	};

	function updateAppUserManagementData(value) {
		dispatch(setAppUserManagementData(value));
	}

	const triggerApi = useApi();

	useEffect(() => {
		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/users/?include_dropdown_options=true`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				updateAppUserManagementData(response);
			}
		};

		makeApiCall();
	}, [rerenderPage]);

	return (
		<>
			<div className="flex grow flex-col gap-[20px]">
				<div className="flex items-center justify-between py-[12px] pl-[40px] pr-[48px]">
					<BreadCrumbs />
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
					{appUserManagementData ? (
						<Table tableData={appUserManagementData?.users} />
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
