import { useField } from 'formik';
import React from 'react';

const RadioPillField = ({ label, name, radioData, formik, ...props }) => {
	const [field] = useField({ ...props, type: 'radio' });

	return (
		<div className="flex flex-col gap-[1px]">
			<div className="flex flex-wrap items-center gap-[8px]">
				{radioData.map(({ id, value, label }) => {
					return (
						<label
							key={id}
							htmlFor={id}
							className="relative flex items-start gap-4 cursor-pointer"
						>
							<input
								{...field}
								className="invisible absolute h-[0px] w-[0px]"
								type="radio"
								id={id}
								value={value}
								checked={props.value === value}
								onChange={() => {
									formik.setTouched({ ...formik.touched, [name]: true });
									formik.setFieldValue(name, value);
								}}
							/>
							<span
								className={`font-invention-app rounded-[18px] border-[1.5px] px-[10px] py-[4px] text-sm ${
									props.value === value
										? 'border-[#5048ED] bg-[#5048ED] font-bold text-[#ffffff]'
										: 'border-[#DDE2E5]'
								}`}
							>
								{label}
							</span>
						</label>
					);
				})}

				{formik.errors[name] && formik.touched[name] ? (
					<div className="font-invention-app text-form-xs text-[#cc3300]">
						{formik.errors[name]}
					</div>
				) : null}
			</div>
		</div>
	);
};

export default RadioPillField