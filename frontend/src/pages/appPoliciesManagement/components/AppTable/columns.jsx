import { createColumnHelper } from '@tanstack/react-table';
import ListRoleCell from './ListRoleCell';

function columns({ handleViewPolicyConfigure }) {
	const columnHelper = createColumnHelper();

	const columnsData = [
		columnHelper.accessor((row) => row.id, {
			id: 'Id',
			header: () => (
				<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] py-[12px] pl-[32px] pr-[20px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Policy Id
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
				<div className="flex h-full min-w-max items-start justify-start border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Policy Name
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
		columnHelper.accessor((row) => row.configuration, {
			id: 'configuration',
			header: () => (
				<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Configuration
					</span>
				</div>
			),
			cell: (info) => (
				<div className="flex h-full flex-col border-b border-[#F0F3F4] px-[20px] py-[14px]">
					<button
						type="button"
						onClick={() => handleViewPolicyConfigure(info.row.original)}
					>
						<span className="text-start font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-primary">
							View Config
						</span>
					</button>
				</div>
			),
		}),
		columnHelper.accessor((row) => row.description, {
			id: 'description',
			header: () => (
				<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Description
					</span>
				</div>
			),
			cell: (info) => (
				<div className="flex h-full min-w-max max-w-[200px] flex-col border-b border-[#F0F3F4] px-[20px] py-[14px]">
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
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Roles
					</span>
				</div>
			),
			cell: (info) => <ListRoleCell data={info.getValue()} />,
		}),
	];

	return columnsData;
}

export default columns;
