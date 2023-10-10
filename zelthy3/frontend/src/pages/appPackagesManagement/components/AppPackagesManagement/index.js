import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import useApi from '../../../../hooks/useApi';
import {
	selectAppPackagesManagementData,
	selectRerenderPage,
	setAppPackagesManagementData,
} from '../../slice';
import BreadCrumbs from '../BreadCrumbs';
import ConfigurePackageModal from '../Models/ConfigurePackageModal';
import InstallPackageModal from '../Models/InstallPackageModal';
import Table from '../Table';

export default function AppPackagesManagement() {
	let { appId } = useParams();
	const rerenderPage = useSelector(selectRerenderPage);

	const appTaskManagementData = useSelector(selectAppPackagesManagementData);

	const dispatch = useDispatch();

	function updateAppPackagesManagementData(value) {
		dispatch(setAppPackagesManagementData(value));
	}

	const triggerApi = useApi();

	useEffect(() => {
		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/packages/?include_dropdown_options=true`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				updateAppPackagesManagementData(response);
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
							<Table tableData={appTaskManagementData?.packages} />
						) : null}
					</div>
				</div>
			</div>
			<ConfigurePackageModal />
			<InstallPackageModal />
		</>
	);
}
