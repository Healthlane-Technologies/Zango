import { useField } from 'formik';
import { usePopper } from 'react-popper';
import { Listbox, Transition } from '@headlessui/react';
import { Fragment, useRef, useState, useEffect } from 'react';

import { ReactComponent as NavSearchDownArrowIcon } from '../../../../../assets/images/svg/nav-select-down-arrow.svg';

export default function Select({
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
		<div className="relative flex w-[198px] flex-col gap-[4px]">
			<div
				ref={itemRef}
				className="absolute block cursor-pointer p-2 font-lato opacity-0"
			></div>
			<div className="">
				<Listbox value={selected} onChange={handleChange}>
					<div className="relative">
						<Listbox.Button
							className="flex w-full items-center gap-[12px] rounded-r-[4px] border-l border-l-[#DDE2E5] bg-[#F0F3F4] py-[6px] px-[16px] hover:outline-0 focus:outline-0"
							{...field}
							ref={(ref) => setReferenceElement(ref)}
						>
							<span
								className={`block w-[80%] truncate bg-transparent text-left font-lato text-sm tracking-[0.2px] outline-0 ring-0 placeholder:text-[#6C747D] ${
									selected.id ? 'font-bold text-[#212429]' : 'text-[#9A9A9A]'
								}`}
							>
								{selected.label}
							</span>
							<span className="pointer-events-none absolute inset-y-0 right-[24px] flex items-center">
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
							<Listbox.Options className="absolute z-[1] mt-[-32px] h-fit max-h-96 w-full overflow-y-auto rounded-[4px] bg-[#495057] font-lato text-base focus:outline-none sm:text-sm">
								<div className="relative">
									<div className="flex w-full items-center gap-[12px] rounded-r-[4px] border-l border-[#495057] bg-[#495057] py-[6px] px-[16px] hover:outline-0 focus:outline-0">
										<span
											className={`block truncate bg-transparent text-left font-lato text-sm  font-bold tracking-[0.2px] text-[#FFFFFF] outline-0 ring-0 placeholder:text-[#6C747D] `}
										>
											{selected.label}
										</span>
										<span className="pointer-events-none absolute inset-y-0 right-[24px] flex items-center">
											<NavSearchDownArrowIcon
												aria-hidden="true"
												className="rotate-180 text-[#FFFFFF]"
											/>
										</span>
									</div>
								</div>
								<div className="flex flex-col pt-[6px] pb-[12px]">
									{optionsData.map((option, index) => (
										<Listbox.Option
											key={index}
											className={({ active }) =>
												`relative flex cursor-default select-none items-center px-[16px] py-[4px] ${
													active ? '' : ''
												}`
											}
											value={option}
										>
											{({ selected }) => (
												<>
													<span
														className={`block font-lato text-[#FFFFFF] ${
															selected ? '' : 'font-lato'
														} ${
															optionsData[index].unavailable || false
																? 'opacity-50'
																: 'cursor-pointer'
														}`}
													>
														{optionsData[index].label}
													</span>
												</>
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
	);
}
