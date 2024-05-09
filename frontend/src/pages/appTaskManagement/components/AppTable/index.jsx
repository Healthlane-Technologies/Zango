import debounce from 'just-debounce-it';
import * as React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import Table from '../../../../components/Table';
import {
	selectAppTaskManagementData,
	selectAppTaskManagementTableData,
	setAppTaskManagementData,
	setAppTaskManagementTableData,
} from '../../slice';
import SyncTask from '../SyncTask';
import columns from './columns';
import RowMenu from './RowMenu';

export default function AppTable() {
	let { appId } = useParams();
	const appTaskManagementTableData = useSelector(
		selectAppTaskManagementTableData
	);

	const appTaskManagementData = useSelector(selectAppTaskManagementData);

	const dispatch = useDispatch();

	const updateLocalTableData = (data) => {
		dispatch(setAppTaskManagementTableData(data));
	};

	function updatePageData(value) {
		dispatch(setAppTaskManagementData(value));
	}

	const debounceSearch = debounce((data) => {
		dispatch(setAppTaskManagementTableData(data));
	}, 500);

	return (
		<Table
			localTableData={appTaskManagementTableData}
			searchPlaceholder={'Search Tasks by name / ID / policy(s)'}
			tableData={appTaskManagementData?.tasks}
			columns={columns({
				debounceSearch,
				localTableData: appTaskManagementTableData,
			})}
			pageData={appTaskManagementData}
			pageId={'tasks'}
			apiUrl={`/api/v1/apps/${appId}/tasks/`}
			updatePageData={updatePageData}
			updateLocalTableData={updateLocalTableData}
			RowMenu={RowMenu}
			SearchFilters={<SyncTask />}
		/>
	);
}
