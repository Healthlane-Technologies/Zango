import React, { useState } from 'react';

const ResizableInput = ({ table }) => {
	const min = 0;
	const max = table.getPageCount();

	const [value, setValue] = useState(1);

	const handleChange = (event) => {
		const value = Math.max(min, Math.min(max, Number(event.target.value)));
		setValue(value);
		table.setPageIndex(value - 1);
	};

	return (
		<label>
			<input
				type="number"
				value={value}
				onChange={handleChange}
				className="fixed top-[100vh]"
			/>
			<div className="flex rounded-[4px] border border-[#DDE2E5] bg-transparent px-[16px] py-[6px] text-center font-lato text-[12px] font-bold leading-[16px] tracking-[0.2px] outline-0 ring-0 placeholder:text-[#6C747D]">
				{table.getState().pagination.pageIndex + 1}
			</div>
		</label>
	);
};

export default ResizableInput;
