import { flexRender } from '@tanstack/react-table';

function TableHead({ table }) {
	return (
		<thead className="sticky top-0 z-[2] bg-[#ffffff]  z-30">
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
	);
}

export default TableHead;
