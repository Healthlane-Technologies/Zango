import { findIndex, set } from 'lodash';

/**
 * Handle table colunm filter search
 *
 * @param {*} data - table data
 * @param {*} localTableData - filter data stored in specific page slice
 * @param {*} debounceSearch - callback
 */
export const handleColumnSearch = (data, localTableData, debounceSearch) => {
	let tempTableData = JSON.parse(JSON.stringify(localTableData));
	let index = findIndex(tempTableData?.columns, { id: data?.id });

	if (index !== -1) {
		set(tempTableData?.columns[index], 'value', data?.value);
	} else {
		tempTableData?.columns.push({ id: data?.id, value: data?.value });
	}

	let searchData = {
		...tempTableData,
		pageIndex: 0,
	};

	debounceSearch(searchData);
};
