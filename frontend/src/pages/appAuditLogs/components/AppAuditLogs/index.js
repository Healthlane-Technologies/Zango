import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import { ReactComponent as AddUserIcon } from '../../../../assets/images/svg/add-user-icon.svg';
import useApi from '../../../../hooks/useApi';
import BreadCrumbs from '../../../app/components/BreadCrumbs';
import {
	openIsAddNewUserModalOpen,
	selectAppAuditLogsData,
	selectAppAuditLogsTableData,
	selectRerenderPage,
	setAppAuditLogsData,
	selectIsAppAuditLogsDataEmpty,
} from '../../slice';
import ActivateUserModal from '../Models/ActivateUserModal';
import AddNewUserModal from '../Models/AddNewUserModal';
import DeactivateUserModal from '../Models/DeactivateUserModal';
import EditUserDetailsModal from '../Models/EditUserDetailsModal';
import ResetPasswordModal from '../Models/ResetPasswordModal';
import Table from '../Table';

export default function AppAuditLogs() {
	let { appId } = useParams();
	const rerenderPage = useSelector(selectRerenderPage);
	const appAuditLogsData = useSelector(selectAppAuditLogsData);
	const appAuditLogsTableData = useSelector(selectAppAuditLogsTableData);
	const isAppAuditLogsDataEmpty = useSelector(selectIsAppAuditLogsDataEmpty);

	const dispatch = useDispatch();

	const handleAddNewUser = () => {
		dispatch(openIsAddNewUserModalOpen());
	};

	function updateAppAuditLogsData(value) {
		dispatch(setAppAuditLogsData(value));
	}

	const triggerApi = useApi();

	useEffect(() => {
		let columnFilter = appAuditLogsTableData?.columns
			? appAuditLogsTableData?.columns
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
				url: `/api/v1/apps/${appId}/auditlog/?page=${
					appAuditLogsTableData?.pageIndex + 1
				}&page_size=${
					appAuditLogsTableData?.pageSize
				}&include_dropdown_options=true&search=${
					appAuditLogsTableData?.searchValue
				}${columnFilter?.length ? columnFilter : ''}`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				updateAppAuditLogsData(response);
			}
		};

		makeApiCall();
	}, [rerenderPage]);

	return (
		<>
			<div className="flex grow flex-col gap-[20px]">
				<div className="flex items-center justify-between py-[12px] pl-[40px] pr-[48px]">
					<BreadCrumbs />
					{/* {isAppAuditLogsDataEmpty ? null : (
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
					)} */}
				</div>
				<div className="flex grow flex-col overflow-x-auto">
					{isAppAuditLogsDataEmpty ? (
						<div className="flex grow flex-col items-center justify-center gap-[56px]">
							<div className="flex flex-col items-center justify-center gap-[8px]">
								<h3 className="first-app-text font-source-sans-pro text-[64px] font-[700] leading-[72px]">
									audit logs
								</h3>
								{/* <p className="font-source-sans-pro text-[18px] font-semibold leading-[24px] text-[#212429]">
									description to be added
								</p> */}
							</div>
							{/* <button
								type="button"
								onClick={handleAddNewUser}
								className="flex gap-[8px] rounded-[4px] bg-primary px-[16px] py-[7px]"
							>
								<span className="font-lato text-[14px] font-bold leading-[20px] text-[#FFFFFF]">
									Create New User
								</span>
								<AddUserIcon />
							</button> */}
						</div>
					) : appAuditLogsData ? (
						<Table tableData={appAuditLogsData?.audit_logs} />
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
