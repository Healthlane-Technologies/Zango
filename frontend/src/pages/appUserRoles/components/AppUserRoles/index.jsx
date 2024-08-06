import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import { ReactComponent as AddUserIcon } from '../../../../assets/images/svg/add-user-icon.svg';
import useApi from '../../../../hooks/useApi';
import BreadCrumbs from '../../../app/components/BreadCrumbs';
import {
	openIsAddNewUserRolesModalOpen,
	selectAppUserRolesData,
	selectAppUserRolesTableData,
	selectIsAppUserRolesDataEmpty,
	selectRerenderPage,
	setAppUserRolesData,
} from '../../slice';
import AppTable from '../AppTable';
import ActivateUserRolesModal from '../Modals/ActivateUserRolesModal';
import AddNewUserRolesModal from '../Modals/AddNewUserRolesModal';
import DeactivateUserRolesModal from '../Modals/DeactivateUserRolesModal';
import EditUserRolesDetailsModal from '../Modals/EditUserDetailsRolesModal';

export default function AppUserRoles() {
	let { appId } = useParams();
	const appUserRolesData = useSelector(selectAppUserRolesData);
	const appUserRolesTableData = useSelector(selectAppUserRolesTableData);
	const rerenderPage = useSelector(selectRerenderPage);
	const isAppUserRolesDataEmpty = useSelector(selectIsAppUserRolesDataEmpty);

	const dispatch = useDispatch();

	const handleAddNewUser = () => {
		dispatch(openIsAddNewUserRolesModalOpen());
	};

	function updateAppUserRolesData(value) {
		dispatch(setAppUserRolesData(value));
	}

	const triggerApi = useApi();

	useEffect(() => {
		let columnFilter = appUserRolesTableData?.columns
			? appUserRolesTableData?.columns
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
				url: `/api/v1/apps/${appId}/roles/?page=${
					appUserRolesTableData?.pageIndex + 1
				}&page_size=${
					appUserRolesTableData?.pageSize
				}&include_dropdown_options=true&search=${
					appUserRolesTableData?.searchValue
				}${columnFilter?.length ? columnFilter : ''}`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				updateAppUserRolesData(response);
			}
		};

		makeApiCall();
	}, [rerenderPage, appUserRolesTableData]);

	if (!appUserRolesData) {
		return null;
	}

	return (
		<>
			<div className="flex grow flex-col gap-[20px]">
				<div className="flex items-center justify-between py-[12px] pl-[40px] pr-[48px]">
					<BreadCrumbs />
					{isAppUserRolesDataEmpty ? null : (
						<button
							data-cy="add_user_role_button"	
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
					{isAppUserRolesDataEmpty ? (
						<div className="flex grow flex-col items-center justify-center gap-[56px]">
							<div className="flex flex-col items-center justify-center gap-[8px]">
								<h3 className="first-app-text font-source-sans-pro text-[64px] font-[700] leading-[72px]">
									set-up user role(s)
								</h3>
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
					) : appUserRolesData ? (
						<AppTable tableData={appUserRolesData?.users} />
					) : null}
				</div>
			</div>
			<AddNewUserRolesModal />
			<EditUserRolesDetailsModal />
			<DeactivateUserRolesModal />
			<ActivateUserRolesModal />
		</>
	);
}
