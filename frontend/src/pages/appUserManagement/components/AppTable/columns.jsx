import { createColumnHelper } from '@tanstack/react-table';
import { find } from 'lodash';
import ListCell from '../../../../components/Table/ListCell';
import TableDropdownFilter from '../../../../components/Table/TableDropdownFilter';
import { formatTableDate } from '../../../../utils/formats';
import { handleColumnSearch } from '../../../../utils/table';

function columns({ debounceSearch, localTableData }) {
	const columnHelper = createColumnHelper();

	const columnsData = [
		columnHelper.accessor((row) => row.id, {
			id: 'id',
			header: () => (
				<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] py-[12px] pl-[32px] pr-[20px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						User Id
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
		columnHelper.accessor((row) => row.name, {
			id: 'name',
			header: () => (
				<div className="flex h-full items-start justify-start gap-[16px] border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						User Name Active/inactive
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
									? find(localTableData?.columns, {
											id: 'is_active',
									  })?.value
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
			cell: (info) => {
				return (
					<div className="flex h-full flex-col gap-[8px] border-b border-[#F0F3F4] px-[20px] py-[14px]">
						<span className="min-w-max text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
							{info.getValue()}
						</span>
						<span
							className={`w-fit min-w-[77px] rounded-[15px] px-[4px] py-[3px] text-center font-lato text-[12px] font-normal capitalize leading-[16px] tracking-[0.2px] text-[#1C1E27] ${
								info.row.original?.is_active ? 'bg-[#E4F9F2]' : 'bg-[#FBE0DD]'
							}`}
						>
							{info.row.original?.is_active ? 'Active' : 'Inactive'}
						</span>
					</div>
				);
			},
		}),
		columnHelper.accessor((row) => row.mobile, {
			id: 'mobile',
			header: () => (
				<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Mobile
					</span>
				</div>
			),
			cell: (info) => (
				<div className="flex h-full min-w-max flex-col border-b border-[#F0F3F4] px-[20px] py-[14px]">
					<span className="text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
						{info.getValue()}
					</span>
				</div>
			),
		}),
		columnHelper.accessor((row) => row.email, {
			id: 'email',
			header: () => (
				<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Email
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
		columnHelper.accessor((row) => row.roles, {
			id: 'roles',
			header: () => (
				<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="min-w-max font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Management Access
					</span>
				</div>
			),
			cell: (info) => <ListCell data={info.getValue()} />,
		}),
		columnHelper.accessor((row) => row.created_at, {
			id: 'created_at',
			header: () => (
				<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Last Login / Date Joined
					</span>
				</div>
			),
			cell: (info) => (
				<div className="flex h-full flex-col gap-[4px] border-b border-[#F0F3F4] px-[20px] py-[14px]">
					<span className="w-fit min-w-max text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
						{info.row.original?.last_login
							? formatTableDate(info.row.original?.last_login)
							: null}
					</span>
					<span className="w-fit min-w-max text-start font-lato text-[12px] font-normal leading-[16px] tracking-[0.2px] text-[#A3ABB1]">
						{formatTableDate(info.getValue())}
					</span>
				</div>
			),
		}),
		columnHelper.accessor((row) => row.password_change_at, {
			id: 'password_change_at',
			header: () => (
				<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Password Change date
					</span>
				</div>
			),
			cell: (info) => (
				<div className="flex h-full flex-col gap-[4px] border-b border-[#F0F3F4] px-[20px] py-[14px]">
					<span className="w-fit min-w-max text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
						{formatTableDate(info.getValue())}
					</span>
				</div>
			),
		}),
	];

	return columnsData;
}

export default columns;
