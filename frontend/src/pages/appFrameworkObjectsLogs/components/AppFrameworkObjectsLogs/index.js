import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import useApi from '../../../../hooks/useApi';
import BreadCrumbs from '../../../app/components/BreadCrumbs';
import {
	selectAppFrameworkObjectsLogsData,
	selectAppFrameworkObjectsLogsTableData,
	selectIsAppFrameworkObjectsLogsDataEmpty,
	selectRerenderPage,
	setAppFrameworkObjectsLogsData,
} from '../../slice';
import AppTable from '../AppTable';

export default function AppFrameworkObjectsLogs() {
	const { appId } = useParams();
	const rerenderPage = useSelector(selectRerenderPage);
	const appFrameworkObjectsLogsData = useSelector(
		selectAppFrameworkObjectsLogsData
	);
	const appFrameworkObjectsLogsTableData = useSelector(
		selectAppFrameworkObjectsLogsTableData
	);
	const isAppFrameworkObjectsLogsDataEmpty = useSelector(
		selectIsAppFrameworkObjectsLogsDataEmpty
	);

	const dispatch = useDispatch();

	function updateAppFrameworkObjectsLogsData(value) {
		dispatch(setAppFrameworkObjectsLogsData(value));
	}

	const triggerApi = useApi();

	useEffect(() => {
		let columnFilter = appFrameworkObjectsLogsTableData?.columns
			? appFrameworkObjectsLogsTableData?.columns
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
				url: `/api/v1/apps/${appId}/auditlog/?model_type=core_models&page=${
					appFrameworkObjectsLogsTableData?.pageIndex + 1
				}&page_size=${
					appFrameworkObjectsLogsTableData?.pageSize
				}&include_dropdown_options=true&search=${
					appFrameworkObjectsLogsTableData?.searchValue
				}${columnFilter?.length ? columnFilter : ''}`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				updateAppFrameworkObjectsLogsData(response);
			}
		};

		makeApiCall();
	}, [rerenderPage, appFrameworkObjectsLogsTableData]);

	if (!appFrameworkObjectsLogsData) {
		return null;
	}

	return (
		<>
			<div className="flex grow flex-col gap-[20px]">
				<div className="flex items-center justify-between py-[12px] pl-[40px] pr-[48px]">
					<BreadCrumbs />
				</div>
				<div className="flex grow flex-col overflow-x-auto">
					{isAppFrameworkObjectsLogsDataEmpty ? (
						<div className="flex grow flex-col items-center justify-center gap-[56px]">
							<div className="flex flex-col items-center justify-center gap-[8px]">
								<h3 className="first-app-text font-source-sans-pro text-[64px] font-[700] leading-[72px]">
									framework objects logs
								</h3>
							</div>
						</div>
					) : appFrameworkObjectsLogsData ? (
						<AppTable />
					) : null}
				</div>
			</div>
		</>
	);
}
