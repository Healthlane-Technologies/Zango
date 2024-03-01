import { useField } from 'formik';
import { usePopper } from 'react-popper';
import { Listbox, Transition } from '@headlessui/react';
import { Fragment, useRef, useState, useEffect } from 'react';

import { ReactComponent as NavSearchDownArrowIcon } from '../../../../../assets/images/svg/nav-select-down-arrow.svg';
import { ReactComponent as SelectCheckIcon } from '../../../../../assets/images/svg/select-check-icon.svg';

export default function SelectField({
	label,
	formik,
	optionsData,
	optionsDataName,
	value,
	...props
}) {
	const [referenceElement, setReferenceElement] = useState(null);
	const [popperElement, setPopperElement] = useState(null);
	const { styles, attributes } = usePopper(referenceElement, popperElement, {
		placement: 'top-start',
	});

	const [selected, setSelected] = useState(
		optionsData.find((eachData) => eachData.id === value) || {
			label: 'Select',
			id: '',
			unavailable: true,
		}
	);

	const [field, meta] = useField(props);

	const handleChange = (value) => {
		setSelected(value);
		formik.setFieldValue(props.id, value.id);
		if (props.id === 'city_id') {
			formik.setFieldValue('state_id', value.state_id);
		}
	};

	useEffect(() => {
		if (
			optionsData &&
			value &&
			optionsData.find((eachData) => eachData?.id === value)
		) {
			setSelected(optionsData.find((eachData) => eachData?.id === value));
		}

		if (!value) {
			setSelected({
				label: 'Select',
				id: '',
				unavailable: true,
			});
		}
	}, [value, optionsData]);

	const itemRef = useRef();

	return (
		<div className="flex items-center gap-[8px]">
			<span className="font-lato text-[14px] leading-[20px] tracking-[0.2px] text-[#A3ABB1]">
				{label}
			</span>
			<div className="relative flex w-fit flex-col gap-[4px]">
				<div
					ref={itemRef}
					className="absolute block cursor-pointer p-2 font-lato opacity-0"
				></div>
				<div className="">
					<Listbox value={selected} onChange={handleChange}>
						<div className="relative">
							<Listbox.Button
								className="flex w-full items-center gap-[8px] rounded-r-[4px] hover:outline-0 focus:outline-0"
								{...field}
								ref={(ref) => setReferenceElement(ref)}
							>
								<span
									className={`block w-fit truncate bg-transparent text-left font-lato text-[14px] leading-[20px] tracking-[0.2px] outline-0 ring-0 placeholder:text-[#6C747D] ${
										selected.id ? 'text-[#000000]' : 'text-[#000000]'
									}`}
								>
									{selected.label}
								</span>
								<span className="pointer-events-none relative flex items-center">
									<NavSearchDownArrowIcon aria-hidden="true" />
								</span>
							</Listbox.Button>
							<Transition
								as={Fragment}
								leave="transition ease-in duration-100"
								leaveFrom="opacity-100"
								leaveTo="opacity-0"
								// @ts-ignore
								ref={(ref) => setPopperElement(ref)}
								style={styles['popper']}
								{...attributes['popper']}
							>
								<Listbox.Options className="absolute z-[1] h-fit max-h-96 w-fit overflow-y-auto rounded-[4px] bg-[#ffffff] font-lato text-base shadow-appSort focus:outline-none sm:text-sm">
									<div className="flex flex-col gap-[8px] p-[16px] pr-[24px]">
										{optionsData.map((option, index) => (
											<Listbox.Option
												key={index}
												className={({ active }) =>
													`relative flex cursor-default select-none items-center ${
														active ? '' : ''
													}`
												}
												value={option}
											>
												{({ selected }) => (
													<div className="flex items-center gap-[12px]">
														{selected ? (
															<SelectCheckIcon />
														) : (
															<span className="min-w-[12px]"></span>
														)}

														<span
															className={`block whitespace-nowrap font-lato text-[#212429] ${
																selected ? '' : 'font-lato'
															} ${
																optionsData[index].unavailable || false
																	? 'opacity-50'
																	: 'cursor-pointer'
															}`}
														>
															{optionsData[index].label}
														</span>
													</div>
												)}
											</Listbox.Option>
										))}
									</div>
								</Listbox.Options>
							</Transition>
						</div>
					</Listbox>
				</div>
				{meta.touched && meta.error ? (
					<div className="font-lato text-form-xs text-[#cc3300]">
						{meta.error}
					</div>
				) : null}
			</div>
		</div>
	);
}
