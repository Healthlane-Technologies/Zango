import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import useApi from '../../../../hooks/useApi';
import BreadCrumbs from '../../../app/components/BreadCrumbs';
import {
	selectAppApplicationObjectsLogsData,
	selectAppApplicationObjectsLogsTableData,
	selectIsAppApplicationObjectsLogsDataEmpty,
	selectRerenderPage,
	setAppApplicationObjectsLogsData,
} from '../../slice';
import AppTable from '../AppTable';

export default function AppApplicationObjectsLogs() {
	let { appId } = useParams();
	const rerenderPage = useSelector(selectRerenderPage);
	const appApplicationObjectsLogsData = useSelector(
		selectAppApplicationObjectsLogsData
	);
	const appApplicationObjectsLogsTableData = useSelector(
		selectAppApplicationObjectsLogsTableData
	);
	const isAppApplicationObjectsLogsDataEmpty = useSelector(
		selectIsAppApplicationObjectsLogsDataEmpty
	);

	const dispatch = useDispatch();

	function updateAppApplicationObjectsLogsData(value) {
		dispatch(setAppApplicationObjectsLogsData(value));
	}

	const triggerApi = useApi();

	useEffect(() => {
		let columnFilter = appApplicationObjectsLogsTableData?.columns
			? appApplicationObjectsLogsTableData?.columns
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
				url: `/api/v1/apps/${appId}/auditlog/?model_type=dynamic_models&page=${
					appApplicationObjectsLogsTableData?.pageIndex + 1
				}&page_size=${
					appApplicationObjectsLogsTableData?.pageSize
				}&include_dropdown_options=true&search=${
					appApplicationObjectsLogsTableData?.searchValue
				}${columnFilter?.length ? columnFilter : ''}`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				updateAppApplicationObjectsLogsData(response);
			}
		};

		makeApiCall();
	}, [rerenderPage, appApplicationObjectsLogsTableData]);

	if (!appApplicationObjectsLogsData) {
		return null;
	}

	return (
		<>
			<div className="flex grow flex-col gap-[20px]">
				<div className="flex items-center justify-between py-[12px] pl-[40px] pr-[48px]">
					<BreadCrumbs />
				</div>
				<div className="flex grow flex-col overflow-x-auto">
					{isAppApplicationObjectsLogsDataEmpty ? (
						<div className="flex grow flex-col items-center justify-center gap-[56px]">
							<div className="flex flex-col items-center justify-center gap-[8px]">
								<h3 className="first-app-text font-source-sans-pro text-[64px] font-[700] leading-[72px]">
									application objects logs
								</h3>
							</div>
						</div>
					) : appApplicationObjectsLogsData ? (
						<AppTable />
					) : null}
				</div>
			</div>
		</>
	);
}
