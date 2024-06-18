import { createColumnHelper } from '@tanstack/react-table';
import { find } from 'lodash';
import ListCell from '../../../../components/Table/ListCell';
import TableDropdownFilter from '../../../../components/Table/TableDropdownFilter';
import { handleColumnSearch } from '../../../../utils/table';

function columns({ debounceSearch, localTableData }) {
	const columnHelper = createColumnHelper();

	const columnsData = [
		columnHelper.accessor((row) => row.name, {
			id: 'name',
			header: () => (
				<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] py-[12px] pl-[32px] pr-[20px] text-start">
					<span className="min-w-max font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Role
					</span>
				</div>
			),
			cell: (info) => {
				return (
					<div className="flex h-full flex-col gap-[8px] border-b border-[#F0F3F4] py-[14px] pl-[32px] pr-[20px]">
						<span className="text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
							{info.getValue()}
						</span>
					</div>
				);
			},
		}),
		columnHelper.accessor((row) => row.attached_policies, {
			id: 'attached_policies',
			header: () => (
				<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Policy(s)
					</span>
				</div>
			),
			cell: (info) => <ListCell data={info.getValue()} />,
		}),
		columnHelper.accessor((row) => row.is_active, {
			id: 'is_active',
			header: () => (
				<div className="flex h-full items-start justify-start gap-[16px] border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Active/Inactive
					</span>
					<div className="translate-y-[-2px]">
						<TableDropdownFilter
							key="is_active"
							label="Stockist"
							name="is_active"
							id="is_active"
							placeholder="Select"
							value={
								find(localTableData?.columns, { id: 'is_active' })?.value
									? find(localTableData?.columns, { id: 'is_active' })?.value
									: ''
							}
							optionsDataName="is_active"
							optionsData={[
								{ id: '', label: '-select-' },
								{ id: 'false', label: 'Inactive' },
								{ id: 'true', label: 'Active' },
							]}
							onChange={(value) => {
								handleColumnSearch(
									{
										id: 'is_active',
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
						className={`w-fit min-w-[77px] rounded-[15px]  px-[4px] py-[3px] text-center font-lato text-[12px] font-normal capitalize leading-[16px] tracking-[0.2px] text-[#1C1E27] ${
							info.getValue() ? 'bg-[#E4F9F2]' : 'bg-[#FBE0DD]'
						}`}
					>
						{info.getValue() ? 'Active' : 'Inactive'}
					</span>
				</div>
			),
		}),
		columnHelper.accessor((row) => row.no_of_users, {
			id: 'no_of_users',
			header: () => (
				<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="min-w-max font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						No. of Users
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
	];

	return columnsData;
}

export default columns;
