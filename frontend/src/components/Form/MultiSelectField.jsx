import { Listbox, Transition } from '@headlessui/react';
import { useField } from 'formik';
import { Fragment, useEffect, useState } from 'react';
import 'react-dates/initialize';
import 'react-dates/lib/css/_datepicker.css';
import { usePopper } from 'react-popper';
import { ReactComponent as FormSelectSearchCloseIcon } from '../../assets/images/svg/form-select-search-close-icon.svg';
import { ReactComponent as FormSelectDropdownIcon } from '../../assets/images/svg/form-select-dropdown-icon.svg';
import { ReactComponent as RemoveOptionIcon } from '../../assets/images/svg/remove-option-icon.svg';
import { ReactComponent as FormMultiSelectCheckIcon } from '../../assets/images/svg/form-multiselect-check-icon.svg';

const MultiSelectField = ({
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
		optionsData.filter((eachData) => value.indexOf(eachData.id) >= 0)
	);

	const [field, meta] = useField(props);

	const filteredOptions = searchTerm
		? optionsData?.filter((item) =>
				item.label.toLowerCase().includes(searchTerm.toLowerCase())
		  )
		: optionsData;

	const handleChange = (selectedValues) => {
		let selectedAllValuesID = selectedValues?.map((selectedValue) => {
			return selectedValue?.id;
		});

		let selectOptions = optionsData.filter(
			(eachData) => selectedAllValuesID.indexOf(eachData.id) >= 0
		);
		setSelected((previous) => [...selectOptions]);

		formik.setFieldValue(props.name, [...selectedAllValuesID]);
	};

	const handleRemove = (selectedValue) => {
		setSelected((previous) => [
			...previous.filter((eachValue) => eachValue.id !== selectedValue.id),
		]);

		formik.setFieldValue(props.name, [
			...value.filter((eachValue) => eachValue !== selectedValue.id),
		]);
	};

	useEffect(() => {
		if (optionsData && value?.length) {
			setSelected(
				optionsData.filter((eachData) => value.indexOf(eachData.id) >= 0)
			);
		}
	}, [value, optionsData]);

	return (
		<div className="flex w-full flex-col gap-[4px]">
			<label
				htmlFor={props.value || props.name}
				className="font-lato text-[12px] font-semibold text-[#A3ABB1]"
			>
				{label}
			</label>
			<div data-cy="dropdown_field" className="flex flex-col gap-[12px]">
				<Listbox value={selected} onChange={handleChange} multiple>
					<div className="relative">
						<Listbox.Button
							className="w-full rounded-[6px] rounded-[6px] border border-[#DDE2E5] px-[16px] px-[16px] py-[14px] py-[14px] font-lato placeholder:text-[#9A9A9A] hover:outline-0 focus:outline-0"
							{...field}
							ref={(ref) => setReferenceElement(ref)}
							id={props.id || props.name}
						>
							<span
								className={`block w-[80%] truncate text-left ${
									selected?.length ? '' : 'text-[#9A9A9A]'
								}`}
							>
								{selected?.length
									? `${selected?.length} selected`
									: placeholder}
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
							<Listbox.Options
								data-cy="multi_select_values"
								className="absolute z-[1] h-fit max-h-96 w-full overflow-y-auto border bg-white px-[8px] py-[12px] font-lato text-base ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm"
							>
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

								{/* Replaced the react-window List with a normal map */}
								<Listbox.Options className="space-y-2">
									{filteredOptions.map((option, index) => (
										<Listbox.Option
											key={index}
											className={({ active }) =>
												`relative flex cursor-default select-none items-center gap-[12px] p-2 ${
													active ? '' : ''
												}`
											}
											value={option}
											disabled={option.unavailable || false}
										>
											<span className="flex items-center">
												<FormMultiSelectCheckIcon
													className={`${
														value.indexOf(option.id) >= 0
															? 'text-[#000000]'
															: 'text-[#eff3f4]'
													} `}
												/>
											</span>
											<span
												className={`block truncate font-lato ${
													option.unavailable || false
														? 'opacity-50'
														: 'cursor-pointer'
												}`}
											>
												{option.label}
											</span>
										</Listbox.Option>
									))}
								</Listbox.Options>
							</Listbox.Options>
						</Transition>
					</div>
				</Listbox>
				{selected?.length ? (
					<div className="flex flex-wrap gap-[8px]">
						{selected?.map((eachData) => {
							return (
								<div
									key={eachData.id}
									className="flex gap-[16px] rounded-[16px] border border-[#6C747D] px-[12px] py-[4px]"
								>
									<span className="font-lato text-[14px] leading-[20px] tracking-[0.2px] text-[#212429]">
										{eachData.label}
									</span>
									<button type="button" onClick={() => handleRemove(eachData)}>
										<RemoveOptionIcon />
									</button>
								</div>
							);
						})}
					</div>
				) : null}
			</div>

			{meta.touched && meta.error ? (
				<div
					data-cy="error_message"
					className="font-lato text-[12px] text-[#cc3300]"
				>
					{meta.error}
				</div>
			) : null}
		</div>
	);
};

export default MultiSelectField;
