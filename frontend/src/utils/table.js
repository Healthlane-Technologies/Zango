import { findIndex, set } from 'lodash';

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
