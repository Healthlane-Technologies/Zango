import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import useApi from '../../../../hooks/useApi';
import BreadCrumbs from '../../../app/components/BreadCrumbs';
import {
	selectAppAccessLogsData,
	selectAppAccessLogsTableData,
	selectIsAppAccessLogsDataEmpty,
	selectRerenderPage,
	setAppAccessLogsData,
} from '../../slice';
import Table from '../Table';

export default function AppAccessLogs() {
	let { appId } = useParams();
	const appAccessLogsData = useSelector(selectAppAccessLogsData);
	const appAccessLogsTableData = useSelector(selectAppAccessLogsTableData);
	const rerenderPage = useSelector(selectRerenderPage);
	const isAppAccessLogsDataEmpty = useSelector(selectIsAppAccessLogsDataEmpty);
	const dispatch = useDispatch();

	function updateAppAccessLogsData(value) {
		dispatch(setAppAccessLogsData(value));
	}

	const triggerApi = useApi();

	useEffect(() => {
		let columnFilter = appAccessLogsTableData?.columns
			? appAccessLogsTableData?.columns
					?.map(({ id, value }) => {
						return `&search_${id}=${value}`;
					})
					.join('')
			: '';

		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/access-logs/?page=${
					appAccessLogsTableData?.pageIndex + 1
				}&page_size=${
					appAccessLogsTableData?.pageSize
				}&include_dropdown_options=true&search=${
					appAccessLogsTableData?.searchValue
				}${columnFilter?.length ? columnFilter : ''}`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				updateAppAccessLogsData(response);
			}
		};

		makeApiCall();
	}, [rerenderPage]);

	return (
		<>
			<div className="flex grow flex-col gap-[20px]">
				<div className="flex items-center justify-between py-[12px] pl-[40px] pr-[48px]">
					<BreadCrumbs />
				</div>
				<div className="flex grow flex-col overflow-x-auto">
					{isAppAccessLogsDataEmpty ? (
						<div className="flex grow flex-col items-center justify-center gap-[56px]">
							<div className="flex flex-col items-center justify-center gap-[8px]">
								<h3 className="first-app-text font-source-sans-pro text-[64px] font-[700] leading-[72px]">
									access log(s)
								</h3>
							</div>
						</div>
					) : appAccessLogsData ? (
						<Table tableData={appAccessLogsData?.users} />
					) : null}
				</div>
			</div>
		</>
	);
}
