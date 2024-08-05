import {
	createColumnHelper,
	flexRender,
	getCoreRowModel,
	useReactTable,
} from '@tanstack/react-table';
import * as React from 'react';
import { useEffect, useMemo, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import { ReactComponent as TablePaginationNextIcon } from '../../../../assets/images/svg/table-pagination-next-icon.svg';
import { ReactComponent as TablePaginationPreviousIcon } from '../../../../assets/images/svg/table-pagination-previous-icon.svg';
import { ReactComponent as TableSearchIcon } from '../../../../assets/images/svg/table-search-icon.svg';
import useApi from '../../../../hooks/useApi';
import {
	selectAppPermissionsManagementData,
	setAppPermissionsManagementData,
} from '../../slice';
import SyncPermissions from '../SyncPermissions';
import PageCountSelectField from './PageCountSelectField';
import ResizableInput from './ResizableInput';
import RowMenu from './RowMenu';

export default function Table({ tableData }) {
	let { appId } = useParams();

	const columnHelper = createColumnHelper();

	const columns = [
		columnHelper.accessor((row) => row.name, {
			id: 'name',
			header: () => (
				<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] py-[12px] pl-[32px] pr-[20px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Permission Name
					</span>
				</div>
			),
			cell: (info) => {
				return (
					<div className="flex h-full flex-col gap-[8px] border-b border-[#F0F3F4] py-[14px] pl-[32px] pr-[20px]">
						<span className="min-w-max text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
							{info.getValue()}
						</span>
					</div>
				);
			},
		}),
		columnHelper.accessor((row) => row.id, {
			id: 'id',
			header: () => (
				<div className="flex h-full min-w-max items-start justify-start border-b-[4px] border-[#F0F3F4] py-[12px] px-[20px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Permission Id
					</span>
				</div>
			),
			cell: (info) => (
				<div className="flex h-full flex-col border-b border-[#F0F3F4] py-[14px] px-[20px]">
					<span className="text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
						{info.getValue()}
					</span>
				</div>
			),
		}),
		columnHelper.accessor((row) => row.type, {
			id: 'type',
			header: () => (
				<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] py-[12px] px-[20px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Type
					</span>
				</div>
			),
			cell: (info) => (
				<div className="flex h-full flex-col border-b border-[#F0F3F4] py-[14px] px-[20px]">
					<span className="text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
						{info.getValue()}
					</span>
				</div>
			),
		}),
		columnHelper.accessor((row) => row.description, {
			id: 'description',
			header: () => (
				<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] py-[12px] px-[20px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Description
					</span>
				</div>
			),
			cell: (info) => (
				<div className="flex h-full flex-col border-b border-[#F0F3F4] py-[14px] px-[20px]">
					<span className="min-w-max max-w-[200px] text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
						{info.getValue()}
					</span>
				</div>
			),
		}),
	];

	const [{ pageIndex, pageSize }, setPagination] = useState({
		pageIndex: 0,
		pageSize: 10,
	});

	const defaultData = useMemo(() => [], []);

	const pagination = useMemo(
		() => ({
			pageIndex,
			pageSize,
		}),
		[pageIndex, pageSize]
	);

	const appPermissionsManagementData = useSelector(
		selectAppPermissionsManagementData
	);

	const table = useReactTable({
		data: appPermissionsManagementData.permissions?.records ?? defaultData,
		columns,
		pageCount: appPermissionsManagementData.permissions?.total_pages ?? -1,
		state: {
			pagination,
		},
		onPaginationChange: setPagination,
		getCoreRowModel: getCoreRowModel(),
		manualPagination: true,
	});

	const dispatch = useDispatch();

	function updateAppPermissionsManagementData(value) {
		dispatch(setAppPermissionsManagementData(value));
	}

	const triggerApi = useApi();

	useEffect(() => {
		let { pageIndex, pageSize } = pagination;
		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/permissions/?page=${
					pageIndex + 1
				}&page_size=${pageSize}&include_dropdown_options=true`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				updateAppPermissionsManagementData(response);
			}
		};

		makeApiCall();
	}, [pagination]);

	return (
		<div className="flex grow flex-col overflow-auto">
			<div className="flex bg-[#F0F3F4]">
				<div className="flex grow items-center gap-[24px] py-[13px] pl-[24px] pr-[32px]">
					<div className="flex grow items-center gap-[8px]">
						<TableSearchIcon />
						<input
							data-cy="table_search_field"
							id="searchValue"
							name="searchValue"
							type="text"
							className="w-full bg-transparent font-lato text-sm leading-[20px] tracking-[0.2px] outline-0 ring-0 placeholder:text-[#6C747D]"
							placeholder="Search Users by name / ID / role(s)"
						/>
					</div>
					<SyncPermissions />
					{/* <TableFilterIcon />
					<TableColumnFilterIcon /> */}
				</div>
			</div>
			<div className="flex max-w-[calc(100vw_-_88px)] grow overflow-x-auto overflow-y-auto">
				<table className="h-fit w-full border-collapse">
					<thead className="sticky top-0 z-[2] bg-[#ffffff]">
						{table.getHeaderGroups().map((headerGroup) => (
							<tr key={headerGroup.id}>
								{headerGroup.headers.map((header) => (
									<th key={header.id} className="p-0 align-top">
										{header.isPlaceholder
											? null
											: flexRender(
													header.column.columnDef.header,
													header.getContext()
											  )}
									</th>
								))}
								<th key="extra-head" className="p-0 align-top">
									<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] py-[12px] px-[20px] text-start">
										<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]"></span>
									</div>
								</th>
								<th key="extra-head2" className="p-0 align-top">
									<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] py-[12px] px-[20px] text-start">
										<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]"></span>
									</div>
								</th>
							</tr>
						))}
					</thead>
					<tbody>
						{table.getRowModel().rows.map((row) => (
							<tr
								key={row.id}
								className="group relative hover:bg-[#f5f7f8] hover:shadow-table-row"
							>
								{row.getVisibleCells().map((cell) => (
									<td key={cell.id}>
										{flexRender(cell.column.columnDef.cell, cell.getContext())}
									</td>
								))}
								<td key="extra-cell" className="w-full">
									<div className="flex h-full flex-col border-b border-[#F0F3F4] py-[14px] px-[20px]">
										<span className="text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]"></span>
									</div>
								</td>
								<td
									key="extra-cell2"
									className="flex h-full w-[188px] flex-col border-b border-[#F0F3F4] py-[14px] px-[20px] group-hover:hidden"
								></td>

								<td className="from-0% to-90% sticky inset-y-0 right-0 z-[1] hidden h-full w-[188px] items-center justify-end border-b border-[#F0F3F4] bg-gradient-to-l from-[#F5F7F8] px-[32px]  group-hover:flex">
									<RowMenu rowData={row.original} />
								</td>
							</tr>
						))}
					</tbody>
				</table>
			</div>
			<div className="flex border-t border-[#DDE2E5] py-[4px]">
				<div className="flex grow items-center justify-between py-[7px] pl-[22px] pr-[24px]">
					<span className="font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#212429]">
						Total count:{' '}
						{appPermissionsManagementData?.permissions?.total_records}
					</span>
					<span className="font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#212429]">
						<PageCountSelectField
							key="page_count"
							label="Counts per page"
							name="page_count"
							id="page_count"
							placeholder="Select"
							value={table.getState().pagination.pageSize}
							optionsDataName="page_count"
							optionsData={[
								{ id: 10, label: 10 },
								{ id: 25, label: 25 },
								{ id: 50, label: 50 },
								{ id: 100, label: 100 },
							]}
							table={table}
						/>
					</span>
				</div>
				<span className="h-full w-[2px] min-w-[2px] bg-[#F0F3F4]"></span>
				<div className="flex w-fit items-center gap-[14px] px-[56px]">
					<button
						type="button"
						className="flex min-h-[24px] min-w-[24px] cursor-pointer items-center justify-center"
						onClick={() => table.previousPage()}
						disabled={!table.getCanPreviousPage()}
					>
						<TablePaginationPreviousIcon />
					</button>
					<div className="flex items-center gap-[8px]">
						<ResizableInput table={table} />
						<span className="font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#212429]">
							/{table.getPageCount()}
						</span>
					</div>
					<button
						type="button"
						className="flex min-h-[24px] min-w-[24px] cursor-pointer items-center justify-center"
						onClick={() => table.nextPage()}
						disabled={!table.getCanNextPage()}
					>
						<TablePaginationNextIcon />
					</button>
				</div>
			</div>
		</div>
	);
}
