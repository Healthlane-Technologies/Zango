import debounce from 'just-debounce-it';
import * as React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import Table from '../../../../components/Table';
import {
	selectPlatformUserManagementData,
	selectPlatformUserManagementTableData,
	setPlatformUserManagementData,
	setPlatformUserManagementTableData,
} from '../../slice';
import columns from './columns';
import RowMenu from './RowMenu';

export default function AppTable({ tableData }) {
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

	function updatePageData(value) {
		dispatch(setPlatformUserManagementData(value));
	}

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
			pageData={platformUserManagementData}
			pageId={'platform-users'}
			apiUrl={`/api/v1/auth/platform-users/`}
			updatePageData={updatePageData}
			updateLocalTableData={updateLocalTableData}
			RowMenu={RowMenu}
			haveSideMenu={false}
		/>
	);
}
