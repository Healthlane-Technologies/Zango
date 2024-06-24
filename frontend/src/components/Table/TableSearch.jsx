import debounce from 'just-debounce-it';
import { useEffect, useRef } from 'react';
import { ReactComponent as TableSearchIcon } from '../../assets/images/svg/table-search-icon.svg';

function TableSearch({
	searchPlaceholder,
	localTableData,
	updateLocalTableData,
	SearchFilters,
}) {
	const searchRef = useRef();

	const handleSearch = (value) => {
		let searchData = {
			...localTableData,
			searchValue: value,
			pageIndex: 0,
		};
		debounceSearch(searchData);
	};

	const debounceSearch = debounce((data) => {
		updateLocalTableData(data);
	}, 500);

	useEffect(() => {
		searchRef.current.value = localTableData?.searchValue || '';
	}, [localTableData]);

	return (
		<div className="flex bg-[#F0F3F4]">
			<div className="flex grow items-center gap-[24px] py-[13px] pl-[24px] pr-[32px]">
				<div className="flex grow items-center gap-[8px]">
					<TableSearchIcon />
					<input
						data-cy="table_search_field"
						ref={searchRef}
						id="searchValue"
						name="searchValue"
						type="text"
						className="w-full bg-transparent font-lato text-sm leading-[20px] tracking-[0.2px] outline-0 ring-0 placeholder:text-[#6C747D]"
						placeholder={searchPlaceholder}
						onChange={(e) => handleSearch(e?.target?.value)}
					/>
				</div>
				{SearchFilters}
			</div>
		</div>
	);
}

export default TableSearch;
