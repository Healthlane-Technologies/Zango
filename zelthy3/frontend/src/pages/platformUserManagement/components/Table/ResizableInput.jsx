import React, { useState } from 'react';
import { useEffect } from 'react';

const ResizableInput = ({ table }) => {
	const [text, setText] = useState('');

	useEffect(() => {
		setText((table.getState().pagination.pageIndex + 1).toString());
	}, [table.getState().pagination.pageIndex]);

	return (
		<input
			type="number"
			value={text}
			onChange={(e) => {
				const page = e.target.value ? Number(e.target.value) - 1 : 0;
				table.setPageIndex(page);
				setText(e.target.value);
			}}
			style={{ maxWidth: `calc(${text.length}ch + 34px) ` }}
			className="flex min-w-[30px] rounded-[4px] border border-[#DDE2E5] bg-transparent px-[16px] py-[6px] font-lato text-[12px] font-bold leading-[16px] tracking-[0.2px] outline-0 ring-0 placeholder:text-[#6C747D]"
		/>
	);
};

export default ResizableInput;
