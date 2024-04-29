import { usePopper } from 'react-popper';
import { Fragment } from 'react';
import { Menu, Transition } from '@headlessui/react';
import { ReactComponent as EachSideMenuIcon } from '../../../../assets/images/svg/table-row-kebab-icon.svg';
import { ReactComponent as SidemenuArrowIcon } from '../../../../assets/images/svg/sidemenu-arrow-icon.svg';
import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';

export default function SideMenuDropdown({ label, Icon, sublinks }) {
	const location = useLocation();
	let pathnameArray = location.pathname.split('/').filter((each) => each);
	let allSublinks = sublinks
		?.map(({ url }) => url.split('/').filter((each) => each))
		.flat(Infinity);
	let isCurrentPage = allSublinks.some(
		(eachLink) => pathnameArray.indexOf(eachLink) > -1
	);
	const [referenceElement, setReferenceElement] = useState(null);
	const [popperElement, setPopperElement] = useState(null);
	const { styles, attributes } = usePopper(referenceElement, popperElement, {
		placement: 'right-start',
		modifiers: [
			{
				name: 'offset',
				options: {
					offset: [20, 0],
				},
			},
		],
	});

	return (
		<div className="relative">
			<Menu as="div" className="relative flex">
				<Menu.Button
					className="flex w-full justify-center focus:outline-none"
					ref={(ref) => setReferenceElement(ref)}
				>
					<div
						className={`flex w-full cursor-pointer flex-col items-center justify-center gap-[4px] px-[13px] py-[10px] hover:bg-[#d3c9a4] ${
							isCurrentPage ? 'bg-[#d3c9a4]' : 'bg-transparent'
						}`}
					>
						<Icon />
						<span className="text-center font-lato text-[10px] font-bold leading-[12px] tracking-[0.2px] text-[#26210F]">
							{label}
						</span>
						<SidemenuArrowIcon className="absolute right-[2px] bottom-[2px]" />
					</div>
				</Menu.Button>
				<Transition
					as={Fragment}
					// @ts-ignore
					ref={(ref) => setPopperElement(ref)}
					style={styles['popper']}
					{...attributes['popper']}
				>
					<Menu.Items className="absolute top-[30px] right-0 w-[186px] origin-top-right rounded-[4px] bg-[#E1D6AE] shadow-table-menu focus:outline-none">
						<div className="flex flex-col gap-[6px] px-[20px] py-[12px]">
							{sublinks?.map(({ url, label }) => {
								return (
									<Menu.Item key={label}>
										{({ active }) => (
											<NavLink
												to={url}
												className="flex flex-col items-center justify-center bg-transparent"
												children={({ isActive }) => {
													return (
														<div
															className={`${
																active ? '' : ''
															} relative flex w-full flex-col rounded-[2px]`}
														>
															{isActive ? (
																<span className="absolute top-[6px] left-[-8px] h-[4px] w-[4px] rounded bg-black"></span>
															) : null}
															<span className="text-start font-lato text-[11px] font-bold leading-[16px] tracking-[0.2px] text-[#212429]">
																{label}
															</span>
														</div>
													);
												}}
											/>
										)}
									</Menu.Item>
								);
							})}

							{/* <Menu.Item>
								{({ active }) => (
									<NavLink
										to={`app-settings/app-theme-configuration/`}
										className="flex flex-col items-center justify-center bg-transparent"
										children={({ isActive }) => {
											return (
												<div
													className={`${
														active ? '' : ''
													} relative flex w-full flex-col rounded-[2px]`}
												>
													{isActive ? (
														<span className="absolute top-[6px] left-[-8px] h-[4px] w-[4px] rounded bg-black"></span>
													) : null}
													<span className="text-start font-lato text-[11px] font-bold leading-[16px] tracking-[0.2px] text-[#212429]">
														App Theme Configuration
													</span>
												</div>
											);
										}}
									/>
								)}
							</Menu.Item> */}
						</div>
					</Menu.Items>
				</Transition>
			</Menu>
		</div>
	);
}
