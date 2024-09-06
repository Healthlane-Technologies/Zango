import { createColumnHelper } from '@tanstack/react-table';
import ViewDetailButton from './ViewDetailButton';

function columns({ dispatch }) {
	const columnHelper = createColumnHelper();
	const columnsData = [
		columnHelper.accessor((row) => row.name, {
			id: 'name',
			header: () => (
				<div className="flex h-full min-w-max items-start justify-start border-b-[4px] border-[#F0F3F4] py-[12px] pl-[32px] pr-[20px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Package Name
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

		columnHelper.accessor((row) => row.installed_version, {
			id: 'installed_version',
			header: () => (
				<div className="flex h-full items-start justify-start border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="min-w-max font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Version
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
		columnHelper.accessor((row) => row.status, {
			id: 'status',
			header: () => (
				<div className="flex h-full min-w-max items-start justify-start border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Status
					</span>
				</div>
			),
			cell: (info) => (
				<div className="flex h-full flex-col border-b border-[#F0F3F4] px-[20px] py-[14px]">
					<span
						className={`w-fit min-w-max rounded-[15px] px-[12px] py-[3px] text-center font-lato text-[12px] font-normal capitalize leading-[16px] tracking-[0.2px] text-[#1C1E27] ${
							info.getValue() === 'Installed' ? 'bg-[#E4F9F2]' : 'bg-[#FBE0DD]'
						}`}
					>
						{info.getValue()}
					</span>
				</div>
			),
		}),
		columnHelper.accessor((row) => row.status, {
			id: 'status',
			header: () => (
				<div className="flex h-full min-w-max items-start justify-start border-b-[4px] border-[#F0F3F4] px-[20px] py-[12px] text-start">
					<span className="font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Status
					</span>
				</div>
			),
			cell: (info) =>  <ViewDetailButton dispatch={dispatch} info={info} />
		}),
	];

	return columnsData;
}

export default columns;


