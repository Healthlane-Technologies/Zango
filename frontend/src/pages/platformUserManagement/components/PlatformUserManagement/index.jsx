import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { ReactComponent as AddUserIcon } from '../../../../assets/images/svg/add-user-icon.svg';
import useApi from '../../../../hooks/useApi';
import {
	openIsAddNewUserModalOpen,
	selectPlatformUserManagementData,
	selectPlatformUserManagementTableData,
	selectRerenderPage,
	setPlatformUserManagementData,
} from '../../slice';
import ActivateUserModal from '../Modals/ActivateUserModal';
import AddNewUserModal from '../Modals/AddNewUserModal';
import DeactivateUserModal from '../Modals/DeactivateUserModal';
import EditUserDetailsModal from '../Modals/EditUserDetailsModal';
import ResetPasswordModal from '../Modals/ResetPasswordModal';
import AppTable from '../AppTable';

export default function PlatformUserManagement() {
	const rerenderPage = useSelector(selectRerenderPage);

	const platformUserManagementData = useSelector(
		selectPlatformUserManagementData
	);
	const platformUserManagementTableData = useSelector(
		selectPlatformUserManagementTableData
	);

	const dispatch = useDispatch();

	const handleAddNewUser = () => {
		dispatch(openIsAddNewUserModalOpen());
	};

	function updatePlatformUserManagementData(value) {
		dispatch(setPlatformUserManagementData(value));
	}

	const triggerApi = useApi();

	const makeApiCall = async (columnFilter) => {
		const { response, success } = await triggerApi({
			url: `/api/v1/auth/platform-users/?page=${
				platformUserManagementTableData?.pageIndex + 1
			}&page_size=${
				platformUserManagementTableData?.pageSize
			}&include_dropdown_options=true&search=${
				platformUserManagementTableData?.searchValue
			}${columnFilter?.length ? columnFilter : ''}`,
			type: 'GET',
			loader: true,
		});
		if (success && response) {
			updatePlatformUserManagementData(response);
		}
	};

	useEffect(() => {
		let columnFilter = platformUserManagementTableData?.columns
			? platformUserManagementTableData?.columns
					?.filter(({ id, value }) => value)
					?.map(({ id, value }) => {
						if (
							typeof value === 'object' &&
							!Array.isArray(value) &&
							isNaN(parseInt(value))
						) {
							return `&search_${id}=${JSON.stringify(value)}`;
						} else {
							return `&search_${id}=${value}`;
						}
					})
					.join('')
			: '';

		makeApiCall(columnFilter);
	}, [rerenderPage, platformUserManagementTableData]);

	if (!platformUserManagementData) {
		return null;
	}

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
						<AppTable tableData={platformUserManagementData?.platform_users} />
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
