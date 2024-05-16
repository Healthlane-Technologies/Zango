import debounce from 'just-debounce-it';
import * as React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import Table from '../../../../components/Table';
import {
	selectAppApplicationObjectsLogsData,
	selectAppApplicationObjectsLogsTableData,
	setAppApplicationObjectsLogsData,
	setAppApplicationObjectsLogsTableData,
} from '../../slice';
import columns from './columns';

export default function AppTable() {
	const { appId } = useParams();
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

	function updatePageData(value) {
		dispatch(setAppApplicationObjectsLogsData(value));
	}

	const debounceSearch = debounce((data) => {
		dispatch(setAppApplicationObjectsLogsTableData(data));
	}, 500);

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
			pageData={appApplicationObjectsLogsData}
			pageId={'users'}
			// TODO: global api reference
			apiUrl={`/api/v1/apps/${appId}/auditlog/`}
			// TODO: remove apiQuery
			apiQuery={`&model_type=dynamic_models`}
			updatePageData={updatePageData}
			updateLocalTableData={updateLocalTableData}
		/>
	);
}
