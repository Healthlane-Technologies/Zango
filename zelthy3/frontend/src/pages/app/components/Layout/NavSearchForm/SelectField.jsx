import { usePopper } from 'react-popper';
import { Fragment } from 'react';
import { Menu, Transition } from '@headlessui/react';
import { ReactComponent as NavSearchDownArrowIcon } from '../../../../../assets/images/svg/nav-select-down-arrow.svg';
import { useState } from 'react';
import { NavLink } from 'react-router-dom';

export default function SelectField({ label }) {
	const [referenceElement, setReferenceElement] = useState(null);
	const [popperElement, setPopperElement] = useState(null);
	const { styles, attributes } = usePopper(referenceElement, popperElement, {
		placement: 'top-start',
	});

	return (
		<div className="relative">
			<Menu as="div" className="relative flex w-[198px]">
				<Menu.Button
					className="flex w-full items-center gap-[12px] rounded-r-[4px] border-l border-l-[#DDE2E5] bg-[#F0F3F4] py-[6px] px-[16px] hover:outline-0 focus:outline-0"
					ref={(ref) => setReferenceElement(ref)}
				>
					<span
						className={`block w-[80%] truncate bg-transparent text-left font-lato text-sm font-bold tracking-[0.2px] text-[#212429] outline-0  ring-0 placeholder:text-[#6C747D] `}
					>
						Apps
					</span>
					<span className="pointer-events-none absolute inset-y-0 right-[24px] flex items-center">
						<NavSearchDownArrowIcon aria-hidden="true" />
					</span>
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
					<Menu.Items className="absolute z-[1] mt-[-32px] h-fit max-h-96 w-full overflow-y-auto rounded-[4px] bg-[#495057] font-lato text-base focus:outline-none sm:text-sm">
						<div className="relative">
							<div className="flex w-full items-center gap-[12px] rounded-r-[4px] border-l border-[#495057] bg-[#495057] py-[6px] px-[16px] hover:outline-0 focus:outline-0">
								<span
									className={`block truncate bg-transparent text-left font-lato text-sm  font-bold tracking-[0.2px] text-[#FFFFFF] outline-0 ring-0 placeholder:text-[#6C747D] `}
								>
									Apps
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
							<Menu.Item>
								{({ active }) => (
									<NavLink
										exact
										to={`/platform/apps`}
										className="relative flex items-center px-[16px] py-[4px]"
										children={({ isActive }) => {
											return (
												<div
													className={`${
														active ? '' : ''
													} relative flex w-full flex-col rounded-[2px]`}
												>
													<span
														className={`block font-lato text-[#FFFFFF] ${
															isActive ? 'font-bold' : ''
														}`}
													>
														Apps
													</span>
												</div>
											);
										}}
									/>
								)}
							</Menu.Item>
							<Menu.Item>
								{({ active }) => (
									<NavLink
										exact
										to={`/platform/user-managements`}
										className="relative flex items-center px-[16px] py-[4px]"
										children={({ isActive }) => {
											return (
												<div
													className={`${
														active ? '' : ''
													} relative flex w-full flex-col rounded-[2px]`}
												>
													<span
														className={`block font-lato text-[#FFFFFF] ${
															isActive ? 'font-bold' : ''
														}`}
													>
														User Management
													</span>
												</div>
											);
										}}
									/>
								)}
							</Menu.Item>
						</div>
					</Menu.Items>
				</Transition>
			</Menu>
		</div>
	);
}
