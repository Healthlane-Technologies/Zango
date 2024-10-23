import { createColumnHelper } from '@tanstack/react-table';
import { find } from 'lodash';
import ListCell from '../../../../components/Table/ListCell';
import TableDropdownFilter from '../../../../components/Table/TableDropdownFilter';
import { handleColumnSearch } from '../../../../utils/table';
import HeaderInfo from '../../../../components/Table/HeaderInfo';
import HeaderInfoHover from '../../../../components/Table/HeaderInfoHover';
import Editor from '@monaco-editor/react';

function columns({ debounceSearch, localTableData }) {
	const columnHelper = createColumnHelper();

	const columnsData = [
		columnHelper.accessor((row) => row.id, {
			id: 'id',
			header: () => (
				<div className="flex h-full min-w-max items-start justify-start border-b-[4px] border-[#F0F3F4] py-[12px] pl-[32px] pr-[20px] text-start">
					<span className="font-lato text-[11px] font-normal uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Task Id
					</span>
				</div>
			),
			cell: (info) => {
				return (
					<div className="flex h-full flex-col gap-[8px] border-b border-[#F0F3F4] py-[14px] pl-[32px] pr-[20px] ">
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
				<div className="flex h-full min-w-max items-start justify-start border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="font-lato text-[11px] font-normal uppercase text-[#6C747D] leading-[16px] tracking-[0.6px]  ">
						Task Name
					</span>
				</div>
			),
			cell: (info) => {
				let TaskInfo = () => (
					<div className="flex flex-col gap-2">
						<Editor
							height="150px"
							width="450px"
							theme="vs-dark"
							defaultLanguage="python"
							defaultValue={ info?.row?.original?.code}
							options={{
								readOnly: true,
							}}
						/>
					</div>
				);
				return (
					<div className="flex h-full flex-col border-b border-[#F0F3F4] px-[20px] py-[14px] ">
						<div className=" flex min-w-max flex-row  items-center  justify-start gap-2">
							<span className="text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px] ">
								{info.getValue()}
							</span>
							<span className="">
								<HeaderInfoHover message={<TaskInfo />} />
							</span>
						</div>
					</div>
				);
			},
		}),
		columnHelper.accessor((row) => row.attached_policies, {
			id: 'attached_policies',
			header: () => (
				<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="min-w-max font-lato text-[11px] font-normal uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Policy
					</span>
				</div>
			),
			cell: (info) => <ListCell data={info.getValue()} />,
		}),
		columnHelper.accessor((row) => row.schedule, {
			id: 'schedule',
			header: () => (
				<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="min-w-max font-lato text-[11px] font-normal uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Schedule (UTC)
					</span>
				</div>
			),
			cell: (info) => (
				<div className="flex h-full flex-col border-b border-[#F0F3F4] px-[20px] py-[14px]">
					<span className="text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
						{info.getValue()}
					</span>
				</div>
			),
		}),
		columnHelper.accessor((row) => row.is_enabled, {
			id: 'is_enabled',
			header: () => (
				<div className="flex h-full items-start justify-start gap-[16px] border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="min-w-max font-lato text-[11px] font-normal uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Status
					</span>
					<div className="translate-y-[-2px] ">
						<TableDropdownFilter
							key="is_enabled"
							label="Status"
							name="is_enabled"
							id="is_enabled"
							placeholder="Select"
							value={
								find(localTableData?.columns, { id: 'is_enabled' })?.value
									? find(localTableData?.columns, {
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
								handleColumnSearch(
									{
										id: 'is_enabled',
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
				<div className="flex h-full flex-col border-b border-[#F0F3F4] px-[20px] py-[14px]">
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

	return columnsData;
}

export default columns;
