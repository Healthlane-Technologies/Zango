import { Listbox, Transition } from '@headlessui/react';
import { useField } from 'formik';
import { Fragment, useEffect, useState } from 'react';
import 'react-dates/initialize';
import 'react-dates/lib/css/_datepicker.css';
import { usePopper } from 'react-popper';
import { FixedSizeList as List } from 'react-window';
import { ReactComponent as FormSelectDropdownIcon } from '../../assets/images/svg/form-select-dropdown-icon.svg';
import { ReactComponent as FormSelectSearchCloseIcon } from '../../assets/images/svg/form-select-search-close-icon.svg';

const FontFamilySelectField = ({
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
	const [loadedFonts, setLoadedFonts] = useState(new Set());

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

	// Function to load Google Font dynamically
	const loadFont = (fontFamily) => {
		if (!fontFamily || loadedFonts.has(fontFamily)) return;

		const fontUrl = `https://fonts.googleapis.com/css2?family=${fontFamily.replace(/ /g, '+')}&display=swap`;
		
		// Check if the font link already exists
		const existingLink = document.querySelector(`link[href="${fontUrl}"]`);
		if (existingLink) {
			setLoadedFonts(prev => new Set([...prev, fontFamily]));
			return;
		}

		// Create and append the font link
		const link = document.createElement('link');
		link.href = fontUrl;
		link.rel = 'stylesheet';
		link.onload = () => {
			setLoadedFonts(prev => new Set([...prev, fontFamily]));
		};
		document.head.appendChild(link);
	};

	// Load fonts for visible options
	useEffect(() => {
		// Load the first 20 fonts initially for better UX
		const fontsToLoad = filteredOptions.slice(0, 20);
		fontsToLoad.forEach(option => {
			if (option.id && option.id !== '') {
				loadFont(option.id);
			}
		});
	}, [filteredOptions]);

	// Load font when selected changes
	useEffect(() => {
		if (selected?.id && selected.id !== '') {
			loadFont(selected.id);
		}
	}, [selected]);

	const handleChange = (value) => {
		setSelected(value);
		formik.setFieldValue(props.name, value.id);
		// Load the selected font
		if (value.id && value.id !== '') {
			loadFont(value.id);
		}
	};

	useEffect(() => {
		if (optionsData && value) {
			setSelected(optionsData.find((eachData) => eachData?.id === value));
		}
	}, [value, optionsData]);

	// Custom option renderer with font preview
	const FontOption = ({ index, style, data }) => {
		const option = data[index];
		const fontFamily = option.id;
		const isLoaded = loadedFonts.has(fontFamily);

		// Load font when option becomes visible
		useEffect(() => {
			if (fontFamily && fontFamily !== '') {
				loadFont(fontFamily);
			}
		}, [fontFamily]);

		return (
			<Listbox.Option
				key={index}
				style={style}
				className={({ active }) =>
					`relative cursor-default select-none p-2 ${
						active ? 'bg-gray-100' : ''
					}`
				}
				value={option}
				disabled={option.unavailable || false}
			>
				{({ selected }) => (
					<div className="flex flex-col">
						<div className="flex items-center justify-between">
							<span
								className={`block truncate text-sm ${
									selected ? 'font-bold' : 'font-normal'
								} ${
									option.unavailable || false
										? 'opacity-50'
										: 'cursor-pointer'
								}`}
							>
								{option.label}
							</span>
						</div>
						{/* Font Preview */}
						{isLoaded && fontFamily && fontFamily !== '' && (
							<div 
								className="text-xs text-gray-600 mt-1 truncate"
								style={{ 
									fontFamily: fontFamily,
									fontSize: '12px',
									lineHeight: '1.2'
								}}
							>
								The quick brown fox jumps over the lazy dog
							</div>
						)}
						{!isLoaded && fontFamily && fontFamily !== '' && (
							<div className="text-xs text-gray-400 mt-1 italic">
								Loading font preview...
							</div>
						)}
					</div>
				)}
			</Listbox.Option>
		);
	};

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
							className="w-full rounded-[6px] border border-[#DDE2E5] px-[16px] py-[14px] font-lato placeholder:text-[#9A9A9A] hover:outline-0 focus:outline-0"
							{...field}
							ref={(ref) => setReferenceElement(ref)}
							id={props.id || props.name}
						>
							<div className="flex flex-col items-start">
								<span
									className={`block w-[80%] truncate text-left ${
										selected?.id ? '' : 'text-[#9A9A9A]'
									}`}
								>
									{selected?.label}
								</span>
								{/* Font preview in the button */}
								{selected?.id && selected.id !== '' && loadedFonts.has(selected.id) && (
									<span 
										className="text-xs text-gray-500 mt-1 truncate w-[80%] text-left"
										style={{ 
											fontFamily: selected.id,
											fontSize: '11px',
											lineHeight: '1.2'
										}}
									>
										The quick brown fox
									</span>
								)}
							</div>
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
											placeholder="Search fonts..."
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
										filteredOptions.length < 8
											? filteredOptions.length * 60  // Increased height for font preview
											: 480  // Increased max height
									}
									itemCount={filteredOptions.length}
									itemSize={60}  // Increased item size for font preview
									itemData={filteredOptions}
									className="complete-hidden-scroll-style"
								>
									{FontOption}
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

export default FontFamilySelectField;