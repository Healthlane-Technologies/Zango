import { getCoreRowModel, useReactTable } from '@tanstack/react-table';
import { useMemo } from 'react';
import TableBody from './TableBody';
import TableEmpty from './TableEmpty';
import TableFooter from './TableFooter';
import TableHead from './TableHead';
import TableSearch from './TableSearch';

function Table({
	columns,
	searchPlaceholder = 'Search',
	localTableData,
	tableData,
	updateLocalTableData,
	RowMenu = null,
	haveSideMenu = true,
	SearchFilters = null,
}) {
	const defaultData = useMemo(() => [], []);

	const pagination = useMemo(
		() => ({
			pageIndex: localTableData?.pageIndex,
			pageSize: localTableData?.pageSize,
		}),
		[localTableData]
	);

	const table = useReactTable({
		data: tableData?.records ?? defaultData,
		columns,
		pageCount: tableData?.total_pages ?? -1,
		state: {
			pagination,
		},
		onPaginationChange: (updater) => {
			if (typeof updater !== 'function') return;

			const newPageInfo = updater(table.getState().pagination);

			updateLocalTableData({
				...localTableData,
				...newPageInfo,
			});
		},
		getCoreRowModel: getCoreRowModel(),
		manualPagination: true,
	});

	return (
		<div
			className={`flex ${
				haveSideMenu ? 'max-w-[calc(100vw_-_88px)]' : 'max-w-[100vw]'
			}  grow flex-col overflow-auto `}
		>
			<TableSearch
				searchPlaceholder={searchPlaceholder}
				localTableData={localTableData}
				updateLocalTableData={updateLocalTableData}
				SearchFilters={SearchFilters}
			/>
			<div className="relative flex grow overflow-x-auto overflow-y-auto">
				<table className="h-fit w-full border-collapse  ">
					<TableHead table={table} />
					<TableBody table={table} RowMenu={RowMenu} />
				</table>
				{table.getRowModel().rows?.length ? null : <TableEmpty />}
			</div>
			<TableFooter table={table} tableData={tableData} />
		</div>
	);
}

export default Table;
