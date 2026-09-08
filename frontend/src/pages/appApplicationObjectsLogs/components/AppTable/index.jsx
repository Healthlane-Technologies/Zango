import debounce from 'just-debounce-it';
import * as React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import ExportButton from '../../../../components/ExportButton';
import Table from '../../../../components/Table';
import {
	selectAppApplicationObjectsLogsData,
	selectAppApplicationObjectsLogsTableData,
	setAppApplicationObjectsLogsTableData,
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
	const appApplicationObjectsLogsData = useSelector(
		selectAppApplicationObjectsLogsData
	);
	const appApplicationObjectsLogsTableData = useSelector(
		selectAppApplicationObjectsLogsTableData
	);

	const dispatch = useDispatch();

	const updateLocalTableData = (data) => {
		dispatch(setAppApplicationObjectsLogsTableData(data));
	};

	const debounceSearch = debounce((data) => {
		dispatch(setAppApplicationObjectsLogsTableData(data));
	}, 500);

	const exportFilters = {
		search: appApplicationObjectsLogsTableData?.searchValue || '',
		columns: columnsArrayToDict(
			appApplicationObjectsLogsTableData?.columns
		),
	};

	return (
		<Table
			localTableData={appApplicationObjectsLogsTableData}
			searchPlaceholder={
				'Search Application Objects Logs by Object ID / Log ID / actor / changes'
			}
			tableData={appApplicationObjectsLogsData?.audit_logs}
			columns={columns({
				debounceSearch,
				localTableData: appApplicationObjectsLogsTableData,
				tableData: appApplicationObjectsLogsData,
			})}
			updateLocalTableData={updateLocalTableData}
			SearchFilters={
				<ExportButton kind="audit_logs_app" filters={exportFilters} />
			}
		/>
	);
}
