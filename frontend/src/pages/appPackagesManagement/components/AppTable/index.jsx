import debounce from 'just-debounce-it';
import * as React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import Table from '../../../../components/Table';
import {
	selectAppPackagesManagementData,
	selectAppPackagesManagementTableData,
	setAppPackagesManagementTableData,
} from '../../slice';
import columns from './columns';
import RowMenu from './RowMenu';

export default function AppTable() {
	const appPackagesManagementTableData = useSelector(
		selectAppPackagesManagementTableData
	);

	const appPackagesManagementData = useSelector(
		selectAppPackagesManagementData
	);

	const dispatch = useDispatch();

	const updateLocalTableData = (data) => {
		dispatch(setAppPackagesManagementTableData(data));
	};

	const debounceSearch = debounce((data) => {
		dispatch(setAppPackagesManagementTableData(data));
	}, 500);

	return (
		<Table
			localTableData={appPackagesManagementTableData}
			searchPlaceholder={'Search Packages by name'}
			tableData={appPackagesManagementData?.packages}
			columns={columns({
				debounceSearch,
				localTableData: appPackagesManagementTableData,
				dispatch: dispatch,

			})}
			updateLocalTableData={updateLocalTableData}
			RowMenu={RowMenu}
		/>
	);
}
