function EachDescriptionRow({ label, content }) {
	return (
		<tr className="py-[4px] first:pb-[4px] last:pt-[4px]">
			<td className="align-baseline">
				<span className="whitespace-nowrap font-lato text-[14px] leading-[20px] tracking-[0.2px] text-[#A3ABB1]">
					{label}
				</span>
			</td>
			<td className="w-full pl-[20px]">{content}</td>
		</tr>
	);
}

export default EachDescriptionRow;
