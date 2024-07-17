import debounce from 'just-debounce-it';
import * as React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import Table from '../../../../components/Table';
import {
	selectAppAccessLogsData,
	selectAppAccessLogsTableData,
	setAppAccessLogsData,
	setAppAccessLogsTableData,
} from '../../slice';
import columns from './columns';

export default function AppTable() {
	const appAccessLogsTableData = useSelector(selectAppAccessLogsTableData);

	const appAccessLogsData = useSelector(selectAppAccessLogsData);

	const dispatch = useDispatch();

	function updateAppAccessLogsData(data) {
		dispatch(setAppAccessLogsData(data));
	}

	const debounceSearch = debounce((data) => {
		dispatch(setAppAccessLogsTableData(data));
	}, 500);

	return (
		<Table
			localTableData={appAccessLogsTableData}
			searchPlaceholder={
				'Search Access Logs by ID / User / IP Address / User Agent'
			}
			tableData={appAccessLogsData?.access_logs}
			columns={columns({
				debounceSearch,
				localTableData: appAccessLogsTableData,
				tableData: appAccessLogsData,
			})}
			updateLocalTableData={updateAppAccessLogsData}
		/>
	);
}
