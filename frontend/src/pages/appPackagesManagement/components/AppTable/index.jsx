import debounce from 'just-debounce-it';
import * as React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import Table from '../../../../components/Table';
import {
	selectAppPackagesManagementData,
	selectAppPackagesManagementTableData,
	setAppPackagesManagementData,
	setAppPackagesManagementTableData,
} from '../../slice';
import columns from './columns';
import RowMenu from './RowMenu';

export default function AppTable() {
	const { appId } = useParams();
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

	function updatePageData(value) {
		dispatch(setAppPackagesManagementData(value));
	}

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
			pageData={appPackagesManagementData}
			pageId={'packages'}
			apiUrl={`/api/v1/apps/${appId}/packages/`}
			updatePageData={updatePageData}
			updateLocalTableData={updateLocalTableData}
			RowMenu={RowMenu}
		/>
		// <div className="flex max-w-[100vw] grow flex-col overflow-auto">
		// 	<div className="flex bg-[#F0F3F4]">
		// 		<div className="flex grow items-center gap-[24px] py-[13px] pl-[24px] pr-[32px]">
		// 			<div className="flex grow items-center gap-[8px]">
		// 				<TableSearchIcon />
		// 				<input
		// 					ref={searchRef}
		// 					id="searchValue"
		// 					name="searchValue"
		// 					type="text"
		// 					className="w-full bg-transparent font-lato text-sm leading-[20px] tracking-[0.2px] outline-0 ring-0 placeholder:text-[#6C747D]"
		// 					placeholder="Search Packages by name"
		// 					onChange={(e) => handleSearch(e.target.value)}
		// 				/>
		// 			</div>
		// 			{/* <TableFilterIcon />
		// 			<TableColumnFilterIcon /> */}
		// 		</div>
		// 	</div>
		// 	<div className="relative flex max-w-[calc(100vw_-_88px)] grow overflow-x-auto overflow-y-auto">
		// 		<table className="h-fit w-full border-collapse">
		// 			<thead className="sticky top-0 z-[2] bg-[#ffffff]">
		// 				{table.getHeaderGroups().map((headerGroup) => (
		// 					<tr key={headerGroup.id}>
		// 						{headerGroup.headers.map((header) => (
		// 							<th key={header.id} className="p-0 align-top">
		// 								{header.isPlaceholder
		// 									? null
		// 									: flexRender(
		// 											header.column.columnDef.header,
		// 											header.getContext()
		// 									  )}
		// 							</th>
		// 						))}
		// 						<th key="extra-head" className="p-0 align-top">
		// 							<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
		// 								<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]"></span>
		// 							</div>
		// 						</th>
		// 						<th key="extra-head" className="p-0 align-top">
		// 							<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
		// 								<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]"></span>
		// 							</div>
		// 						</th>
		// 						<th key="extra-head2" className="p-0 align-top">
		// 							<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
		// 								<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]"></span>
		// 							</div>
		// 						</th>
		// 					</tr>
		// 				))}
		// 			</thead>
		// 			<tbody>
		// 				{table.getRowModel().rows.map((row) => (
		// 					<tr
		// 						key={row.id}
		// 						className="group relative hover:bg-[#f5f7f8] hover:shadow-table-row"
		// 					>
		// 						{row.getVisibleCells().map((cell) => (
		// 							<td key={cell.id}>
		// 								{flexRender(cell.column.columnDef.cell, cell.getContext())}
		// 							</td>
		// 						))}
		// 						<td>
		// 							<div className="flex h-full flex-col border-b border-[#F0F3F4] px-[20px] py-[14px]">
		// 								<button
		// 									className="flex items-center gap-[12px] disabled:opacity-25"
		// 									onClick={() => {
		// 										dispatch(openIsConfigurePackageModalOpen(row.original));
		// 									}}
		// 									disabled={row.original?.status !== 'Installed'}
		// 								>
		// 									<span
		// 										className={`w-fit min-w-max rounded-[15px] text-center font-lato text-[14px] font-normal capitalize leading-[20px] tracking-[0.2px] text-[#5048ED]`}
		// 									>
		// 										View Details
		// 									</span>
		// 									<DetailEyeIcon />
		// 								</button>
		// 							</div>
		// 						</td>
		// 						<td key="extra-cell" className="w-full">
		// 							<div className="flex h-full flex-col border-b border-[#F0F3F4] px-[20px] py-[14px]">
		// 								<span className="text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]"></span>
		// 							</div>
		// 						</td>
		// 						<td
		// 							key="extra-cell2"
		// 							className="flex h-full w-[188px] flex-col border-b border-[#F0F3F4] px-[20px] py-[14px] group-hover:hidden"
		// 						></td>

		// 						<td className="sticky inset-y-0 right-0 z-[1] hidden h-full w-[188px] items-center justify-end border-b border-[#F0F3F4] bg-gradient-to-l from-[#F5F7F8] from-0% to-90% px-[32px]  group-hover:flex">
		// 							<RowMenu rowData={row.original} />
		// 						</td>
		// 					</tr>
		// 				))}
		// 			</tbody>
		// 		</table>
		// 		{table.getRowModel().rows?.length ? null : (
		// 			<div className="absolute inset-0 flex items-center justify-center">
		// 				<span className="text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
		// 					No data
		// 				</span>
		// 			</div>
		// 		)}
		// 	</div>
		// 	<div className="flex border-t border-[#DDE2E5] py-[4px]">
		// 		<div className="flex grow items-center justify-between py-[7px] pl-[22px] pr-[24px]">
		// 			<span className="font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#212429]">
		// 				Total count: {appPackagesManagementData?.packages?.total_records}
		// 			</span>
		// 			<span className="font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#212429]">
		// 				<PageCountSelectField
		// 					key="page_count"
		// 					label="Counts per page"
		// 					name="page_count"
		// 					id="page_count"
		// 					placeholder="Select"
		// 					value={table.getState().pagination.pageSize}
		// 					optionsDataName="page_count"
		// 					optionsData={[
		// 						{ id: 10, label: 10 },
		// 						{ id: 25, label: 25 },
		// 						{ id: 50, label: 50 },
		// 						{ id: 100, label: 100 },
		// 					]}
		// 					table={table}
		// 				/>
		// 			</span>
		// 		</div>
		// 		<span className="h-full w-[2px] min-w-[2px] bg-[#F0F3F4]"></span>
		// 		<div className="flex w-fit items-center gap-[14px] px-[56px]">
		// 			<button
		// 				type="button"
		// 				className="flex min-h-[24px] min-w-[24px] cursor-pointer items-center justify-center"
		// 				onClick={() => table.previousPage()}
		// 				disabled={!table.getCanPreviousPage()}
		// 			>
		// 				<TablePaginationPreviousIcon />
		// 			</button>
		// 			<div className="flex items-center gap-[8px]">
		// 				<ResizableInput table={table} />
		// 				<span className="font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#212429]">
		// 					/{table.getPageCount()}
		// 				</span>
		// 			</div>
		// 			<button
		// 				type="button"
		// 				className="flex min-h-[24px] min-w-[24px] cursor-pointer items-center justify-center"
		// 				onClick={() => table.nextPage()}
		// 				disabled={!table.getCanNextPage()}
		// 			>
		// 				<TablePaginationNextIcon />
		// 			</button>
		// 		</div>
		// 	</div>
		// </div>
	);
}
