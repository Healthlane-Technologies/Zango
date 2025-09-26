import { Field, FieldArray } from 'formik';
import { ReactComponent as DeleteIcon } from '../../assets/images/svg/delete-icon.svg';

function DomainFieldArray({
	label,
	id,
	formik,
	value,
	placeholder = 'Enter domain',
	...props
}) {
	const handlePrimaryChange = (index, arrayHelpers) => {
		// Make only the selected domain primary and others non-primary
		const updatedDomains = value.map((domain, i) => ({
			...domain,
			is_primary: i === index
		}));
		formik.setFieldValue(id, updatedDomains);
	};

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
							{value?.map((domainObj, index) => (
								<div key={index}>
									<div className="relative flex flex-col gap-[8px]">
										<div className="relative flex items-center gap-[12px]">
											<div className="flex-1">
												<Field name={`${id}.${index}.domain`}>
													{({ field, form, meta }) => (
														<>
															<input
																type="text"
																{...field}
																className="w-full rounded-[6px] border border-[#DDE2E5] px-[16px] py-[14px] font-lato placeholder:text-[#9A9A9A] hover:outline-0 focus:outline-0"
																placeholder={placeholder}
															/>
															{meta.touched && meta.error && (
																<div className="font-lato text-form-xs text-[#cc3300] mt-[4px]">
																	{meta.error}
																</div>
															)}
														</>
													)}
												</Field>
											</div>
											
											<div className="flex items-center gap-[8px]">
												<label className="flex items-center gap-[8px] cursor-pointer">
													<input
														type="radio"
														name="primaryDomain"
														checked={domainObj.is_primary || false}
														onChange={() => handlePrimaryChange(index, arrayHelpers)}
														className="w-[16px] h-[16px] text-[#5048ED] focus:ring-[#5048ED] focus:ring-2"
													/>
													<span className="text-[13px] font-medium text-[#6B7280]">
														Primary
													</span>
												</label>
												
												{value?.length > 1 && (
													<button
														type="button"
														onClick={() => arrayHelpers.remove(index)}
														className="p-[4px] hover:bg-[#F3F4F6] rounded-[4px] transition-colors"
													>
														<DeleteIcon />
													</button>
												)}
											</div>
										</div>
									</div>
								</div>
							))}
						</div>
						<button
							type="button"
							onClick={() => arrayHelpers.push({ domain: '', is_primary: value.length === 0 })}
							className="w-fit"
						>
							<span className="font-lato text-[14px] font-bold leading-[20px] text-primary">
								+ Add more {label}
							</span>
						</button>
					</div>
				)}
			/>

			{formik?.touched[id] && formik?.errors[id] && typeof formik.errors[id] === 'string' && (
				<div className="font-lato text-form-xs text-[#cc3300]">
					{formik?.errors[id]}
				</div>
			)}
		</div>
	);
}

export default DomainFieldArray;