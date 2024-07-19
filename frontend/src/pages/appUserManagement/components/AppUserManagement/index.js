import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import { ReactComponent as AddUserIcon } from '../../../../assets/images/svg/add-user-icon.svg';
import useApi from '../../../../hooks/useApi';
import BreadCrumbs from '../../../app/components/BreadCrumbs';
import {
	openIsAddNewUserModalOpen,
	selectAppUserManagementData,
	selectAppUserManagementTableData,
	selectIsAppUserManagementDataEmpty,
	selectRerenderPage,
	setAppUserManagementData,
} from '../../slice';
import AppTable from '../AppTable';
import ActivateUserModal from '../Modals/ActivateUserModal';
import AddNewUserModal from '../Modals/AddNewUserModal';
import DeactivateUserModal from '../Modals/DeactivateUserModal';
import EditUserDetailsModal from '../Modals/EditUserDetailsModal';
import ResetPasswordModal from '../Modals/ResetPasswordModal';

export default function UserManagement() {
	let { appId } = useParams();
	const rerenderPage = useSelector(selectRerenderPage);
	const appUserManagementData = useSelector(selectAppUserManagementData);
	const appUserManagementTableData = useSelector(
		selectAppUserManagementTableData
	);
	const isAppUserManagementDataEmpty = useSelector(
		selectIsAppUserManagementDataEmpty
	);

	const dispatch = useDispatch();

	const handleAddNewUser = () => {
		dispatch(openIsAddNewUserModalOpen());
	};

	function updateAppUserManagementData(value) {
		dispatch(setAppUserManagementData(value));
	}

	const triggerApi = useApi();

	useEffect(() => {
		let columnFilter = appUserManagementTableData?.columns
			? appUserManagementTableData?.columns
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

		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/users/?page=${
					appUserManagementTableData?.pageIndex + 1
				}&page_size=${
					appUserManagementTableData?.pageSize
				}&include_dropdown_options=true&search=${
					appUserManagementTableData?.searchValue
				}${columnFilter?.length ? columnFilter : ''}`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				updateAppUserManagementData(response);
			}
		};

		makeApiCall();
	}, [rerenderPage, appUserManagementTableData]);

	if (!appUserManagementData) {
		return null;
	}

	return (
		<>
			<div data-cy="add_user" className="flex grow flex-col gap-[20px]">
				<div className="flex items-center justify-between py-[12px] pl-[40px] pr-[48px]">
					<BreadCrumbs />
					{isAppUserManagementDataEmpty ? null : (
						<button
							data-cy="new_user_button"
							type="button"
							onClick={handleAddNewUser}
							className="flex gap-[8px] rounded-[4px] bg-primary px-[16px] py-[7px]"
						>
							<span className="font-lato text-[14px] font-bold leading-[20px] text-[#FFFFFF]">
								New User
							</span>
							<AddUserIcon />
						</button>
					)}
				</div>
				<div className="flex grow flex-col overflow-x-auto">
					{isAppUserManagementDataEmpty ? (
						<div className="flex grow flex-col items-center justify-center gap-[56px]">
							<div className="flex flex-col items-center justify-center gap-[8px]">
								<h3 className="first-app-text font-source-sans-pro text-[64px] font-[700] leading-[72px]">
									set-up user(s)
								</h3>
							</div>
							<button
								data-cy="add_user_button"
								type="button"
								onClick={handleAddNewUser}
								className="flex gap-[8px] rounded-[4px] bg-primary px-[16px] py-[7px]"
							>
								<span className="font-lato text-[14px] font-bold leading-[20px] text-[#FFFFFF]">
									Create New User
								</span>
								<AddUserIcon />
							</button>
						</div>
					) : appUserManagementData ? (
						<AppTable />
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
