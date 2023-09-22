import { Menu, Transition } from '@headlessui/react';
import { Fragment, useState } from 'react';
import { usePopper } from 'react-popper';
import { ReactComponent as ProfileDropdownIcon } from '../../../../assets/images/svg/profile-dropdown-icon.svg';

export default function ProfileMenu() {
	const [referenceElement, setReferenceElement] = useState(null);
	const [popperElement, setPopperElement] = useState(null);
	const { styles, attributes } = usePopper(referenceElement, popperElement, {
		placement: 'bottom-end',
		modifiers: [
			{
				name: 'offset',
				options: {
					offset: [16, 8],
				},
			},
		],
	});

	return (
		<div className="relativ z-10">
			<Menu as="div" className="relative flex">
				<Menu.Button
					className="flex w-full justify-center focus:outline-none"
					ref={(ref) => setReferenceElement(ref)}
				>
					<ProfileDropdownIcon />
				</Menu.Button>
				<Transition
					as={Fragment}
					enter="transition ease-out duration-100"
					enterFrom="transform opacity-0 scale-95"
					enterTo="transform opacity-100 scale-100"
					leave="transition ease-in duration-75"
					leaveFrom="transform opacity-100 scale-100"
					leaveTo="transform opacity-0 scale-95"
					// @ts-ignore
					ref={(ref) => setPopperElement(ref)}
					style={styles['popper']}
					{...attributes['popper']}
				>
					<Menu.Items className="absolute top-[30px] right-0 w-[186px] origin-top-right rounded-[4px] bg-white shadow-table-menu focus:outline-none">
						<div className="p-[4px]">
							<div className="flex w-full flex-col rounded-[2px] px-[12px] py-[8px]">
								<span className="text-start font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
									User Name
								</span>
								<span className="text-start font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#6C747D]">
									Description
								</span>
							</div>
						</div>
						<hr></hr>
						<div className="p-[4px]">
							<Menu.Item>
								{({ active }) => (
									<a href="/admin/logout/">
										<div
											className={`${
												active ? 'bg-[#F0F3F4]' : ''
											} flex w-full flex-col rounded-[2px] px-[12px] py-[8px]`}
										>
											<span className="text-start font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
												Log Out
											</span>
											<span className="text-start font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#6C747D]">
												It will logout user.
											</span>
										</div>
									</a>
								)}
							</Menu.Item>
						</div>
					</Menu.Items>
				</Transition>
			</Menu>
		</div>
	);
}
