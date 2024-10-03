import { createColumnHelper } from '@tanstack/react-table';
import { find } from 'lodash';
import moment from 'moment';
import HeaderInfo from '../../../../components/Table/HeaderInfo';

import ListGeneralCell from '../../../../components/Table/ListGeneralCell';
import TableDateRangeFilter from '../../../../components/Table/TableDateRangeFilter';
import TableDropdownFilter from '../../../../components/Table/TableDropdownFilter';
import { handleColumnSearch } from '../../../../utils/table';

function columns({ debounceSearch, localTableData, tableData }) {
	const columnHelper = createColumnHelper();

	const columnsData = [
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
								find(localTableData?.columns, {
									id: 'object_type',
								})?.value
									? find(localTableData?.columns, {
											id: 'object_type',
									  })?.value
									: ''
							}
							optionsDataName="object_type"
							optionsData={tableData?.dropdown_options?.object_type}
							onChange={(value) => {
								handleColumnSearch(
									{
										id: 'object_type',
										value: value?.id,
									},
									localTableData,
									debounceSearch
								);
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
						Date and Time
					</span>
					<div className="">
						<TableDateRangeFilter
							key="timestamp"
							label="Stockist"
							name="timestamp"
							id="timestamp"
							placeholder="Select"
							value={
								find(localTableData?.columns, {
									id: 'timestamp',
								})?.value
									? find(localTableData?.columns, {
											id: 'timestamp',
									  })?.value
									: ''
							}
							optionsDataName="timestamp"
							optionsData={tableData?.dropdown_options?.timestamp}
							onChange={(value) => {
								handleColumnSearch(
									{
										id: 'timestamp',
										value: value,
									},
									localTableData,
									debounceSearch
								);
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

		columnHelper.accessor((row) => row.actor, {
			id: 'actor',
			header: () => (
				<div className="flex h-full items-start justify-start gap-[10px] whitespace-nowrap border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D] ">
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
			cell: (info) => <ListGeneralCell data={info.getValue()} info={info} />,
		}),
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
								find(localTableData?.columns, {
									id: 'action',
								})?.value
									? find(localTableData?.columns, {
											id: 'action',
									  })?.value
									: ''
							}
							optionsDataName="action"
							optionsData={tableData?.dropdown_options?.action}
							onChange={(value) => {
								handleColumnSearch(
									{
										id: 'action',
										value: value?.id,
									},
									localTableData,
									debounceSearch
								);
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

	return columnsData;
}

export default columns;
