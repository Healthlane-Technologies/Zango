import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import useApi from '../../../../hooks/useApi';
import BreadCrumbs from '../../../app/components/BreadCrumbs';
import {
	selectAppPackagesManagementData,
	selectAppPackagesManagementTableData,
	selectRerenderPage,
	setAppPackagesManagementData,
} from '../../slice';
import AppTable from '../AppTable';
import ConfigurePackageModal from '../Modals/ConfigurePackageModal';
import InstallPackageModal from '../Modals/InstallPackageModal';

export default function AppPackagesManagement() {
	let { appId } = useParams();
	const appPackagesManagementData = useSelector(
		selectAppPackagesManagementData
	);
	const appPackagesManagementTableData = useSelector(
		selectAppPackagesManagementTableData
	);
	const rerenderPage = useSelector(selectRerenderPage);

	const dispatch = useDispatch();

	function updateAppPackagesManagementData(value) {
		dispatch(setAppPackagesManagementData(value));
	}

	const triggerApi = useApi();

	useEffect(() => {
		let columnFilter = appPackagesManagementTableData?.columns
			? appPackagesManagementTableData?.columns
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
				url: `/api/v1/apps/${appId}/packages/?page=${
					appPackagesManagementTableData?.pageIndex + 1
				}&page_size=${
					appPackagesManagementTableData?.pageSize
				}&include_dropdown_options=true&search=${
					appPackagesManagementTableData?.searchValue
				}${columnFilter?.length ? columnFilter : ''}`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				updateAppPackagesManagementData(response);
			}
		};

		makeApiCall();
	}, [rerenderPage, appPackagesManagementTableData]);

	if (!appPackagesManagementData) {
		return null;
	}

	return (
		<>
			<div className="flex grow flex-col gap-[20px]">
				<div className="flex items-center justify-between py-[24px] pl-[40px] pr-[48px]">
					<BreadCrumbs />
				</div>
				<div className="flex grow flex-col overflow-x-auto">
					<div className="flex grow flex-col overflow-x-auto">
						{appPackagesManagementData ? <AppTable /> : null}
					</div>
				</div>
			</div>
			<ConfigurePackageModal />
			<InstallPackageModal />
		</>
	);
}
