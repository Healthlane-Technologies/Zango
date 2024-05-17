import debounce from 'just-debounce-it';
import * as React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import Table from '../../../../components/Table';
import {
	selectAppTaskManagementData,
	selectAppTaskManagementTableData,
	setAppTaskManagementTableData,
} from '../../slice';
import SyncTask from '../SyncTask';
import columns from './columns';
import RowMenu from './RowMenu';

export default function AppTable() {
	const appTaskManagementTableData = useSelector(
		selectAppTaskManagementTableData
	);

	const appTaskManagementData = useSelector(selectAppTaskManagementData);

	const dispatch = useDispatch();

	const updateLocalTableData = (data) => {
		dispatch(setAppTaskManagementTableData(data));
	};

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
			updateLocalTableData={updateLocalTableData}
			RowMenu={RowMenu}
			SearchFilters={<SyncTask />}
		/>
	);
}
