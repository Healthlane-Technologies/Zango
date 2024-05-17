import { Listbox, Transition } from '@headlessui/react';
import { Fragment, useEffect, useState } from 'react';
import 'react-dates/initialize';
import 'react-dates/lib/css/_datepicker.css';
import { usePopper } from 'react-popper';
import { FixedSizeList as List } from 'react-window';
import { ReactComponent as CloseIcon } from '../../assets/images/svg/close-icon.svg';
import { ReactComponent as FormSelectSearchCloseIcon } from '../../assets/images/svg/form-select-search-close-icon.svg';
import { ReactComponent as SelectCheckIcon } from '../../assets/images/svg/select-check-icon.svg';
import { ReactComponent as SelectSearchIcon } from '../../assets/images/svg/select-search-icon.svg';
import { ReactComponent as TableColumnFilterIcon } from '../../assets/images/svg/table-column-filter-icon.svg';

const TableDropdownFilter = ({
	label,
	optionsData,
	optionsDataName,
	value,
	placeholder,
	onChange,
	...props
}) => {
	const [referenceElement, setReferenceElement] = useState(null);
	const [popperElement, setPopperElement] = useState(null);
	const { styles, attributes } = usePopper(referenceElement, popperElement, {
		placement: 'bottom-end',
	});

	const [searchTerm, setSearchTerm] = useState('');

	const [selected, setSelected] = useState(
		optionsData.find((eachData) => eachData.id === value) || {
			label: placeholder,
			id: '',
			unavailable: true,
		}
	);

	const filteredOptions = searchTerm
		? optionsData?.filter((item) =>
				item.label.toLowerCase().includes(searchTerm.toLowerCase())
		  )
		: optionsData;

	const handleChange = (value) => {
		setSelected(value);
		onChange(value);
	};

	useEffect(() => {
		if (optionsData && value) {
			setSelected(optionsData.find((eachData) => eachData?.id === value));
		}
	}, [value, optionsData]);

	return (
		<div className="flex w-full flex-col gap-[4px]">
			<div className="">
				<Listbox value={selected} onChange={handleChange}>
					<div className="relative">
						<Listbox.Button
							className="w-full font-lato placeholder:text-[#9A9A9A] hover:outline-0 focus:outline-0"
							ref={(ref) => setReferenceElement(ref)}
							id={props.id || props.name}
						>
							<TableColumnFilterIcon
								className={`${value ? 'text-primary' : 'text-[#6C747D]'}`}
							/>
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
							<Listbox.Options className="absolute z-[1] h-fit max-h-96 min-w-max overflow-y-auto bg-white font-lato text-base shadow-form-select focus:outline-none sm:text-sm">
								{optionsData?.length > 0 ? (
									<div className="flex items-center gap-[16px] px-[16px] py-[8px]">
										<div className="relative flex w-full gap-[8px] rounded-[4px] border border-[#DDE2E5] px-[12px] py-[8px]">
											<input
												type="text"
												name="search"
												id="search"
												value={searchTerm}
												onChange={(e) => setSearchTerm(e.target.value)}
												placeholder="Search"
												className="block w-full font-lato font-normal placeholder:text-[#6C747D] focus:outline-0 sm:text-sm"
											/>
											{searchTerm && (
												<div className="relative flex items-center text-[#D4D4D4]">
													<FormSelectSearchCloseIcon
														className="h-[10px] w-[10px] cursor-pointer text-black"
														onClick={() => setSearchTerm('')}
													/>
												</div>
											)}
											<label
												htmlFor="search"
												className="relative flex items-center text-[#D4D4D4]"
											>
												<SelectSearchIcon className="h-[16px] min-h-[16px] w-[16px] min-w-[16px]" />
											</label>
										</div>{' '}
										<button type="button" onClick={() => handleChange(null)}>
											<CloseIcon className="h-[10px] w-[10px]" />
										</button>
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
												`relative flex cursor-default select-none items-center hover:bg-[#F0F3F4]${
													active ? '' : ''
												}`
											}
											value={filteredOptions[index]}
											disabled={filteredOptions[index].unavailable || false}
										>
											{({ selected }) => (
												<div className="flex items-center gap-[8px] px-[12px] py-[4px]">
													{selected &&
													filteredOptions[index].label !== '-select-' ? (
														<span className="relative flex min-h-[12px] min-w-[12px] items-center">
															<SelectCheckIcon />
														</span>
													) : (
														<span className="relative flex min-h-[12px] min-w-[12px] items-center"></span>
													)}
													<span
														className={`block truncate capitalize ${
															selected ? 'font-normal' : 'font-lato font-normal'
														} ${
															filteredOptions[index].label === '-select-'
																? 'text-[#6C747D]'
																: ''
														} ${
															filteredOptions[index].unavailable || false
																? 'opacity-50'
																: 'cursor-pointer'
														}`}
													>
														{filteredOptions[index].label}
													</span>
												</div>
											)}
										</Listbox.Option>
									)}
								</List>
							</Listbox.Options>
						</Transition>
					</div>
				</Listbox>
			</div>
		</div>
	);
};

export default TableDropdownFilter;
