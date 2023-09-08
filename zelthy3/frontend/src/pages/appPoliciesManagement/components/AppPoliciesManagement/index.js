import { useSelector, useDispatch } from 'react-redux';
import {
	openIsAddPolicyModalOpen,
	selectAppPoliciesManagementData,
	setAppPoliciesManagementData,
} from '../../slice';
import BreadCrumbs from '../BreadCrumbs';
import Table from '../Table';
import EditPolicyModal from '../Models/EditPolicyModal';
import DeletePolicyModal from '../Models/DeletePolicyModal';
import AddPolicyModal from '../Models/AddPolicyModal';
import { ReactComponent as AddUserIcon } from '../../../../assets/images/svg/add-user-icon.svg';
import ViewPolicyModal from '../Models/ViewPolicyModal';
import { useEffect } from 'react';
import useApi from '../../../../hooks/useApi';

export default function AppPoliciesManagement() {
	const appPoliciesManagementData = useSelector(
		selectAppPoliciesManagementData
	);
	const dispatch = useDispatch();

	const handleAddPolicy = () => {
		dispatch(openIsAddPolicyModalOpen());
	};

	function updateAppPoliciesManagementData(value) {
		dispatch(setAppPoliciesManagementData(value));
	}

	const triggerApi = useApi();

	useEffect(() => {
		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/02248bb4-e120-48fa-bb64-a1c6ee032cb5/policies/`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				updateAppPoliciesManagementData(response);
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
						onClick={handleAddPolicy}
						className="flex gap-[8px] rounded-[4px] bg-primary px-[16px] py-[7px]"
					>
						<span className="font-lato text-[14px] font-bold leading-[20px] text-[#FFFFFF]">
							Add Policy
						</span>
						<AddUserIcon />
					</button>
				</div>
				<div className="flex grow flex-col overflow-x-auto">
					{appPoliciesManagementData ? (
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
