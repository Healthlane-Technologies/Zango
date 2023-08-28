import { Fragment } from 'react';
import { Menu, Transition } from '@headlessui/react';
import { ReactComponent as ProfileDropdownIcon } from '../../../../assets/images/svg/profile-dropdown-icon.svg';

export default function ProfileMenu() {
	return (
		<div className="relative">
			<Menu as="div" className="relative flex">
				<Menu.Button className="flex w-full justify-center focus:outline-none">
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
				>
					<Menu.Items className="absolute top-[30px] right-0 w-[129px] origin-top-right bg-white shadow-dropdown focus:outline-none">
						<div className="py-[16px]">
							<Menu.Item>
								{({ active }) => (
									<a href={`/logout`}>
										<span
											className={`${
												active ? 'bg-[#F7F7F7] text-black' : 'text-[#696969]'
											} group flex w-full items-center px-[24px] py-[8px] font-invention-app text-profile-menu-base`}
										>
											Log Out
										</span>
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
