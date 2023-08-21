import * as React from 'react';

import {
	createColumnHelper,
	flexRender,
	getCoreRowModel,
	useReactTable,
} from '@tanstack/react-table';

import { ReactComponent as TableSearchIcon } from '../../../../assets/images/svg/table-search-icon.svg';
import { ReactComponent as TableFilterIcon } from '../../../../assets/images/svg/table-filter-icon.svg';
import { ReactComponent as TableColumnFilterIcon } from '../../../../assets/images/svg/table-column-filter-icon.svg';
import { ReactComponent as TableRowKebabIcon } from '../../../../assets/images/svg/table-row-kebab-icon.svg';

export default function Table({ tableData }) {
	const columnHelper = createColumnHelper();

	const columns = [
		columnHelper.accessor((row) => row.user_name, {
			id: 'user_name',
			header: () => (
				<div className="flex items-start justify-start py-[12px] pl-[32px] pr-[20px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						User Name Active/inactive
					</span>
				</div>
			),
			cell: (info) => {
				return (
					<div className="flex h-full flex-col gap-[8px] border-b border-[#F0F3F4] py-[14px] pl-[32px] pr-[20px]">
						<span className="text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
							{info.getValue()}
						</span>
						<span className="w-fit min-w-[77px] rounded-[15px] bg-[#E4F9F2] px-[4px] py-[3px] text-center font-lato text-[12px] font-normal leading-[16px] tracking-[0.2px] text-[#1C1E27]">
							Inactive
						</span>
					</div>
				);
			},
		}),
		columnHelper.accessor((row) => row.user_id, {
			id: 'user_id',
			header: () => (
				<div className="flex items-start justify-start py-[12px] px-[20px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						User Id
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
		columnHelper.accessor((row) => row.mobile, {
			id: 'mobile',
			header: () => (
				<div className="flex items-start justify-start py-[12px] px-[20px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Mobile
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
		columnHelper.accessor((row) => row.email, {
			id: 'email',
			header: () => (
				<div className="flex items-start justify-start py-[12px] px-[20px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Email
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
		columnHelper.accessor((row) => row.role_access, {
			id: 'role_access',
			header: () => (
				<div className="flex items-start justify-start py-[12px] px-[20px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Role Access
					</span>
				</div>
			),
			cell: (info) => (
				<div className="flex h-full flex-col border-b border-[#F0F3F4] py-[14px] px-[20px]">
					<span className="min-w-max text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px] text-[#5048ED]">
						{info.getValue()}
					</span>
					<span className="min-w-max text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px] text-[#5048ED]">
						{info.getValue()}
					</span>
					<span className="min-w-max text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px] text-[#5048ED]">
						{info.getValue()}
					</span>
				</div>
			),
		}),
		columnHelper.accessor((row) => row.policy, {
			id: 'policy',
			header: () => (
				<div className="flex items-start justify-start py-[12px] px-[20px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Policy
					</span>
				</div>
			),
			cell: (info) => (
				<div className="flex h-full flex-col border-b border-[#F0F3F4] py-[14px] px-[20px]">
					<span className="min-w-max text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px] text-[#5048ED]">
						{info.getValue()}
					</span>
					<span className="min-w-max text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px] text-[#5048ED]">
						{info.getValue()}
					</span>
				</div>
			),
		}),
		columnHelper.accessor((row) => row.last_login_date_joined, {
			id: 'last_login_date_joined',
			header: () => (
				<div className="flex items-start justify-start py-[12px] px-[20px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Last Login / Date Joined
					</span>
				</div>
			),
			cell: (info) => (
				<div className="flex h-full flex-col gap-[4px] border-b border-[#F0F3F4] py-[14px] px-[20px]">
					<span className="w-fit min-w-max text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
						{info.getValue()}
					</span>
					<span className="w-fit min-w-max text-start font-lato text-[12px] font-normal leading-[16px] tracking-[0.2px] text-[#A3ABB1]">
						{info.getValue()}
					</span>
				</div>
			),
		}),
	];

	const [data, setData] = React.useState(() => [...tableData]);

	const table = useReactTable({
		data,
		columns,
		getCoreRowModel: getCoreRowModel(),
	});

	return (
		<div className="flex grow flex-col overflow-auto">
			<div className="flex bg-[#F0F3F4]">
				<div className="flex grow items-center gap-[24px] py-[13px] pl-[24px] pr-[32px]">
					<div className="flex grow items-center gap-[8px]">
						<TableSearchIcon />
						<input
							id="searchValue"
							name="searchValue"
							type="text"
							className="w-full bg-transparent font-lato text-sm leading-[20px] tracking-[0.2px] outline-0 ring-0 placeholder:text-[#6C747D]"
							placeholder="Search Users by name / ID / role(s)"
						/>
					</div>
					<TableFilterIcon />
					<TableColumnFilterIcon />
				</div>
			</div>
			<div className="flex max-w-[calc(100vw_-_88px)] grow overflow-x-auto overflow-y-auto">
				<table className="h-fit w-full">
					<thead className="sticky top-0 z-[2] border-b-[4px] border-[#F0F3F4] bg-[#ffffff] shadow-table-row">
						{table.getHeaderGroups().map((headerGroup) => (
							<tr key={headerGroup.id}>
								{headerGroup.headers.map((header) => (
									<th key={header.id} className="align-top">
										{header.isPlaceholder
											? null
											: flexRender(
													header.column.columnDef.header,
													header.getContext()
											  )}
									</th>
								))}

								<th key="extra-head" className="align-top">
									<div className="flex items-start justify-start py-[12px] px-[20px] text-start">
										<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]"></span>
									</div>
								</th>
								<th key="extra-head" className="align-top">
									<div className="flex items-start justify-start py-[12px] px-[20px] text-start">
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
								<div className="from-0% sticky inset-y-0 right-0 z-[0] hidden h-full items-center bg-gradient-to-l from-[#F5F7F8] px-[32px] group-hover:flex">
									<TableRowKebabIcon className="text-[#5048ED]" />
								</div>
							</tr>
						))}
					</tbody>
				</table>
			</div>
			<div className="flex border-t border-[#DDE2E5]">
				<div className="flex grow justify-between py-[17px] pl-[22px] pr-[24px]">
					<span className="font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#212429]">
						Total count: 56
					</span>
					<span className="font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#212429]">
						Counts per page
					</span>
				</div>
				<span className="h-[42px] min-h-[42px] w-[2px] min-w-[2px] bg-[#F0F3F4]"></span>
				<div className="flex w-fit py-[17px] px-[56px]">
					<span className="font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#212429]">
						Total count: 56
					</span>
				</div>
			</div>
		</div>
	);
}
