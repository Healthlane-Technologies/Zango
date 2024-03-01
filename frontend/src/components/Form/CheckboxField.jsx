import { useField } from 'formik';
import React from 'react';
import { ReactComponent as IconToggleTick } from '../../assets/images/svg/checkbox-tick.svg';

export default function CheckboxField({ label, content, ...props }) {
	const [field, meta] = useField({ ...props });
	return (
		<div className="my-1 flex flex-col items-start gap-1">
			<label className="relative flex items-center gap-4">
				{props.value ? (
					<div className="relative h-[20px] w-[20px] rounded-sm border-2 border-primary bg-primary">
						<IconToggleTick className="absolute inset-0 top-[3px] left-[2px]" />
					</div>
				) : (
					<div className="h-[20px] w-[20px] rounded-sm border-2 border-[#C4C4C4]"></div>
				)}

				<input
					className="invisible absolute h-[0px] w-[0px]"
					type="checkbox"
					{...field}
					{...props}
				/>
				{content ? (
					content
				) : (
					<span className="font-lato leading-5">{label}</span>
				)}
			</label>
			{meta.touched && meta.error ? (
				<div className="font-lato text-form-xs text-[#cc3300]">
					{meta.error}
				</div>
			) : null}
		</div>
	);
}
