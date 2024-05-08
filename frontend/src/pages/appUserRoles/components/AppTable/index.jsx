import debounce from 'just-debounce-it';
import * as React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import Table from '../../../../components/Table';
import {
	selectAppUserRolesData,
	selectAppUserRolesTableData,
	setAppUserRolesData,
	setAppUserRolesTableData,
} from '../../slice';
import columns from './columns';
import RowMenu from './RowMenu';

export default function AppTable({ tableData }) {
	const { appId } = useParams();
	const appUserRolesTableData = useSelector(selectAppUserRolesTableData);
	const appUserRolesData = useSelector(selectAppUserRolesData);
	const dispatch = useDispatch();
	const updateLocalTableData = (data) => {
		dispatch(setAppUserRolesTableData(data));
	};

	function updatePageData(value) {
		dispatch(setAppUserRolesData(value));
	}

	const debounceSearch = debounce((data) => {
		dispatch(setAppUserRolesTableData(data));
	}, 500);

	return (
		<Table
			localTableData={appUserRolesTableData}
			tableData={appUserRolesData?.roles}
			columns={columns({
				debounceSearch,
				localTableData: appUserRolesTableData,
			})}
			pageData={appUserRolesData}
			pageId={'roles'}
			apiUrl={`/api/v1/apps/${appId}/roles/`}
			updatePageData={updatePageData}
			updateLocalTableData={updateLocalTableData}
			RowMenu={RowMenu}
		/>
	);
}
