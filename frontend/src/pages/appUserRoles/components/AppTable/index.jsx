import debounce from 'just-debounce-it';
import * as React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import Table from '../../../../components/Table';
import {
	selectAppUserRolesData,
	selectAppUserRolesTableData,
	setAppUserRolesTableData,
} from '../../slice';
import columns from './columns';
import RowMenu from './RowMenu';

export default function AppTable({ tableData }) {
	const appUserRolesTableData = useSelector(selectAppUserRolesTableData);
	const appUserRolesData = useSelector(selectAppUserRolesData);
	const dispatch = useDispatch();
	const updateLocalTableData = (data) => {
		dispatch(setAppUserRolesTableData(data));
	};

	const debounceSearch = debounce((data) => {
		dispatch(setAppUserRolesTableData(data));
	}, 500);

	return (
		<Table
			localTableData={appUserRolesTableData}
			searchPlaceholder={'Search User roles by role / policy(s)'}
			tableData={appUserRolesData?.roles}
			columns={columns({
				debounceSearch,
				localTableData: appUserRolesTableData,
			})}
			updateLocalTableData={updateLocalTableData}
			RowMenu={RowMenu}
		/>
	);
}
