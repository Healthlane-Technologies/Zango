import { ReactComponent as TablePaginationNextIcon } from '../../assets/images/svg/table-pagination-next-icon.svg';
import { ReactComponent as TablePaginationPreviousIcon } from '../../assets/images/svg/table-pagination-previous-icon.svg';
import PageCountSelectField from './PageCountSelectField';
import ResizableInput from './ResizableInput';

function TableFooter({ table, tableData }) {
	return (
		<div className="flex border-t border-[#DDE2E5] py-[4px]">
			<div className="flex grow items-center justify-between py-[7px] pl-[22px] pr-[24px]">
				<span className="font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#212429]">
					Total count: {tableData?.total_records}
				</span>
				<span className="font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#212429]">
					<PageCountSelectField
						key="page_count"
						label="Counts per page"
						name="page_count"
						id="page_count"
						placeholder="Select"
						value={table.getState().pagination.pageSize}
						optionsDataName="page_count"
						optionsData={[
							{ id: 10, label: 10 },
							{ id: 25, label: 25 },
							{ id: 50, label: 50 },
							{ id: 100, label: 100 },
						]}
						table={table}
					/>
				</span>
			</div>
			<span className="h-full w-[2px] min-w-[2px] bg-[#F0F3F4]"></span>
			<div className="flex w-fit items-center gap-[14px] px-[56px]">
				<button
					type="button"
					className="flex min-h-[24px] min-w-[24px] cursor-pointer items-center justify-center"
					onClick={() => table.previousPage()}
					disabled={!table.getCanPreviousPage()}
				>
					<TablePaginationPreviousIcon />
				</button>
				<div className="flex items-center gap-[8px]">
					<ResizableInput table={table} />
					<span className="font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#212429]">
						/{table.getPageCount()}
					</span>
				</div>
				<button
					type="button"
					className="flex min-h-[24px] min-w-[24px] cursor-pointer items-center justify-center"
					onClick={() => table.nextPage()}
					disabled={!table.getCanNextPage()}
				>
					<TablePaginationNextIcon />
				</button>
			</div>
		</div>
	);
}

export default TableFooter;
