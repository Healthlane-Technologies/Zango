import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import { ReactComponent as AddUserIcon } from '../../../../assets/images/svg/add-user-icon.svg';
import useApi from '../../../../hooks/useApi';
import BreadCrumbs from '../../../app/components/BreadCrumbs';
import {
	openIsAddCustomPermissionModalOpen,
	selectAppPermissionsManagementData,
	selectRerenderPage,
	setAppPermissionsManagementData,
} from '../../slice';
import AddCustomPermissionModal from '../Modals/AddCustomPermissionModal';
import DeleteCustomPermissionModal from '../Modals/DeleteCustomPermissionModal';
import EditCustomPermissionModal from '../Modals/EditCustomPermissionModal';
import Table from '../Table';

export default function AppPermissionsManagement() {
	let { appId } = useParams();
	const rerenderPage = useSelector(selectRerenderPage);

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
				url: `/api/v1/apps/${appId}/permissions/?include_dropdown_options=true`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				updateAppPermissionsManagementData(response);
			}
		};

		makeApiCall();
	}, [rerenderPage, appId, triggerApi]);

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
