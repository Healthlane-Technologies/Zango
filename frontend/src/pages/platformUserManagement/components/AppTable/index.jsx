import debounce from 'just-debounce-it';
import * as React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import Table from '../../../../components/Table';
import {
	selectPlatformUserManagementData,
	selectPlatformUserManagementTableData,
	setPlatformUserManagementTableData,
} from '../../slice';
import columns from './columns';
import RowMenu from './RowMenu';

export default function AppTable() {
	const platformUserManagementTableData = useSelector(
		selectPlatformUserManagementTableData
	);
	const platformUserManagementData = useSelector(
		selectPlatformUserManagementData
	);
	const dispatch = useDispatch();

	const updateLocalTableData = (data) => {
		dispatch(setPlatformUserManagementTableData(data));
	};

	const debounceSearch = debounce((data) => {
		dispatch(setPlatformUserManagementTableData(data));
	}, 500);

	return (
		<Table
			localTableData={platformUserManagementTableData}
			searchPlaceholder={'Search Users by name / ID / role(s)'}
			tableData={platformUserManagementData?.platform_users}
			columns={columns({
				debounceSearch,
				localTableData: platformUserManagementTableData,
			})}
			updateLocalTableData={updateLocalTableData}
			RowMenu={RowMenu}
			haveSideMenu={false}
		/>
	);
}
