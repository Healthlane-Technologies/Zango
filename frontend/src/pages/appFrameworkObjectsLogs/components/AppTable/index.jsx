import debounce from 'just-debounce-it';
import * as React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import Table from '../../../../components/Table';
import {
	selectAppFrameworkObjectsLogsData,
	selectAppFrameworkObjectsLogsTableData,
	setAppFrameworkObjectsLogsData,
	setAppFrameworkObjectsLogsTableData,
} from '../../slice';
import columns from './columns';

export default function AppTable() {
	const { appId } = useParams();
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

	function updatePageData(value) {
		dispatch(setAppFrameworkObjectsLogsData(value));
	}

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
			pageData={appFrameworkObjectsLogsData}
			pageId={'users'}
			apiUrl={`/api/v1/apps/${appId}/auditlog/`}
			apiQuery={`&model_type=core_models`}
			updatePageData={updatePageData}
			updateLocalTableData={updateLocalTableData}
		/>
	);
}
