import React from "react";

const EachDescriptionRow = ({ label, content }) => {
	return (
		<div className="flex flex-col gap-[8px] border-b border-[#F0F3F4] pb-[8px] last:border-b-0 last:pb-0">
			<div className="font-lato text-[14px] leading-[20px] text-[#A3ABB1]">
				{label}
			</div>
			<div className="font-lato text-[14px] font-bold leading-[20px] text-[#212429]">
				{content || "Not configured"}
			</div>
		</div>
	);
};

export default EachDescriptionRow;