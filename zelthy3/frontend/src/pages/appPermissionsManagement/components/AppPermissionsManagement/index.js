import { useSelector, useDispatch } from 'react-redux';
import {
	openIsAddCustomPermissionModalOpen,
	selectAppPermissionsManagementData,
	setAppPermissionsManagementData,
} from '../../slice';
import BreadCrumbs from '../BreadCrumbs';
import Table from '../Table';
import EditCustomPermissionModal from '../Models/EditCustomPermissionModal';
import DeleteCustomPermissionModal from '../Models/DeleteCustomPermissionModal';
import AddCustomPermissionModal from '../Models/AddCustomPermissionModal';
import { ReactComponent as AddUserIcon } from '../../../../assets/images/svg/add-user-icon.svg';
import useApi from '../../../../hooks/useApi';
import { useEffect } from 'react';

export default function AppPermissionsManagement() {
	const appPermissionsManagementData = useSelector(
		selectAppPermissionsManagementData
	);
	const dispatch = useDispatch();

	const handleAddNewUser = () => {
		dispatch(openIsAddCustomPermissionModalOpen());
	};

	function updateAppPermissionsManagementData(value) {
		dispatch(setAppPermissionsManagementData(value));
	}

	const triggerApi = useApi();

	useEffect(() => {
		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/02248bb4-e120-48fa-bb64-a1c6ee032cb5/permissions/`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				updateAppPermissionsManagementData(response);
			}
		};

		makeApiCall();
	}, []);

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
					{appPermissionsManagementData ? (
						<Table tableData={appPermissionsManagementData?.permissions} />
					) : null}
				</div>
			</div>
			<AddCustomPermissionModal />
			<EditCustomPermissionModal />
			<DeleteCustomPermissionModal />
		</>
	);
}
