import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import { ReactComponent as AddUserIcon } from '../../../../assets/images/svg/add-user-icon.svg';
import useApi from '../../../../hooks/useApi';
import BreadCrumbs from '../../../app/components/BreadCrumbs';
import {
	selectAppTaskManagementData,
	selectRerenderPage,
	setAppTaskManagementData,
	selectAppTaskManagementTableData,
	selectIsAppTaskManagementDataEmpty,
} from '../../slice';
import RemoveAllPoliciesModal from '../Models/RemoveAllPoliciesModal';
import UpdatePolicyModal from '../Models/UpdatePolicyModal';
import SyncTask from '../SyncTask';
import Table from '../Table';

export default function AppTaskManagement() {
	let { appId } = useParams();
	const appTaskManagementData = useSelector(selectAppTaskManagementData);
	const taskManagementRolesTableData = useSelector(
		selectAppTaskManagementTableData
	);
	const rerenderPage = useSelector(selectRerenderPage);
	const isAppTaskManagementDataEmpty = useSelector(
		selectIsAppTaskManagementDataEmpty
	);

	const dispatch = useDispatch();

	function updateAppTaskManagementData(value) {
		dispatch(setAppTaskManagementData(value));
	}

	const triggerApi = useApi();

	useEffect(() => {
		let columnFilter = taskManagementRolesTableData?.columns
			? taskManagementRolesTableData?.columns
					?.map(({ id, value }) => {
						return `&search_${id}=${value}`;
					})
					.join('')
			: '';

		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/tasks/?page=${
					taskManagementRolesTableData?.pageIndex + 1
				}&page_size=${
					taskManagementRolesTableData?.pageSize
				}&include_dropdown_options=true&search=${
					taskManagementRolesTableData?.searchValue
				}${columnFilter?.length ? columnFilter : ''}`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				updateAppTaskManagementData(response);
			}
		};

		makeApiCall();
	}, [rerenderPage]);

	return (
		<>
			<div className="flex grow flex-col gap-[20px]">
				<div className="flex items-center justify-between py-[24px] pl-[40px] pr-[48px]">
					<BreadCrumbs />
				</div>
				<div className="flex grow flex-col overflow-x-auto">
					{isAppTaskManagementDataEmpty ? (
						<div className="flex grow flex-col items-center justify-center gap-[56px]">
							<div className="flex flex-col items-center justify-center gap-[8px]">
								<h3 className="first-app-text font-source-sans-pro text-[64px] font-[700] leading-[72px]">
									set-up task management(s)
								</h3>
								{/* <p className="font-source-sans-pro text-[18px] font-semibold leading-[24px] text-[#212429]">
									description to be added
								</p> */}
							</div>
							<SyncTask theme="dark" />
						</div>
					) : appTaskManagementData ? (
						<div className="flex grow flex-col overflow-x-auto">
							<Table tableData={appTaskManagementData?.tasks} />
						</div>
					) : null}
				</div>
			</div>
			<UpdatePolicyModal />
			<RemoveAllPoliciesModal />
		</>
	);
}
