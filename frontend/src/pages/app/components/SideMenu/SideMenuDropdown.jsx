import { Menu, Transition } from '@headlessui/react';
import { Fragment, useState } from 'react';
import { usePopper } from 'react-popper';
import { NavLink, useLocation } from 'react-router-dom';
import { ReactComponent as SidemenuArrowIcon } from '../../../../assets/images/svg/sidemenu-arrow-icon.svg';

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
						<SidemenuArrowIcon className="absolute bottom-[2px] right-[2px]" />
					</div>
				</Menu.Button>
				<Transition
					as={Fragment}
					// @ts-ignore
					ref={(ref) => setPopperElement(ref)}
					style={styles['popper']}
					{...attributes['popper']}
				>
					<Menu.Items className="absolute right-0 top-[30px] w-[186px] origin-top-right rounded-[4px] bg-[#E1D6AE] shadow-table-menu focus:outline-none">
						<div className="flex flex-col gap-[6px] px-[20px] py-[12px]">
							{sublinks?.map(({ url, label, dataCy }) => {
								return (
									<Menu.Item key={label}>
										{({ active }) => (
											<NavLink
												to={url}
												data-cy={dataCy}
												className="flex flex-col items-center justify-center bg-transparent"
												children={({ isActive }) => {
													return (
														<div
															className={`${
																active ? '' : ''
															} relative flex w-full flex-col rounded-[2px]`}
														>
															{isActive ? (
																<span className="absolute left-[-8px] top-[6px] h-[4px] w-[4px] rounded bg-black"></span>
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
						</div>
					</Menu.Items>
				</Transition>
			</Menu>
		</div>
	);
}
