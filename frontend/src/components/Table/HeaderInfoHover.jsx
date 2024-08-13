import { Menu, Transition } from '@headlessui/react';
import { Fragment, useState } from 'react';
import { usePopper } from 'react-popper';
import { ReactComponent as InfoIcon } from '../../../src/assets/images/svg/info-icon.svg';

export default function HeaderInfoHover({ message }) {
	const [referenceElement, setReferenceElement] = useState(null);
	const [popperElement, setPopperElement] = useState(null);
	const [isOpen, setIsOpen] = useState(false);

	const { styles, attributes } = usePopper(referenceElement, popperElement, {
		placement: 'bottom-end',
		modifiers: [
			{
				name: 'offset',
				options: {
					offset: [460, 2],
				},
			},
		],
	});

	return (
		<div
			className="relative"
			onMouseEnter={() => setIsOpen(true)}
			onMouseLeave={() => setIsOpen(false)}
		>
			<Menu as="div" className="relative flex">
				<Transition
					as={Fragment}
					ref={(ref) => setPopperElement(ref)}
					style={styles.popper}
					{...attributes.popper}
					show={isOpen}
				>
					<Menu.Items className="absolute bottom-[30px] right-0 z-20 min-w-[186px] origin-bottom-right rounded-[4px] bg-white shadow-table-menu focus:outline-none">
						<div className="p-[4px]">
							<Menu.Item>
								{({ active }) => (
									<div
										className={`${
											active ? 'bg-white' : ''
										} flex w-full max-w-fit flex-col rounded-[2px] px-[12px] py-[8px]`}
									>
										<span className="text-wrap text-start font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#6C747D]">
											{message}
										</span>
									</div>
								)}
							</Menu.Item>
						</div>
					</Menu.Items>
				</Transition>
				<Menu.Button
					className="relative z-10 flex w-full justify-center focus:outline-none"
					ref={(ref) => setReferenceElement(ref)}
				>
					<InfoIcon className="h-[16px] min-h-[16px] w-[16px] min-w-[16px] " />
				</Menu.Button>
			</Menu>
		</div>
	);
}
