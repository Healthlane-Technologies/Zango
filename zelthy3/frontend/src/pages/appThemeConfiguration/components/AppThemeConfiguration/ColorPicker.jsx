import { Menu, Transition } from '@headlessui/react';
import { get } from 'lodash';
import { Fragment, useState, useRef, useEffect } from 'react';
import { ChromePicker } from 'react-color';
import { usePopper } from 'react-popper';

export default function ColorPicker({ data }) {
	let { id, formik, label } = data;
	const [referenceElement, setReferenceElement] = useState(null);
	const [popperElement, setPopperElement] = useState(null);
	const { styles, attributes } = usePopper(referenceElement, popperElement, {
		placement: 'bottom-start',
	});
	const [width, setWidth] = useState(0);
	const [color, setColor] = useState(get(formik.values, id, '#ffffff'));
	const [opacity, setOpacity] = useState(data?.opacity || 100);
	const opacityContentRef = useRef(null);

	useEffect(() => {
		formik.setFieldValue(id, color);
	}, [color, opacity]);

	useEffect(() => {
		if (opacityContentRef.current) {
			setWidth(opacityContentRef.current.offsetWidth);
		}
	}, [opacity]);

	const handleOpacityChange = (value) => {
		let opacityValue = parseInt(value);
		if (opacityValue >= 0 && opacityValue <= 100) {
			setOpacity(opacityValue);
		} else if (opacityValue > 100) {
			setOpacity(100);
		} else {
			setOpacity(0);
		}
	};

	const handleChangeComplete = (color, event) => {
		setColor(color.hex);
	};

	return (
		<>
			<div className="flex flex-col gap-[4px]">
				<label
					htmlFor={id}
					className="font-lato text-form-xs font-semibold text-[#A3ABB1]"
				>
					{label}
				</label>
				<div className="flex w-full rounded-[6px] border border-[#DDE2E5]">
					<div className="relative flex w-full">
						<Menu
							as="div"
							className="relative inline-block flex w-full text-left"
						>
							<div className="flex w-full items-center">
								<Menu.Button
									className="flex w-full items-center gap-[12px] px-[16px] py-[13px]"
									ref={(ref) => setReferenceElement(ref)}
								>
									<div
										className={`h-[23px] w-[23px] rounded-[4px] border border-[#DDE2E5]`}
										style={{ backgroundColor: color }}
									></div>
									<span className="font-lato text-[14px] uppercase leading-[20px] tracking-[0.2px] text-[#212429]">
										{color ? color : ''}
									</span>
								</Menu.Button>
								{formik.touched[id] && formik.errors[id] ? (
									<div className="font-lato text-form-xs text-[#cc3300]">
										{formik.errors[id]}
									</div>
								) : null}
							</div>
							<Transition
								as={Fragment}
								enter="transition ease-out duration-100"
								enterFrom="transform opacity-0 scale-95"
								enterTo="transform opacity-100 scale-100"
								leave="transition ease-in duration-75"
								leaveFrom="transform opacity-100 scale-100"
								leaveTo="transform opacity-0 scale-95"
								// @ts-ignore
								ref={setPopperElement}
								style={styles['popper']}
								{...attributes['popper']}
							>
								<Menu.Items className="absolute z-20 mt-2 origin-top-right divide-y divide-gray-100 rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
									<div className="px-1 py-1 ">
										<Menu.Item>
											{({ active }) => (
												<ChromePicker
													className="!shadow-none"
													color={color}
													disableAlpha={true}
													onChangeComplete={handleChangeComplete}
												/>
											)}
										</Menu.Item>
									</div>
								</Menu.Items>
							</Transition>
						</Menu>
					</div>
				</div>
			</div>
		</>
	);
}
