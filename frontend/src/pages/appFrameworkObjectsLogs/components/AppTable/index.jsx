import debounce from 'just-debounce-it';
import * as React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import ExportButton from '../../../../components/ExportButton';
import Table from '../../../../components/Table';
import {
	selectAppFrameworkObjectsLogsData,
	selectAppFrameworkObjectsLogsTableData,
	setAppFrameworkObjectsLogsTableData,
} from '../../slice';
import columns from './columns';

function columnsArrayToDict(columnsArr) {
	const out = {};
	(columnsArr || []).forEach(({ id, value }) => {
		if (value !== undefined && value !== null && value !== '') {
			out[id] = value;
		}
	});
	return out;
}

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

	const exportFilters = {
		search: appFrameworkObjectsLogsTableData?.searchValue || '',
		columns: columnsArrayToDict(appFrameworkObjectsLogsTableData?.columns),
	};

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
			SearchFilters={
				<ExportButton kind="audit_logs_framework" filters={exportFilters} />
			}
		/>
	);
}
