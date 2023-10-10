import { Menu, Transition } from '@headlessui/react';
import { Fragment, useState } from 'react';
import { usePopper } from 'react-popper';
import { NavLink } from 'react-router-dom';
import { ReactComponent as NavSearchDownArrowIcon } from '../../../../../assets/images/svg/nav-select-down-arrow.svg';
import { ReactComponent as SelectDynamicCheckIcon } from '../../../../../assets/images/svg/select-dynamic-check-icon.svg';

export default function SelectField({ label }) {
	const [referenceElement, setReferenceElement] = useState(null);
	const [popperElement, setPopperElement] = useState(null);
	const { styles, attributes } = usePopper(referenceElement, popperElement, {
		placement: 'top-start',
		modifiers: [
			{
				name: 'offset',
				options: {
					offset: [0, -32],
				},
			},
		],
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
						User Management
					</span>
					<span className="pointer-events-none absolute inset-y-0 right-[24px] flex items-center">
						<NavSearchDownArrowIcon aria-hidden="true" />
					</span>
				</Menu.Button>
				<Transition
					as={Fragment}
					// @ts-ignore
					ref={(ref) => setPopperElement(ref)}
					style={styles['popper']}
					{...attributes['popper']}
				>
					<Menu.Items className="absolute z-[1] h-fit max-h-96 w-full overflow-y-auto rounded-[4px] bg-[#495057] font-lato text-base focus:outline-none sm:text-sm">
						<div className="relative">
							<div className="flex w-full items-center gap-[12px] rounded-r-[4px] border-l border-[#495057] bg-[#495057] py-[6px] px-[16px] hover:outline-0 focus:outline-0">
								<span
									className={`block truncate bg-transparent text-left font-lato text-sm  font-bold tracking-[0.2px] text-[#FFFFFF] outline-0 ring-0 placeholder:text-[#6C747D] `}
								>
									User Management
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
										exact="true"
										to={`/platform/apps`}
										className="relative flex items-center px-[16px] py-[4px]"
										children={({ isActive }) => {
											return (
												<div
													className={`${
														active ? '' : ''
													} relative flex w-full flex-col rounded-[2px]`}
												>
													<div className="flex gap-[12px]">
														<div className="min-w-[12px]">
															<SelectDynamicCheckIcon
																className={`${
																	isActive ? 'text-[#FFFFFF]' : 'text-[#495057]'
																}`}
															/>
														</div>
														<span
															className={`block font-lato text-[#FFFFFF] ${
																isActive ? 'font-bold' : ''
															}`}
														>
															Apps
														</span>
													</div>
												</div>
											);
										}}
									/>
								)}
							</Menu.Item>
							<Menu.Item>
								{({ active }) => (
									<NavLink
										exact="true"
										to={`/platform/user-managements`}
										className="relative flex items-center px-[16px] py-[4px]"
										children={({ isActive }) => {
											return (
												<div
													className={`${
														active ? '' : ''
													} relative flex w-full flex-col rounded-[2px]`}
												>
													<div className="flex gap-[12px]">
														<div className="min-w-[12px]">
															<SelectDynamicCheckIcon
																className={`${
																	isActive ? 'text-[#FFFFFF]' : 'text-[#495057]'
																}`}
															/>
														</div>
														<span
															className={`block font-lato text-[#FFFFFF] ${
																isActive ? 'font-bold' : ''
															}`}
														>
															User Management
														</span>
													</div>
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
