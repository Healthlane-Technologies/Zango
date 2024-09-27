import { Fragment, useState, useRef } from 'react';
import { Menu, Transition } from '@headlessui/react';
import { countryCodeList } from '../../utils/countryCodes';
import { ReactComponent as DropdownIcon } from '../../assets/images/svg/down-arrow-icon.svg';

function classNames(...classes) {
	return classes.filter(Boolean).join(' ');
}

export default function CountryCodeSelector({ countryCode, setCountryCode }) {

	const targetElementRef = useRef(null);

	const handleMenuClick = () => {
		setTimeout(() => {
			if (targetElementRef.current) {
				targetElementRef.current.scrollIntoView({
					behavior: 'smooth', // You can use 'auto' or 'smooth' for scrolling behavior
					block: 'start', // You can use 'start', 'center', or 'end' for vertical alignment
					inline: 'nearest', // You can use 'start', 'center', or 'end' for horizontal alignment
				});
			}
		}, 10);
	};

	return (
		<Menu as="div" className="relative inline-block text-left">
			<Menu.Button
				className="inline-flex w-full items-center justify-center gap-[2px] rounded-[4px] rounded-r-[0] bg-white px-3 py-2 text-sm leading-8 text-gray-900"
				onClick={handleMenuClick}
			>
				{countryCode?.dial_code}
				<DropdownIcon />
			</Menu.Button>

			<Transition
				as={Fragment}
				enter="transition ease-out duration-100"
				enterFrom="transform opacity-0 scale-95"
				enterTo="transform opacity-100 scale-100"
				leave="transition ease-in duration-75"
				leaveFrom="transform opacity-100 scale-100"
				leaveTo="transform opacity-0 scale-95"
				ref={targetElementRef}
			>
				<Menu.Items className="absolute right-[-198px] z-10 mt-2 h-[40vh] w-64 origin-top-right overflow-auto rounded-[4px] border border-[#D4D4D4] bg-white">
					<div className="py-1">
						{countryCodeList.map((item) => {
							return (
								<Menu.Item key={item.name}>
									{({ active }) => (
										<div
											onClick={() => {setCountryCode(item)}}
											className={classNames(
												active ? 'bg-gray-100 text-gray-900' : 'text-gray-700',
												'block cursor-pointer px-4 py-2 text-sm hover:bg-[#F0F3F4]'
											)}
										>
											{item.name} ({item.dial_code})
										</div>
									)}
								</Menu.Item>
							);
						})}
					</div>
				</Menu.Items>
			</Transition>
		</Menu>
	);
}
