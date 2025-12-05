import { createColumnHelper } from '@tanstack/react-table';
import { find } from 'lodash';
import TableDropdownFilter from '../../../../components/Table/TableDropdownFilter';
import { handleColumnSearch } from '../../../../utils/table';

function columns({ debounceSearch, localTableData }) {
	const columnHelper = createColumnHelper();

	// Helper function to format date
	const formatDate = (dateString) => {
		if (!dateString) return 'N/A';
		try {
			const date = new Date(dateString);
			return date.toLocaleDateString('en-US', {
				year: 'numeric',
				month: 'short',
				day: 'numeric',
				hour: '2-digit',
				minute: '2-digit'
			});
		} catch {
			return 'N/A';
		}
	};

	const columnsData = [
		columnHelper.accessor((row) => row.name, {
			id: 'name',
			header: () => (
				<div className="flex h-full items-start justify-start py-[12px] pl-[32px] pr-[20px] text-start">
					<span className="min-w-max font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Role Name
					</span>
				</div>
			),
			cell: (info) => {
				const row = info.row.original;
				const isDefault = row.is_default;
				return (
					<div className="flex h-full flex-col gap-[8px] border-b border-[#F0F3F4] py-[14px] pl-[32px] pr-[20px]">
						<div className="flex items-center gap-[8px]">
							<span className="text-start font-lato text-[14px] font-semibold leading-[20px] tracking-[0.2px]">
								{info.getValue()}
							</span>
							{isDefault && (
								<span className="px-[6px] py-[2px] bg-[#EDE9FE] text-[#7C3AED] rounded-[4px] text-[10px] font-medium uppercase tracking-[0.5px]">
									Default
								</span>
							)}
						</div>
						<span className="text-start font-lato text-[12px] text-[#6C747D] leading-[16px]">
							ID: {row.id} • Created: {formatDate(row.created_at)}
						</span>
					</div>
				);
			},
		}),
		columnHelper.accessor((row) => row.is_active, {
			id: 'is_active',
			header: () => (
				<div className="flex h-full items-start justify-start gap-[16px] px-[20px] py-[12px] text-start">
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
		columnHelper.accessor((row) => row.modified_at, {
			id: 'modified_at',
			header: () => (
				<div className="flex h-full items-start justify-start px-[20px] py-[12px] text-start">
					<span className="min-w-max font-lato text-[11px] font-bold uppercase leading-[16px] tracking-[0.6px] text-[#6C747D]">
						Last Modified
					</span>
				</div>
			),
			cell: (info) => {
				const row = info.row.original;
				const modifiedAt = info.getValue();
				const createdAt = row.created_at;
				const isRecent = new Date(modifiedAt) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000); // Within last 7 days
				
				return (
					<div className="flex h-full flex-col gap-[4px] border-b border-[#F0F3F4] px-[20px] py-[14px]">
						<div className="flex items-center gap-[6px]">
							<span className="text-start font-lato text-[14px] font-normal leading-[20px] tracking-[0.2px]">
								{formatDate(modifiedAt)}
							</span>
							{isRecent && (
								<span className="w-[6px] h-[6px] bg-[#10B981] rounded-full"></span>
							)}
						</div>
						<span className="text-start font-lato text-[12px] text-[#6C747D] leading-[16px]">
							{modifiedAt !== createdAt ? 'Modified' : 'Created'}
						</span>
					</div>
				);
			},
		}),
	];

	return columnsData;
}

export default columns;
