import { get } from 'lodash';
import { useEffect, useState } from 'react';

export default function ColorPicker({ data }) {
	let { id, formik, label } = data;
	const [color, setColor] = useState(get(formik.values, id, '#ffffff'));

	useEffect(() => {
		formik.setFieldValue(id, color);
	}, [color]);

	const handleColorChange = (selectedColor) => {
		setColor(selectedColor);
	};

	return (
		<>
			<div className="flex flex-col gap-[4px]">
				<label
					htmlFor={id}
					className="font-lato text-form-xs font-semibold text-[#A3ABB1]"
				>
					{label}
				</label>
				<div className="flex w-full rounded-[6px] border border-[#DDE2E5]">
					<div className="relative flex w-full flex-col">
						<div className="flex w-full items-center gap-[12px] px-[16px] py-[10px]">
							<CustomColorPicker
								defaultColor={color}
								onChange={handleColorChange}
							/>
							<span className="font-lato text-[14px] uppercase leading-[20px] tracking-[0.2px] text-[#212429]">
								{color ? color : ''}
							</span>
						</div>

						{formik.touched[id] && formik.errors[id] ? (
							<div className="font-lato text-form-xs text-[#cc3300]">
								{formik.errors[id]}
							</div>
						) : null}
					</div>
				</div>
			</div>
		</>
	);
}

const CustomColorPicker = ({ defaultColor = '#5048ED', onChange }) => {
	const [color, setColor] = useState(defaultColor);

	const handleColorChange = (event) => {
		const selectedColor = event.target.value;
		setColor(selectedColor);
		if (onChange) {
			onChange(selectedColor);
		}
	};

	return (
		<div className="relative inline-block">
			<input
				type="color"
				value={color}
				onChange={handleColorChange}
				className="pointer-events-none absolute opacity-0"
			/>
			<div
				onClick={(e) => e.target.previousSibling.click()}
				className="h-[26px] w-[26px] cursor-pointer rounded border-2 border-gray-300"
				style={{ backgroundColor: color }}
				title="Pick a color"
			/>
		</div>
	);
};
