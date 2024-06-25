import { Listbox, Transition } from '@headlessui/react';
import { useField } from 'formik';
import { Fragment, useEffect, useState } from 'react';
import 'react-dates/initialize';
import 'react-dates/lib/css/_datepicker.css';
import { usePopper } from 'react-popper';
import { FixedSizeList as List } from 'react-window';
import { ReactComponent as FormSelectDropdownIcon } from '../../assets/images/svg/form-select-dropdown-icon.svg';
import { ReactComponent as FormSelectSearchCloseIcon } from '../../assets/images/svg/form-select-search-close-icon.svg';

const SelectField = ({
	label,
	formik,
	optionsData,
	optionsDataName,
	value,
	placeholder,
	...props
}) => {
	const [referenceElement, setReferenceElement] = useState(null);
	const [popperElement, setPopperElement] = useState(null);
	const { styles, attributes } = usePopper(referenceElement, popperElement);

	const [searchTerm, setSearchTerm] = useState('');

	const [selected, setSelected] = useState(
		optionsData.find((eachData) => eachData.id === value) || {
			label: placeholder,
			id: '',
			unavailable: true,
		}
	);
	const [field, meta] = useField(props);

	const filteredOptions = searchTerm
		? optionsData?.filter((item) =>
				item.label.toLowerCase().includes(searchTerm.toLowerCase())
		  )
		: optionsData;

	const handleChange = (value) => {
		setSelected(value);
		formik.setFieldValue(props.name, value.id);
	};

	useEffect(() => {
		if (optionsData && value) {
			setSelected(optionsData.find((eachData) => eachData?.id === value));
		}
	}, [value, optionsData]);

	return (
		<div className="flex w-full flex-col gap-[4px]">
			<label
				htmlFor={props.id || props.name}
				className="font-lato text-[12px] font-semibold text-[#A3ABB1]"
			>
				{label}
			</label>
			<div data-cy="dropdown_field" className="">
				<Listbox value={selected} onChange={handleChange}>
					<div className="relative">
						<Listbox.Button
							className="w-full rounded-[6px] rounded-[6px] border border-[#DDE2E5] px-[16px] px-[16px] py-[14px] py-[14px] font-lato placeholder:text-[#9A9A9A] hover:outline-0 focus:outline-0"
							{...field}
							ref={(ref) => setReferenceElement(ref)}
							id={props.id || props.name}
						>
							<span
								className={`block w-[80%] truncate text-left ${
									selected?.id ? '' : 'text-[#9A9A9A]'
								}`}
							>
								{selected?.label}
							</span>
							<span className="pointer-events-none absolute inset-y-0 right-[16px] flex items-center">
								<FormSelectDropdownIcon aria-hidden="true" />
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
							<Listbox.Options data-cy="dropdown_values" className="absolute z-[1] h-fit max-h-96 w-full overflow-y-auto border bg-white px-[8px] py-[12px] font-lato text-base ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
								{optionsData?.length > 10 ? (
									<div className="relative mb-4">
										<input
											type="text"
											name="search"
											id="search"
											value={searchTerm}
											onChange={(e) => setSearchTerm(e.target.value)}
											className="block w-full border border-gray-300 bg-gray-50 px-2 py-2 pr-12 shadow-sm focus:outline-0 sm:text-sm"
										/>
										{searchTerm && (
											<div className="absolute inset-y-0 right-[4px] flex items-center px-2 py-2 text-[#D4D4D4]">
												<FormSelectSearchCloseIcon
													className="h-[10px] w-[10px] cursor-pointer text-black"
													onClick={() => setSearchTerm('')}
												/>
											</div>
										)}
									</div>
								) : null}

								<List
									height={
										filteredOptions.length < 10
											? filteredOptions.length * 40
											: 300
									}
									itemCount={filteredOptions.length}
									itemSize={40}
									itemData={filteredOptions}
									className="complete-hidden-scroll-style"
								>
									{({ index, style }) => (
										<Listbox.Option
											key={index}
											style={style}
											className={({ active }) =>
												`relative cursor-default select-none p-2 ${
													active ? '' : ''
												}`
											}
											value={filteredOptions[index]}
											disabled={filteredOptions[index].unavailable || false}
										>
											{({ selected }) => (
												<>
													<span
														className={`block truncate ${
															selected ? 'font-bold' : 'font-lato'
														} ${
															filteredOptions[index].unavailable || false
																? 'opacity-50'
																: 'cursor-pointer'
														}`}
													>
														{filteredOptions[index].label}
													</span>
													{selected ? (
														<span className="absolute inset-y-0 left-0 flex items-center"></span>
													) : null}
												</>
											)}
										</Listbox.Option>
									)}
								</List>
							</Listbox.Options>
						</Transition>
					</div>
				</Listbox>
			</div>
			{meta.touched && meta.error ? (
				<div className="font-lato text-[12px] text-[#cc3300]">{meta.error}</div>
			) : null}
		</div>
	);
};

export default SelectField;
