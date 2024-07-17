import { createColumnHelper } from '@tanstack/react-table';
import { find } from 'lodash';
import TableDateRangeFilter from '../../../../components/Table/TableDateRangeFilter';
import TableDropdownFilter from '../../../../components/Table/TableDropdownFilter';
import { handleColumnSearch } from '../../../../utils/table';
function columns({ debounceSearch, localTableData, tableData }) {
	const columnHelper = createColumnHelper();

    const columnsData = [
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
									find(localTableData?.columns, {
										id: 'attempt_type',
									})?.value
										? find(localTableData?.columns, {
												id: 'attempt_type',
										  })?.value
										: ''
								}
								optionsDataName="attempt_type"
								optionsData={
									tableData?.dropdown_options?.attempt_type
										? tableData?.dropdown_options?.attempt_type
										: []
								}
								onChange={(value) => {
									handleColumnSearch(
										{
											id: 'attempt_type',
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
									find(localTableData?.columns, {
										id: 'attempt_time',
									})?.value
										? find(localTableData?.columns, {
												id: 'attempt_time',
										  })?.value
										: ''
								}
								optionsDataName="attempt_time"
								optionsData={tableData?.dropdown_options?.attempt_time}
								onChange={(value) => {
									handleColumnSearch(
										{
											id: 'attempt_time',
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
									find(localTableData?.columns, {
										id: 'role',
									})?.value
										? find(localTableData?.columns, {
												id: 'role',
										  })?.value
										: ''
								}
								optionsDataName="role"
								optionsData={
									tableData?.dropdown_options?.role
										? tableData?.dropdown_options?.role
										: []
								}
								onChange={(value) => {
									handleColumnSearch(
										{
											id: 'role',
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
									find(localTableData?.columns, {
										id: 'session_expired_at',
									})?.value
										? find(localTableData?.columns, {
												id: 'session_expired_at',
										  })?.value
										: ''
								}
								optionsDataName="session_expired_at"
								optionsData={
									tableData?.dropdown_options?.session_expired_at
								}
								onChange={(value) => {
									handleColumnSearch(
										{
											id: 'session_expired_at',
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
									find(localTableData?.columns, {
										id: 'is_login_successful',
									})?.value
										? find(localTableData?.columns, {
												id: 'is_login_successful',
										  })?.value
										: ''
								}
								optionsDataName="is_login_successful"
								optionsData={
									tableData?.dropdown_options?.is_login_successful
										? tableData?.dropdown_options?.is_login_successful
										: []
								}
								onChange={(value) => {
									handleColumnSearch(
										{
											id: 'is_login_successful',
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
							{info.getValue() ? 'Successful' : 'Failed'}
						</span>
					</div>
				),
			}),
		];


	return columnsData;
}

export default columns;
