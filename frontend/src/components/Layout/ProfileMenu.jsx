import { Menu, Transition } from '@headlessui/react';
import { Fragment, useState } from 'react';
import { usePopper } from 'react-popper';
import { useSelector } from 'react-redux';
import { ReactComponent as ProfileDropdownIcon } from '../../assets/images/svg/profile-dropdown-icon.svg';
import { selectAppPanelInitialData } from '../../pages/platform/slice';

export default function ProfileMenu() {
	const appPanelInitialData = useSelector(selectAppPanelInitialData);
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
					ref={(ref) => setPopperElement(ref)}
					style={styles['popper']}
					{...attributes['popper']}
				>
					<Menu.Items className="absolute right-0 top-[30px] w-[186px] origin-top-right rounded-[4px] bg-white shadow-table-menu focus:outline-none">
						<div className="p-[4px]">
							<div className="flex w-full flex-col rounded-[2px] px-[12px] py-[8px]">
								<span className="text-start font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
									{appPanelInitialData?.user_logged_in?.name}
								</span>
								<span className="text-start font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#6C747D]">
									{appPanelInitialData?.user_logged_in?.email}
								</span>
							</div>
						</div>
						<hr></hr>
						<div className="p-[4px]">
							<Menu.Item>
								{({ active }) => (
									<a href="/auth/logout/">
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
