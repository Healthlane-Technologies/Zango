import BreadCrumbs from '../BreadCrumbs';
import Table from '../Table';
import UpdatePolicyModal from '../Models/UpdatePolicyModal';
import RemoveAllPoliciesModal from '../Models/RemoveAllPoliciesModal';
import {
	selectAppTaskManagementData,
	setAppTaskManagementData,
} from '../../slice';
import useApi from '../../../../hooks/useApi';
import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';

export default function AppTaskManagement() {
	const appTaskManagementData = useSelector(selectAppTaskManagementData);

	const dispatch = useDispatch();

	function updateAppTaskManagementData(value) {
		dispatch(setAppTaskManagementData(value));
	}

	const triggerApi = useApi();

	useEffect(() => {
		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/02248bb4-e120-48fa-bb64-a1c6ee032cb5/tasks/`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				updateAppTaskManagementData(response);
			}
		};

		makeApiCall();
	}, []);

	return (
		<>
			<div className="flex grow flex-col gap-[20px]">
				<div className="flex items-center justify-between py-[24px] pl-[40px] pr-[48px]">
					<BreadCrumbs />
				</div>
				<div className="flex grow flex-col overflow-x-auto">
					<div className="flex grow flex-col overflow-x-auto">
						{appTaskManagementData ? (
							<Table tableData={appTaskManagementData?.tasks} />
						) : null}
					</div>
				</div>
			</div>
			<UpdatePolicyModal />
			<RemoveAllPoliciesModal />
		</>
	);
}
