import { getCoreRowModel, useReactTable } from '@tanstack/react-table';
import debounce from 'just-debounce-it';
import * as React from 'react';
import { useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import Table from '../../../../components/Table';
import {
	selectAppUserManagementData,
	selectAppUserManagementTableData,
	setAppUserManagementTableData,
} from '../../slice';
import columns from './columns';
import RowMenu from './RowMenu';

export default function AppTable() {
	const appUserManagementTableData = useSelector(
		selectAppUserManagementTableData
	);

	const defaultData = useMemo(() => [], []);

	const pagination = useMemo(
		() => ({
			pageIndex: appUserManagementTableData?.pageIndex,
			pageSize: appUserManagementTableData?.pageSize,
		}),
		[appUserManagementTableData]
	);

	const appUserManagementData = useSelector(selectAppUserManagementData);

	const table = useReactTable({
		data: appUserManagementData.users?.records ?? defaultData,
		columns,
		pageCount: appUserManagementData.users?.total_pages ?? -1,
		state: {
			pagination,
		},
		onPaginationChange: (updater) => {
			if (typeof updater !== 'function') return;

			const newPageInfo = updater(table.getState().pagination);

			dispatch(
				setAppUserManagementTableData({
					...appUserManagementTableData,
					...newPageInfo,
				})
			);
		},
		getCoreRowModel: getCoreRowModel(),
		manualPagination: true,
	});

	const dispatch = useDispatch();

	const updateLocalTableData = (data) => {
		dispatch(setAppUserManagementTableData(data));
	};

	const debounceSearch = debounce((data) => {
		dispatch(setAppUserManagementTableData(data));
	}, 500);

	return (
		<Table
			localTableData={appUserManagementTableData}
			searchPlaceholder={'Search Users by name / ID / role(s) / mobile / email'}
			tableData={appUserManagementData?.users}
			columns={columns({
				debounceSearch,
				localTableData: appUserManagementTableData,
			})}
			updateLocalTableData={updateLocalTableData}
			RowMenu={RowMenu}
		/>
	);
}
