import { flexRender } from '@tanstack/react-table';

function TableBody({ table, RowMenu }) {
	return (
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

					<td data-cy="three_dots_menu" className="sticky inset-y-0 right-0 z-[1] hidden h-full w-[188px] items-center justify-end border-b border-[#F0F3F4] bg-gradient-to-l from-[#F5F7F8] from-0% to-90% px-[32px]  group-hover:flex">
						{RowMenu ? <RowMenu rowData={row.original} /> : null}
					</td>
				</tr>
			))}
		</tbody>
	);
}

export default TableBody;
