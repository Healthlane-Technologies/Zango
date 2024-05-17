import debounce from 'just-debounce-it';
import * as React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import Table from '../../../../components/Table';
import {
	selectAppFrameworkObjectsLogsData,
	selectAppFrameworkObjectsLogsTableData,
	setAppFrameworkObjectsLogsTableData,
} from '../../slice';
import columns from './columns';

export default function AppTable() {
	const appFrameworkObjectsLogsTableData = useSelector(
		selectAppFrameworkObjectsLogsTableData
	);
	const appFrameworkObjectsLogsData = useSelector(
		selectAppFrameworkObjectsLogsData
	);

	const dispatch = useDispatch();

	const updateLocalTableData = (data) => {
		dispatch(setAppFrameworkObjectsLogsTableData(data));
	};

	const debounceSearch = debounce((data) => {
		dispatch(setAppFrameworkObjectsLogsTableData(data));
	}, 500);

	return (
		<Table
			localTableData={appFrameworkObjectsLogsTableData}
			searchPlaceholder={
				'Search Framework Objects Logs by Object ID / Log ID / actor / changes'
			}
			tableData={appFrameworkObjectsLogsData?.audit_logs}
			columns={columns({
				debounceSearch,
				localTableData: appFrameworkObjectsLogsTableData,
				tableData: appFrameworkObjectsLogsData,
			})}
			updateLocalTableData={updateLocalTableData}
		/>
	);
}
