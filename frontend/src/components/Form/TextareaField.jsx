import { useField } from 'formik';

function TextareaField({ label, content, type = 'text', key, id, ...props }) {
	const [field, meta] = useField({ ...props });
	return (
		<div data-cy="text_area"key={key} className="flex flex-col gap-[4px]">
			<label
				htmlFor={id}
				className="font-lato text-form-xs font-semibold text-[#A3ABB1]"
			>
				{label}
			</label>
			<textarea
				type={type}
				className="min-h-[89px] rounded-[6px] rounded-[6px] border border border-[#DDE2E5] border-[#DDE2E5] px-[16px] px-[16px] py-[14px] py-[14px] font-lato placeholder:text-[#9A9A9A] hover:outline-0 focus:outline-0"
				{...field}
				{...props}
			/>
			{meta.touched && meta.error ? (
				<div className="font-lato text-form-xs text-[#cc3300]">
					{meta.error}
				</div>
			) : null}
		</div>
	);
}

export default TextareaField;
