import {
	createColumnHelper,
	flexRender,
	getCoreRowModel,
	useReactTable,
} from '@tanstack/react-table';
import debounce from 'just-debounce-it';
import { find, findIndex, set } from 'lodash';
import * as React from 'react';
import { useEffect, useMemo, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import { ReactComponent as TablePaginationNextIcon } from '../../../../assets/images/svg/table-pagination-next-icon.svg';
import { ReactComponent as TablePaginationPreviousIcon } from '../../../../assets/images/svg/table-pagination-previous-icon.svg';
import { ReactComponent as TableSearchIcon } from '../../../../assets/images/svg/table-search-icon.svg';
import ListCell from '../../../../components/Table/ListCell';
import TableDropdownFilter from '../../../../components/Table/TableDropdownFilter';
import useApi from '../../../../hooks/useApi';
import {
	selectAppTaskManagementData,
	selectAppTaskManagementTableData,
	setAppTaskManagementData,
	setAppTaskManagementTableData,
} from '../../slice';
import SyncTask from '../SyncTask';
import PageCountSelectField from './PageCountSelectField';
import ResizableInput from './ResizableInput';
import RowMenu from './RowMenu';

export default function Table({ tableData }) {
	let { appId } = useParams();
	const searchRef = React.useRef(null);
	const appTaskManagementTableData = useSelector(
		selectAppTaskManagementTableData
	);

	const columnHelper = createColumnHelper();

	const handleSearch = (value) => {
		let searchData = {
			...appTaskManagementTableData,
			searchValue: value,
			pageIndex: 0,
		};
		debounceSearch(searchData);
	};

	const handleColumnSearch = (data) => {
		let tempTableData = JSON.parse(JSON.stringify(appTaskManagementTableData));
		let index = findIndex(tempTableData?.columns, { id: data?.id });

		if (index !== -1) {
			set(tempTableData?.columns[index], 'value', data?.value);
		} else {
			tempTableData?.columns.push({ id: data?.id, value: data?.value });
		}

		let searchData = {
			...tempTableData,
			pageIndex: 0,
		};

		debounceSearch(searchData);
	};

	const columns = [
		columnHelper.accessor((row) => row.id, {
			id: 'id',
			header: () => (
				<div className="flex h-full min-w-max items-start justify-start border-b-[4px] border-[#F0F3F4] py-[12px] pl-[32px] pr-[20px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Task Id
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
		columnHelper.accessor((row) => row.name, {
			id: 'name',
			header: () => (
				<div className="flex h-full min-w-max items-start justify-start border-b-[4px] border-[#F0F3F4] py-[12px] px-[20px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Task Name
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
		columnHelper.accessor((row) => row.attached_policies, {
			id: 'attached_policies',
			header: () => (
				<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] py-[12px] px-[20px] text-start">
					<span className="min-w-max font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Policy
					</span>
				</div>
			),
			cell: (info) => <ListCell data={info.getValue()} />,
		}),
		columnHelper.accessor((row) => row.schedule, {
			id: 'schedule',
			header: () => (
				<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] py-[12px] px-[20px] text-start">
					<span className="min-w-max font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Schedule (UTC)
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
		columnHelper.accessor((row) => row.is_enabled, {
			id: 'is_enabled',
			header: () => (
				<div className="flex h-full items-start justify-start gap-[16px] border-b-[4px] border-[#F0F3F4] py-[12px] px-[20px] text-start">
					<span className="min-w-max font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Status
					</span>
					<div className="translate-y-[-2px]">
						<TableDropdownFilter
							key="is_enabled"
							label="Status"
							name="is_enabled"
							id="is_enabled"
							placeholder="Select"
							value={
								find(appTaskManagementTableData?.columns, { id: 'is_enabled' })
									?.value
									? find(appTaskManagementTableData?.columns, {
											id: 'is_enabled',
									  })?.value
									: ''
							}
							optionsDataName="is_enabled"
							optionsData={[
								{ id: '', label: '-select-' },
								{ id: 'true', label: 'Scheduled' },
								{ id: 'false', label: 'Disabled' },
							]}
							onChange={(value) => {
								handleColumnSearch({
									id: 'is_enabled',
									value: value?.id,
								});
							}}
						/>
					</div>
				</div>
			),
			cell: (info) => (
				<div className="flex h-full flex-col border-b border-[#F0F3F4] py-[14px] px-[20px]">
					<span
						className={`w-fit min-w-[77px] rounded-[15px] px-[4px] py-[3px] text-center font-lato text-[12px] font-normal capitalize leading-[16px] tracking-[0.2px] text-[#1C1E27] ${
							info.getValue() ? 'bg-[#E4F9F2]' : 'bg-[#FBE0DD]'
						}`}
					>
						{info.getValue() ? 'Scheduled' : 'Disabled'}
					</span>
				</div>
			),
		}),
	];

	const defaultData = useMemo(() => [], []);

	const pagination = useMemo(
		() => ({
			pageIndex: appTaskManagementTableData?.pageIndex,
			pageSize: appTaskManagementTableData?.pageSize,
		}),
		[appTaskManagementTableData]
	);

	const appTaskManagementData = useSelector(selectAppTaskManagementData);

	const table = useReactTable({
		data: appTaskManagementData.tasks?.records ?? defaultData,
		columns,
		pageCount: appTaskManagementData.tasks?.total_pages ?? -1,
		state: {
			pagination,
		},
		onPaginationChange: (updater) => {
			if (typeof updater !== 'function') return;

			const newPageInfo = updater(table.getState().pagination);

			dispatch(
				setAppTaskManagementTableData({
					...appTaskManagementTableData,
					...newPageInfo,
				})
			);
		},
		getCoreRowModel: getCoreRowModel(),
		manualPagination: true,
	});

	const dispatch = useDispatch();

	function updateAppTaskManagementData(value) {
		dispatch(setAppTaskManagementData(value));
	}

	const triggerApi = useApi();

	const debounceSearch = debounce((data) => {
		dispatch(setAppTaskManagementTableData(data));
	}, 500);

	useEffect(() => {
		let { pageIndex, pageSize } = pagination;

		let columnFilter = appTaskManagementTableData?.columns
			? appTaskManagementTableData?.columns
					?.map(({ id, value }) => {
						return `&search_${id}=${value}`;
					})
					.join('')
			: '';

		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/tasks/?page=${
					pageIndex + 1
				}&page_size=${pageSize}&include_dropdown_options=true&search=${
					appTaskManagementTableData?.searchValue
				}${columnFilter?.length ? columnFilter : ''}`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				updateAppTaskManagementData(response);
			}
		};

		makeApiCall();
	}, [appTaskManagementTableData]);

	useEffect(() => {
		searchRef.current.value = appTaskManagementTableData?.searchValue || '';
	}, []);

	return (
		<div className="flex max-w-[100vw] grow flex-col overflow-auto">
			<div className="flex bg-[#F0F3F4]">
				<div className="flex grow items-center gap-[24px] py-[13px] pl-[24px] pr-[32px]">
					<div className="flex grow items-center gap-[8px]">
						<TableSearchIcon />
						<input
							ref={searchRef}
							id="searchValue"
							name="searchValue"
							type="text"
							className="w-full bg-transparent font-lato text-sm leading-[20px] tracking-[0.2px] outline-0 ring-0 placeholder:text-[#6C747D]"
							placeholder="Search Tasks by name / ID / policy(s)"
							onChange={(e) => handleSearch(e.target.value)}
						/>
					</div>
					<SyncTask />
					{/* <TableFilterIcon />
					<TableColumnFilterIcon /> */}
				</div>
			</div>
			<div className="relative flex max-w-[calc(100vw_-_88px)] grow overflow-x-auto overflow-y-auto">
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
				{table.getRowModel().rows?.length ? null : (
					<div className="absolute inset-0 flex items-center justify-center">
						<span className="text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
							No data
						</span>
					</div>
				)}
			</div>
			<div className="flex border-t border-[#DDE2E5] py-[4px]">
				<div className="flex grow items-center justify-between py-[7px] pl-[22px] pr-[24px]">
					<span className="font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#212429]">
						Total count: {appTaskManagementData?.tasks?.total_records}
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
