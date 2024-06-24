import { Field, FieldArray } from 'formik';
import { ReactComponent as DeleteIcon } from '../../assets/images/svg/delete-icon.svg';

function InputFieldArray({
	label,
	id,
	formik,
	value,
	type = 'text',
	placeholder = 'Enter',
	...props
}) {
	return (
		<div className="flex flex-col gap-[4px]">
			<label
				htmlFor={id}
				className="font-lato text-form-xs font-semibold text-[#A3ABB1]"
			>
				{label}
			</label>

			<FieldArray
				name={id}
				render={(arrayHelpers) => (
					<div className="flex flex-col gap-[12px]">
						<div className="flex flex-col gap-[8px]">
							{value?.map((eachValue, index) => (
								<div key={index}>
									<Field name={`${id}.${index}`}>
										{({ field, form, meta }) => (
											<div className="relative flex flex-col gap-[8px]">
												<div className="relative flex">
													<input
														type={type}
														{...field}
														className="w-full rounded-[6px] border border-[#DDE2E5] px-[16px] py-[14px] font-lato placeholder:text-[#9A9A9A] hover:outline-0 focus:outline-0"
														placeholder={placeholder}
													/>
													{value?.length > 1 ? (
														<button
															type="button"
															onClick={() => arrayHelpers.remove(index)}
															className="absolute inset-y-0 right-[-32px]"
														>
															<DeleteIcon />
														</button>
													) : null}
												</div>

												{meta.touched && meta.error && (
													<div className="font-lato text-form-xs text-[#cc3300]">
														{meta.error}
													</div>
												)}
											</div>
										)}
									</Field>
								</div>
							))}{' '}
						</div>
						<button
							type="button"
							onClick={() => arrayHelpers.push('')}
							className="w-fit"
						>
							<span className="font-lato text-[14px] font-bold leading-[20px] text-primary">
								+ Add more {label}
							</span>
						</button>
					</div>
				)}
			/>

			{formik?.touched.domains && formik?.errors.domains ? (
				<div className="font-lato text-form-xs text-[#cc3300]">
					{formik?.errors.domains}
				</div>
			) : null}
		</div>
	);
}

export default InputFieldArray;
