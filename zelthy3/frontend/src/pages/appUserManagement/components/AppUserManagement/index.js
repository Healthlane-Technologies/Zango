import BreadCrumbs from '../BreadCrumbs';
import { useSelector, useDispatch } from 'react-redux';
import {
	openIsAddNewUserModalOpen,
	selectAppUserManagementData,
	selectRerenderPage,
	setAppUserManagementData,
} from '../../slice';
import AddNewUserModal from '../Models/AddNewUserModal';
import { ReactComponent as AddUserIcon } from '../../../../assets/images/svg/add-user-icon.svg';
import Table from '../Table';
import EditUserDetailsModal from '../Models/EditUserDetailsModal';
import DeactivateUserModal from '../Models/DeactivateUserModal';
import { useEffect } from 'react';
import useApi from '../../../../hooks/useApi';
import { useParams } from 'react-router-dom';

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
				url: `/api/v1/apps/${appId}/users/`,
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
		</>
	);
}
