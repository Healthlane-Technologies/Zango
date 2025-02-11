function 	EachDescriptionRow({ label, content }) {
	return (
		<tr data-cy="row_data" className="py-[4px] first:pb-[4px] last:pt-[4px]">
			<td data-cy="col_data_1" className="align-baseline">
				<span className="whitespace-nowrap font-lato text-[14px] leading-[20px] tracking-[0.2px] text-[#A3ABB1]">
					{label}
				</span>
			</td>
			<td data-cy="col_data_2" className="w-100 pl-[20px]">{content}</td>
		</tr>
	);
}

export default EachDescriptionRow;
