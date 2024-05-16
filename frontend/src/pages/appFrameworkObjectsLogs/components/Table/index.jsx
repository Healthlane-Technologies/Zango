import {
	createColumnHelper,
	flexRender,
	getCoreRowModel,
	useReactTable,
} from '@tanstack/react-table';
import debounce from 'just-debounce-it';
import { find, findIndex, set } from 'lodash';
import moment from 'moment';
import * as React from 'react';
import { useEffect, useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import { ReactComponent as TablePaginationNextIcon } from '../../../../assets/images/svg/table-pagination-next-icon.svg';
import { ReactComponent as TablePaginationPreviousIcon } from '../../../../assets/images/svg/table-pagination-previous-icon.svg';
import { ReactComponent as TableSearchIcon } from '../../../../assets/images/svg/table-search-icon.svg';
import HeaderInfo from '../../../../components/Table/HeaderInfo';
import ListGeneralCell from '../../../../components/Table/ListGeneralCell';
import PageCountSelectField from '../../../../components/Table/PageCountSelectField';
import ResizableInput from '../../../../components/Table/ResizableInput';
import TableDateRangeFilter from '../../../../components/Table/TableDateRangeFilter';
import TableDropdownFilter from '../../../../components/Table/TableDropdownFilter';
import useApi from '../../../../hooks/useApi';
import {
	selectAppFrameworkObjectsLogsData,
	selectAppFrameworkObjectsLogsTableData,
	setAppFrameworkObjectsLogsData,
	setAppFrameworkObjectsLogsTableData,
} from '../../slice';

export default function Table({ tableData }) {
	let { appId } = useParams();
	const searchRef = React.useRef(null);
	const appFrameworkObjectsLogsTableData = useSelector(
		selectAppFrameworkObjectsLogsTableData
	);
	const platformAuditLogsData = useSelector(selectAppFrameworkObjectsLogsData);

	const columnHelper = createColumnHelper();

	const handleSearch = (value) => {
		let searchData = {
			...appFrameworkObjectsLogsTableData,
			searchValue: value,
			pageIndex: 0,
		};
		debounceSearch(searchData);
	};

	const handleColumnSearch = (data) => {
		let tempTableData = JSON.parse(
			JSON.stringify(appFrameworkObjectsLogsTableData)
		);
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
		columnHelper.accessor((row) => row.object_type, {
			id: 'object_type',
			header: () => (
				<div className="flex h-full items-start justify-start gap-[16px] border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="whitespace-nowrap font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Object Type
					</span>
					<div className="translate-y-[-2px]">
						<TableDropdownFilter
							key="object_type"
							label="Stockist"
							name="object_type"
							id="object_type"
							placeholder="Select"
							value={
								find(appFrameworkObjectsLogsTableData?.columns, {
									id: 'object_type',
								})?.value
									? find(appFrameworkObjectsLogsTableData?.columns, {
											id: 'object_type',
									  })?.value
									: ''
							}
							optionsDataName="object_type"
							optionsData={platformAuditLogsData?.dropdown_options?.object_type}
							onChange={(value) => {
								handleColumnSearch({
									id: 'object_type',
									value: value?.id,
								});
							}}
						/>
					</div>
				</div>
			),
			cell: (info) => (
				<div className="flex h-full min-w-max flex-col border-b border-[#F0F3F4] px-[20px] py-[14px]">
					<span className="text-start font-lato text-[14px] font-normal capitalize leading-[20px] tracking-[0.2px]">
						{info.getValue()}
					</span>
				</div>
			),
		}),
		columnHelper.accessor((row) => row.object_id, {
			id: 'object_id',
			header: () => (
				<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="whitespace-nowrap font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Object Id
					</span>
				</div>
			),
			cell: (info) => (
				<div className="flex h-full min-w-max flex-col border-b border-[#F0F3F4] px-[20px] py-[14px]">
					<span className="text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
						{info.getValue() ? info.getValue() : '-'}
					</span>
				</div>
			),
		}),
		columnHelper.accessor((row) => row.timestamp, {
			id: 'timestamp',
			header: () => (
				<div className="flex h-full items-start justify-start gap-[16px] border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="whitespace-nowrap font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						DATE AND TIME
					</span>
					<div className="">
						<TableDateRangeFilter
							key="timestamp"
							label="Stockist"
							name="timestamp"
							id="timestamp"
							placeholder="Select"
							value={
								find(appFrameworkObjectsLogsTableData?.columns, {
									id: 'timestamp',
								})?.value
									? find(appFrameworkObjectsLogsTableData?.columns, {
											id: 'timestamp',
									  })?.value
									: ''
							}
							optionsDataName="timestamp"
							optionsData={platformAuditLogsData?.dropdown_options?.timestamp}
							onChange={(value) => {
								handleColumnSearch({
									id: 'timestamp',
									value: value,
								});
							}}
						/>
					</div>
				</div>
			),
			cell: (info) => {
				return (
					<div className="flex h-full flex-col gap-[8px] border-b border-[#F0F3F4] px-[20px] py-[14px]">
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
				<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] py-[12px] pl-[32px] pr-[20px] text-start">
					<span className="whitespace-nowrap font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Log Id
					</span>
				</div>
			),
			cell: (info) => (
				<div className="flex h-full flex-col border-b border-[#F0F3F4] py-[14px] pl-[32px] pr-[20px]">
					<span className="text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
						{info.getValue()}
					</span>
				</div>
			),
		}),

		// columnHelper.accessor((row) => row.object, {
		// 	id: 'object',
		// 	header: () => (
		// 		<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] py-[12px] px-[20px] text-start">
		// 			<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
		// 				Object
		// 			</span>
		// 		</div>
		// 	),
		// 	cell: (info) => (
		// 		<div className="flex h-full flex-col border-b border-[#F0F3F4] py-[14px] px-[20px]">
		// 			<span className="text-pretty text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
		// 				{info.getValue()}
		// 			</span>
		// 		</div>
		// 	),
		// }),

		columnHelper.accessor((row) => row.actor, {
			id: 'actor',
			header: () => (
				<div className="flex h-full items-start justify-start gap-[10px] whitespace-nowrap border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Actor
					</span>
					<HeaderInfo message={'* Denotes Platform User'} />
				</div>
			),
			cell: (info) => (
				<div className="flex h-full flex-col border-b border-[#F0F3F4] px-[20px] py-[14px]">
					<span className="whitespace-nowrap text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
						{info.getValue()
							? info.row.original?.actor_type === 'platform_actor'
								? `${info.getValue()} *`
								: info.getValue()
							: '-'}
					</span>
				</div>
			),
		}),
		columnHelper.accessor((row) => row.changes, {
			id: 'changes',
			header: () => (
				<div className="flex h-full items-start justify-start gap-[10px] whitespace-nowrap border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="min-w-max font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						CHANGES
					</span>
					<HeaderInfo
						message={'Date & Time values displayed here are in UTC Timezone'}
					/>
				</div>
			),
			cell: (info) => (
				<ListGeneralCell data={info.getValue()} info={info} />
				// <div className="flex h-full flex-col border-b border-[#F0F3F4] py-[14px] px-[20px]">
				// 	{/* <span className="text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
				// 		{JSON.stringify(info.getValue())}
				// 	</span> */}
				// 	<table class="table-auto">
				// 		<thead>
				// 			<tr>
				// 				<th></th>
				// 				<th></th>
				// 			</tr>
				// 		</thead>
				// 		<tbody>
				// 			{Object.entries(info.getValue()).map((eachChange) => {
				// 				if (!Array.isArray(eachChange[1])) {
				// 					return (
				// 						<>
				// 							<tr>
				// 								<td className="pr-[24px]">
				// 									<span className="whitespace-nowrap text-start font-lato text-[14px] font-normal capitalize leading-[20px] tracking-[0.2px]">
				// 										field
				// 									</span>
				// 								</td>
				// 								<td className="pr-[10px]">
				// 									<span className="flex gap-[10px] text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
				// 										:{''}
				// 										<span>{eachChange[0].split('_').join(' ')}</span>
				// 									</span>
				// 								</td>
				// 							</tr>
				// 							<tr>
				// 								<td className="pr-[24px]">
				// 									<span className="whitespace-nowrap text-start font-lato text-[14px] font-normal capitalize leading-[20px] tracking-[0.2px]">
				// 										type
				// 									</span>
				// 								</td>
				// 								<td className="pr-[10px]">
				// 									<span className="flex gap-[10px] text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
				// 										:{''}
				// 										<span>{eachChange[1]?.type}</span>
				// 									</span>
				// 								</td>
				// 							</tr>
				// 							<tr>
				// 								<td className="pr-[24px]">
				// 									<span className="whitespace-nowrap text-start font-lato text-[14px] font-normal capitalize leading-[20px] tracking-[0.2px]">
				// 										objects
				// 									</span>
				// 								</td>
				// 								<td className="pr-[10px]">
				// 									<span className="flex gap-[10px] whitespace-nowrap text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
				// 										:{''}
				// 										<span>{eachChange[1]?.objects.join(', ')}</span>
				// 									</span>
				// 								</td>
				// 							</tr>
				// 							<tr>
				// 								<td className="pr-[24px]">
				// 									<span className="whitespace-nowrap text-start font-lato text-[14px] font-normal capitalize leading-[20px] tracking-[0.2px]">
				// 										operation
				// 									</span>
				// 								</td>
				// 								<td className="pr-[10px]">
				// 									<span className="flex gap-[10px] text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
				// 										:{''}
				// 										<span>{eachChange[1]?.operation}</span>
				// 									</span>
				// 								</td>
				// 							</tr>
				// 						</>
				// 					);
				// 				}

				// 				return (
				// 					<tr>
				// 						<td className="pr-[24px] align-top">
				// 							<span className="whitespace-nowrap text-start font-lato text-[14px] font-normal capitalize leading-[20px] tracking-[0.2px]">
				// 								{eachChange[0].split('_').join(' ')}
				// 							</span>
				// 						</td>
				// 						<td className="pr-[10px] align-top">
				// 							<span className="flex gap-[10px] text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
				// 								:{''}
				// 								{eachChange[1].map(
				// 									(changesValue, index, arrayContext) => {
				// 										if (
				// 											index === 0 &&
				// 											info.row.original?.action === 'Create'
				// 										) {
				// 											return <></>;
				// 										}
				// 										return (
				// 											<span
				// 												className={`text-balance text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px] ${
				// 													arrayContext?.length - 1 !== index
				// 														? 'whitespace-nowrap text-[#A3ABB1]'
				// 														: ''
				// 												}`}
				// 											>
				// 												{!changesValue ? '<empty>' : changesValue}
				// 												{arrayContext?.length - 1 !== index
				// 													? ' ->'
				// 													: ''}
				// 											</span>
				// 										);
				// 									}
				// 								)}
				// 							</span>
				// 						</td>
				// 					</tr>
				// 				);
				// 			})}
				// 		</tbody>
				// 	</table>
				// </div>
			),
		}),
		// columnHelper.accessor((row) => row.policies, {
		// 	id: 'policies',
		// 	header: () => (
		// 		<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] py-[12px] px-[20px] text-start">
		// 			<span className="min-w-max font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
		// 				Policy
		// 			</span>
		// 		</div>
		// 	),
		// 	cell: (info) => <ListCell data={info.getValue()} />,
		// }),
		columnHelper.accessor((row) => row.action, {
			id: 'action',
			header: () => (
				<div className="flex h-full items-start justify-start gap-[16px] border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Action
					</span>
					<div className="translate-y-[-2px]">
						<TableDropdownFilter
							key="action"
							label="Stockist"
							name="action"
							id="action"
							placeholder="Select"
							value={
								find(appFrameworkObjectsLogsTableData?.columns, {
									id: 'action',
								})?.value
									? find(appFrameworkObjectsLogsTableData?.columns, {
											id: 'action',
									  })?.value
									: ''
							}
							optionsDataName="action"
							optionsData={platformAuditLogsData?.dropdown_options?.action}
							onChange={(value) => {
								handleColumnSearch({
									id: 'action',
									value: value?.id,
								});
							}}
						/>
					</div>
				</div>
			),
			cell: (info) => (
				<div className="flex h-full flex-col gap-[4px] border-b border-[#F0F3F4] px-[20px] py-[14px]">
					<span className="w-fit min-w-max text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
						{info.getValue()}
					</span>
				</div>
			),
		}),
	];

	const defaultData = useMemo(() => [], []);

	const pagination = useMemo(
		() => ({
			pageIndex: appFrameworkObjectsLogsTableData?.pageIndex,
			pageSize: appFrameworkObjectsLogsTableData?.pageSize,
		}),
		[appFrameworkObjectsLogsTableData]
	);

	const table = useReactTable({
		data: platformAuditLogsData.audit_logs?.records ?? defaultData,
		columns,
		pageCount: platformAuditLogsData.audit_logs?.total_pages ?? -1,
		state: {
			pagination,
		},
		onPaginationChange: (updater) => {
			if (typeof updater !== 'function') return;

			const newPageInfo = updater(table.getState().pagination);

			dispatch(
				setAppFrameworkObjectsLogsTableData({
					...appFrameworkObjectsLogsTableData,
					...newPageInfo,
				})
			);
		},
		getCoreRowModel: getCoreRowModel(),
		manualPagination: true,
	});

	const dispatch = useDispatch();

	function updateAppFrameworkObjectsLogsData(value) {
		dispatch(setAppFrameworkObjectsLogsData(value));
	}

	const triggerApi = useApi();

	const debounceSearch = debounce((data) => {
		dispatch(setAppFrameworkObjectsLogsTableData(data));
	}, 500);

	useEffect(() => {
		let { pageIndex, pageSize } = pagination;

		let columnFilter = appFrameworkObjectsLogsTableData?.columns
			? appFrameworkObjectsLogsTableData?.columns
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
				url: `/api/v1/apps/${appId}/auditlog/?page=${
					pageIndex + 1
				}&page_size=${pageSize}&model_type=core_models&include_dropdown_options=true&search=${
					appFrameworkObjectsLogsTableData?.searchValue
				}${columnFilter?.length ? columnFilter : ''}`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				updateAppFrameworkObjectsLogsData(response);
			}
		};

		makeApiCall();
	}, [appFrameworkObjectsLogsTableData]);

	useEffect(() => {
		searchRef.current.value =
			appFrameworkObjectsLogsTableData?.searchValue || '';
	}, []);

	return (
		<div className="flex max-w-[calc(100vw_-_88px)] grow flex-col overflow-auto">
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
							placeholder="Search Audit Logs by Object ID / Log ID / actor / changes"
							onChange={(e) => handleSearch(e.target.value)}
						/>
					</div>
					{/* <TableFilterIcon />
					<TableColumnFilterIcon /> */}
				</div>
			</div>
			<div className="relative flex grow overflow-x-auto overflow-y-auto">
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
						Total count: {platformAuditLogsData?.audit_logs?.total_records}
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
