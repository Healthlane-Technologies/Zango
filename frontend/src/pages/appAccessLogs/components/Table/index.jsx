import {
	createColumnHelper,
	flexRender,
	getCoreRowModel,
	useReactTable,
} from '@tanstack/react-table';
import debounce from 'just-debounce-it';
import { find, findIndex, set } from 'lodash';
import * as React from 'react';
import { useEffect, useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import { ReactComponent as TablePaginationNextIcon } from '../../../../assets/images/svg/table-pagination-next-icon.svg';
import { ReactComponent as TablePaginationPreviousIcon } from '../../../../assets/images/svg/table-pagination-previous-icon.svg';
import { ReactComponent as TableSearchIcon } from '../../../../assets/images/svg/table-search-icon.svg';
import PageCountSelectField from '../../../../components/Table/PageCountSelectField';
import ResizableInput from '../../../../components/Table/ResizableInput';
import TableDateRangeFilter from '../../../../components/Table/TableDateRangeFilter';
import TableDropdownFilter from '../../../../components/Table/TableDropdownFilter';
import useApi from '../../../../hooks/useApi';
import {
	selectAppAccessLogsData,
	selectAppAccessLogsTableData,
	setAppAccessLogsData,
	setAppAccessLogsTableData,
} from '../../slice';

export default function Table({ tableData }) {
	let { appId } = useParams();
	const searchRef = React.useRef(null);
	const appAccessLogsTableData = useSelector(selectAppAccessLogsTableData);

	const columnHelper = createColumnHelper();

	const handleSearch = (value) => {
		let searchData = {
			...appAccessLogsTableData,
			searchValue: value,
			pageIndex: 0,
		};
		debounceSearch(searchData);
	};

	const handleColumnSearch = (data) => {
		let tempTableData = JSON.parse(JSON.stringify(appAccessLogsTableData));
		let index = findIndex(tempTableData?.columns, { id: data?.id });

		if (index !== -1) {
			set(tempTableData?.columns[index], 'value', data?.value);
		} else {
			tempTableData?.columns.push({
				id: data?.id,
				value: data?.value,
			});
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
				<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] py-[12px] pl-[32px] pr-[20px] text-start">
					<span className="min-w-max font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Id
					</span>
				</div>
			),
			cell: (info) => {
				return (
					<div className="flex h-full flex-col gap-[8px] border-b border-[#F0F3F4] py-[14px] pl-[32px] pr-[20px]">
						<span className="text-start font-lato text-[14px] font-normal capitalize leading-[20px] tracking-[0.2px]">
							{info.getValue()}
						</span>
					</div>
				);
			},
		}),
		columnHelper.accessor((row) => row.user, {
			id: 'user',
			header: () => (
				<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="min-w-max font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						User
					</span>
				</div>
			),
			cell: (info) => (
				<div className="flex h-full flex-col border-b border-[#F0F3F4] px-[20px] py-[14px]">
					<span className="whitespace-nowrap text-start font-lato text-[14px] font-normal capitalize leading-[20px] tracking-[0.2px]">
						{info.getValue()}
					</span>
				</div>
			),
		}),
		columnHelper.accessor((row) => row.username, {
			id: 'username',
			header: () => (
				<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="min-w-max font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Username
					</span>
				</div>
			),
			cell: (info) => (
				<div className="flex h-full flex-col border-b border-[#F0F3F4] px-[20px] py-[14px]">
					<span className="whitespace-nowrap text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
						{info.getValue()}
					</span>
				</div>
			),
		}),
		columnHelper.accessor((row) => row.ip_address, {
			id: 'ip_address',
			header: () => (
				<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="min-w-max font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Ip Address
					</span>
				</div>
			),
			cell: (info) => (
				<div className="flex h-full flex-col border-b border-[#F0F3F4] px-[20px] py-[14px]">
					<span className="text-start font-lato text-[14px] font-normal capitalize leading-[20px] tracking-[0.2px]">
						{info.getValue()}
					</span>
				</div>
			),
		}),
		columnHelper.accessor((row) => row.attempt_type, {
			id: 'attempt_type',
			header: () => (
				<div className="flex h-full items-start justify-start gap-[16px] border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Attempt Type
					</span>
					<div className="translate-y-[-2px]">
						<TableDropdownFilter
							key="attempt_type"
							label="Attempt Type"
							name="attempt_type"
							id="attempt_type"
							placeholder="Select"
							value={
								find(appAccessLogsTableData?.columns, {
									id: 'attempt_type',
								})?.value
									? find(appAccessLogsTableData?.columns, {
											id: 'attempt_type',
									  })?.value
									: ''
							}
							optionsDataName="attempt_type"
							optionsData={
								appAccessLogsData?.dropdown_options?.attempt_type
									? appAccessLogsData?.dropdown_options?.attempt_type
									: []
							}
							onChange={(value) => {
								handleColumnSearch({
									id: 'attempt_type',
									value: value?.id,
								});
							}}
						/>
					</div>
				</div>
			),
			cell: (info) => (
				<div className="flex h-full flex-col border-b border-[#F0F3F4] px-[20px] py-[14px]">
					<span className="text-start font-lato text-[14px] font-normal capitalize leading-[20px] tracking-[0.2px]">
						{info.getValue()}
					</span>
				</div>
			),
		}),
		columnHelper.accessor((row) => row.attempt_time, {
			id: 'attempt_time',
			header: () => (
				<div className="flex h-full items-start justify-start gap-[16px] border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="whitespace-nowrap font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Attempt Time
					</span>
					<div className="">
						<TableDateRangeFilter
							key="attempt_time"
							label="Stockist"
							name="attempt_time"
							id="attempt_time"
							placeholder="Select"
							value={
								find(appAccessLogsTableData?.columns, {
									id: 'attempt_time',
								})?.value
									? find(appAccessLogsTableData?.columns, {
											id: 'attempt_time',
									  })?.value
									: ''
							}
							optionsDataName="attempt_time"
							optionsData={appAccessLogsData?.dropdown_options?.attempt_time}
							onChange={(value) => {
								handleColumnSearch({
									id: 'attempt_time',
									value: value,
								});
							}}
						/>
					</div>
				</div>
			),
			cell: (info) => (
				<div className="flex h-full flex-col border-b border-[#F0F3F4] px-[20px] py-[14px]">
					<span className="whitespace-nowrap text-start font-lato text-[14px] font-normal capitalize leading-[20px] tracking-[0.2px]">
						{info.getValue()}
					</span>
				</div>
			),
		}),
		columnHelper.accessor((row) => row.role, {
			id: 'role',
			header: () => (
				<div className="flex h-full items-start justify-start gap-[16px] border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Role
					</span>
					<div className="translate-y-[-2px]">
						<TableDropdownFilter
							key="role"
							label="Role"
							name="role"
							id="role"
							placeholder="Select"
							value={
								find(appAccessLogsTableData?.columns, {
									id: 'role',
								})?.value
									? find(appAccessLogsTableData?.columns, {
											id: 'role',
									  })?.value
									: ''
							}
							optionsDataName="role"
							optionsData={
								appAccessLogsData?.dropdown_options?.role
									? appAccessLogsData?.dropdown_options?.role
									: []
							}
							onChange={(value) => {
								handleColumnSearch({
									id: 'role',
									value: value?.id,
								});
							}}
						/>
					</div>
				</div>
			),
			cell: (info) => (
				<div className="flex h-full flex-col border-b border-[#F0F3F4] px-[20px] py-[14px]">
					<span className="text-start font-lato text-[14px] font-normal capitalize leading-[20px] tracking-[0.2px]">
						{info.getValue()}
					</span>
				</div>
			),
		}),
		columnHelper.accessor((row) => row.user_agent, {
			id: 'user_agent',
			header: () => (
				<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="min-w-max font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						user agent
					</span>
				</div>
			),
			cell: (info) => (
				<div className="flex h-full flex-col border-b border-[#F0F3F4] px-[20px] py-[14px]">
					<span className="whitespace-nowrap text-start font-lato text-[14px] font-normal capitalize leading-[20px] tracking-[0.2px]">
						{info.getValue()}
					</span>
				</div>
			),
		}),
		columnHelper.accessor((row) => row.session_expired_at, {
			id: 'session_expired_at',
			header: () => (
				<div className="flex h-full items-start justify-start gap-[16px] border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="whitespace-nowrap font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Session Expired At
					</span>
					<div className="">
						<TableDateRangeFilter
							key="session_expired_at"
							label="Session Expired At"
							name="session_expired_at"
							id="session_expired_at"
							placeholder="Select"
							value={
								find(appAccessLogsTableData?.columns, {
									id: 'session_expired_at',
								})?.value
									? find(appAccessLogsTableData?.columns, {
											id: 'session_expired_at',
									  })?.value
									: ''
							}
							optionsDataName="session_expired_at"
							optionsData={
								appAccessLogsData?.dropdown_options?.session_expired_at
							}
							onChange={(value) => {
								handleColumnSearch({
									id: 'session_expired_at',
									value: value,
								});
							}}
						/>
					</div>
				</div>
			),
			cell: (info) => (
				<div className="flex h-full flex-col border-b border-[#F0F3F4] px-[20px] py-[14px]">
					<span className="whitespace-nowrap text-start font-lato text-[14px] font-normal capitalize leading-[20px] tracking-[0.2px]">
						{info.getValue()}
					</span>
				</div>
			),
		}),
		columnHelper.accessor((row) => row.is_login_successful, {
			id: 'is_login_successful',
			header: () => (
				<div className="flex h-full items-start justify-start gap-[16px] border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Login Attempt
					</span>
					<div className="translate-y-[-2px]">
						<TableDropdownFilter
							key="is_login_successful"
							label="Is Login Successful"
							name="is_login_successful"
							id="is_login_successful"
							placeholder="Select"
							value={
								find(appAccessLogsTableData?.columns, {
									id: 'is_login_successful',
								})?.value
									? find(appAccessLogsTableData?.columns, {
											id: 'is_login_successful',
									  })?.value
									: ''
							}
							optionsDataName="is_login_successful"
							optionsData={
								appAccessLogsData?.dropdown_options?.is_login_successful
									? appAccessLogsData?.dropdown_options?.is_login_successful
									: []
							}
							onChange={(value) => {
								handleColumnSearch({
									id: 'is_login_successful',
									value: value?.id,
								});
							}}
						/>
					</div>
				</div>
			),
			cell: (info) => (
				<div className="flex h-full flex-col border-b border-[#F0F3F4] px-[20px] py-[14px]">
					<span
						className={`w-fit min-w-[77px] rounded-[15px]  px-[4px] py-[3px] text-center font-lato text-[12px] font-normal capitalize leading-[16px] tracking-[0.2px] text-[#1C1E27] ${
							info.getValue() ? 'bg-[#E4F9F2]' : 'bg-[#FBE0DD]'
						}`}
					>
						{info.getValue() ? 'Successful' : 'Failed'}
					</span>
				</div>
			),
		}),
	];

	const defaultData = useMemo(() => [], []);

	const pagination = useMemo(
		() => ({
			pageIndex: appAccessLogsTableData?.pageIndex,
			pageSize: appAccessLogsTableData?.pageSize,
		}),
		[appAccessLogsTableData]
	);

	const appAccessLogsData = useSelector(selectAppAccessLogsData);

	const table = useReactTable({
		data: appAccessLogsData?.access_logs?.records ?? defaultData,
		columns,
		pageCount: appAccessLogsData?.access_logs?.total_pages ?? -1,
		state: {
			pagination,
		},
		onPaginationChange: (updater) => {
			if (typeof updater !== 'function') return;

			const newPageInfo = updater(table.getState().pagination);

			dispatch(
				setAppAccessLogsTableData({
					...appAccessLogsTableData,
					...newPageInfo,
				})
			);
		},

		getCoreRowModel: getCoreRowModel(),
		manualPagination: true,
	});

	const dispatch = useDispatch();

	function updateAppAccessLogsData(value) {
		dispatch(setAppAccessLogsData(value));
	}

	const triggerApi = useApi();

	const debounceSearch = debounce((data) => {
		dispatch(setAppAccessLogsTableData(data));
	}, 500);

	useEffect(() => {
		let { pageIndex, pageSize } = pagination;

		let columnFilter = appAccessLogsTableData?.columns
			? appAccessLogsTableData?.columns
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
							if (value !== undefined) {
								return `&search_${id}=${value}`;
							} else {
								return ``;
							}
						}
					})
					.join('')
			: '';

		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/access-logs/?page=${
					pageIndex + 1
				}&page_size=${pageSize}&include_dropdown_options=true&search=${
					appAccessLogsTableData?.searchValue
				}${columnFilter?.length ? columnFilter : ''}`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				updateAppAccessLogsData(response);
			}
		};

		makeApiCall();
	}, [appAccessLogsTableData]);

	useEffect(() => {
		searchRef.current.value = appAccessLogsTableData?.searchValue || '';
	}, []);

	return (
		<div className="flex grow flex-col overflow-auto">
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
							placeholder="Search Access Logs by ID / User / IP Address / User Agent"
							onChange={(e) => handleSearch(e.target.value)}
						/>
					</div>
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
									<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
										<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]"></span>
									</div>
								</th>
								<th key="extra-head2" className="p-0 align-top">
									<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
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
									<div className="flex h-full flex-col border-b border-[#F0F3F4] px-[20px] py-[14px]">
										<span className="text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]"></span>
									</div>
								</td>
								<td
									key="extra-cell2"
									className="flex h-full w-[188px] flex-col border-b border-[#F0F3F4] px-[20px] py-[14px] group-hover:hidden"
								></td>
								<td className="sticky inset-y-0 right-0 z-[1] hidden h-full w-[188px] items-center justify-end border-b border-[#F0F3F4] bg-gradient-to-l from-[#F5F7F8] from-0% to-90% px-[32px]  group-hover:flex"></td>
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
						Total count: {appAccessLogsData?.access_logs?.total_records}
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
