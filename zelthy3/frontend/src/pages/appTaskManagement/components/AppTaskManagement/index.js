import BreadCrumbs from '../BreadCrumbs';
import Table from '../Table';
import UpdatePolicyModal from '../Models/UpdatePolicyModal';
import RemoveAllPoliciesModal from '../Models/RemoveAllPoliciesModal';
import {
	selectAppTaskManagementData,
	selectRerenderPage,
	setAppTaskManagementData,
} from '../../slice';
import useApi from '../../../../hooks/useApi';
import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';

export default function AppTaskManagement() {
	let { appId } = useParams();
	const rerenderPage = useSelector(selectRerenderPage);

	const appTaskManagementData = useSelector(selectAppTaskManagementData);

	const dispatch = useDispatch();

	function updateAppTaskManagementData(value) {
		dispatch(setAppTaskManagementData(value));
	}

	const triggerApi = useApi();

	useEffect(() => {
		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/tasks/`,
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
