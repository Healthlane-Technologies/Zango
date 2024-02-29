import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import { ReactComponent as AddUserIcon } from '../../../../assets/images/svg/add-user-icon.svg';
import useApi from '../../../../hooks/useApi';
import BreadCrumbs from '../../../app/components/BreadCrumbs';
import {
	openIsAddPolicyModalOpen,
	selectAppPoliciesManagementData,
	selectAppPoliciesManagementTableData,
	selectRerenderPage,
	setAppPoliciesManagementData,
} from '../../slice';
import AddPolicyModal from '../Models/AddPolicyModal';
import DeletePolicyModal from '../Models/DeletePolicyModal';
import EditPolicyModal from '../Models/EditPolicyModal';
import ViewPolicyModal from '../Models/ViewPolicyModal';
import Table from '../Table';

export default function AppPoliciesManagement() {
	let { appId } = useParams();
	const appPoliciesManagementData = useSelector(
		selectAppPoliciesManagementData
	);
	const appPoliciesManagementTableData = useSelector(
		selectAppPoliciesManagementTableData
	);
	const rerenderPage = useSelector(selectRerenderPage);
	const isAppPoliciesManagementDataEmpty = false;

	const dispatch = useDispatch();

	const handleAddPolicy = () => {
		dispatch(openIsAddPolicyModalOpen());
	};

	function updateAppPoliciesManagementData(value) {
		dispatch(setAppPoliciesManagementData(value));
	}

	const triggerApi = useApi();

	useEffect(() => {
		let columnFilter = appPoliciesManagementTableData?.columns
			? appPoliciesManagementTableData?.columns
					?.map(({ id, value }) => {
						return `&search_${id}=${value}`;
					})
					.join('')
			: '';

		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/policies/?page=${
					appPoliciesManagementTableData?.pageIndex + 1
				}&page_size=${
					appPoliciesManagementTableData?.pageSize
				}&include_dropdown_options=true&search=${
					appPoliciesManagementTableData?.searchValue
				}${columnFilter?.length ? columnFilter : ''}`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				updateAppPoliciesManagementData(response);
			}
		};

		makeApiCall();
	}, [rerenderPage]);
	return (
		<>
			<div className="flex grow flex-col gap-[20px]">
				<div className="flex items-center justify-between py-[24px] pl-[40px] pr-[48px]">
					<BreadCrumbs />
					{/* {isAppPoliciesManagementDataEmpty ? null : (
						<button
							type="button"
							onClick={handleAddPolicy}
							className="flex gap-[8px] rounded-[4px] bg-primary px-[16px] py-[7px]"
						>
							<span className="font-lato text-[14px] font-bold leading-[20px] text-[#FFFFFF]">
								Add Policy
							</span>
							<AddUserIcon />
						</button>
					)} */}
				</div>
				<div className="flex grow flex-col overflow-x-auto">
					{isAppPoliciesManagementDataEmpty ? (
						<div className="flex grow flex-col items-center justify-center gap-[56px]">
							<div className="flex flex-col items-center justify-center gap-[8px]">
								<h3 className="first-app-text font-source-sans-pro text-[64px] font-[700] leading-[72px]">
									set-up policy(s)
								</h3>
								<p className="font-source-sans-pro text-[18px] font-semibold leading-[24px] text-[#212429]">
									description to be added
								</p>
							</div>
							<button
								type="button"
								onClick={handleAddPolicy}
								className="flex gap-[8px] rounded-[4px] bg-primary px-[16px] py-[7px]"
							>
								<span className="font-lato text-[14px] font-bold leading-[20px] text-[#FFFFFF]">
									Add New Policy
								</span>
								<AddUserIcon />
							</button>
						</div>
					) : appPoliciesManagementData ? (
						<Table tableData={appPoliciesManagementData?.policies} />
					) : null}
				</div>
			</div>
			<AddPolicyModal />
			<EditPolicyModal />
			<DeletePolicyModal />
			<ViewPolicyModal />
		</>
	);
}
