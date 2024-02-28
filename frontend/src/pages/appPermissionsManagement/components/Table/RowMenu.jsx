import { Menu, Transition } from '@headlessui/react';
import { Fragment, useState } from 'react';
import { usePopper } from 'react-popper';
import { useDispatch } from 'react-redux';
import { ReactComponent as TableRowKebabIcon } from '../../../../assets/images/svg/table-row-kebab-icon.svg';
import {
	openIsDeleteCustomPermissionModalOpen,
	openIsEditCustomPermissionModalOpen,
} from '../../slice';

export default function RowMenu({ className }) {
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

	const dispatch = useDispatch();

	const handleEditUserDetails = () => {
		dispatch(openIsEditCustomPermissionModalOpen());
	};

	const handleDeactivateUser = () => {
		dispatch(openIsDeleteCustomPermissionModalOpen());
	};

	return (
		<Menu as="div" className="relative flex">
			<Menu.Button
				className="flex w-full justify-center focus:outline-none"
				ref={(ref) => setReferenceElement(ref)}
			>
				<TableRowKebabIcon className="text-[#5048ED]" />
			</Menu.Button>
			<Transition
				as={Fragment}
				// @ts-ignore
				ref={(ref) => setPopperElement(ref)}
				style={styles['popper']}
				{...attributes['popper']}
			>
				<Menu.Items className="absolute top-[30px] right-0 w-[210px] origin-top-right rounded-[4px] bg-white shadow-table-menu focus:outline-none">
					<div className="p-[4px]">
						<Menu.Item>
							{({ active }) => (
								<button
									type="button"
									className="flex w-full"
									onClick={handleEditUserDetails}
								>
									<div
										className={`${
											active ? 'bg-[#F0F3F4]' : ''
										} flex w-full flex-col rounded-[2px] px-[12px] py-[8px]`}
									>
										<span className="text-start font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
											Edit Custom Permission
										</span>
										<span className="text-start font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#6C747D]">
											edit custom permission
										</span>
									</div>
								</button>
							)}
						</Menu.Item>
						<Menu.Item>
							{({ active }) => (
								<button
									type="button"
									className="flex  w-full"
									onClick={handleDeactivateUser}
								>
									<div
										className={`${
											active ? 'bg-[#F0F3F4]' : ''
										} flex w-full flex-col rounded-[2px] px-[12px] py-[8px]`}
									>
										<span className="text-start font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#AA2113]">
											Delete Custom Permission
										</span>
										<span className="text-start font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#6C747D]">
											this will delete the custom permission along with all the
											details of this permission
										</span>
									</div>
								</button>
							)}
						</Menu.Item>
					</div>
				</Menu.Items>
			</Transition>
		</Menu>
	);
}
