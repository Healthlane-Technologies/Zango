import { getCoreRowModel, useReactTable } from '@tanstack/react-table';
import { useEffect, useMemo } from 'react';
import useApi from '../../hooks/useApi';
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
	updatePageData,
	updateLocalTableData,
	RowMenu = null,
	apiUrl,
	apiQuery = '',
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

	const triggerApi = useApi();

	useEffect(() => {
		let { pageIndex, pageSize } = pagination;

		let columnFilter = localTableData?.columns
			? localTableData?.columns
					?.filter(({ id, value }) => {
						if (
							typeof value === 'object' &&
							!Array.isArray(value) &&
							isNaN(parseInt(value))
						) {
							return value?.start && value?.end;
						} else {
							return value;
						}
					})
					?.map(({ id, value }) => {
						if (
							typeof value === 'object' &&
							!Array.isArray(value) &&
							isNaN(parseInt(value))
						) {
							return `&search_${id}=${JSON.stringify(value)}`;
						} else {
							return `&search_${id}=${value}`;
						}
					})
					.join('')
			: '';

		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `${apiUrl}?page=${pageIndex + 1}&page_size=${pageSize}${
					apiQuery ? apiQuery : ''
				}&include_dropdown_options=true&search=${localTableData?.searchValue}${
					columnFilter?.length ? columnFilter : ''
				}`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				updatePageData(response);
			}
		};

		makeApiCall();
	}, [localTableData]);

	return (
		<div
			className={`flex ${
				haveSideMenu ? 'max-w-[calc(100vw_-_88px)]' : 'max-w-[100vw]'
			}  grow flex-col overflow-auto`}
		>
			<TableSearch
				searchPlaceholder={searchPlaceholder}
				localTableData={localTableData}
				updateLocalTableData={updateLocalTableData}
				SearchFilters={SearchFilters}
			/>
			<div className="relative flex grow overflow-x-auto overflow-y-auto">
				<table className="h-fit w-full border-collapse">
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
