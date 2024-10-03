import { Menu, Transition } from '@headlessui/react';
import { Fragment, useState } from 'react';
import { usePopper } from 'react-popper';
import { useDispatch } from 'react-redux';
import { ReactComponent as TableRowKebabIcon } from '../../../../assets/images/svg/table-row-kebab-icon.svg';
import {
	openIsConfigurePackageModalOpen,
	openIsInstallPackageModalOpen,
} from '../../slice';

export default function RowMenu({ rowData }) {
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

	const handleConfiurePackage = () => {
		dispatch(openIsConfigurePackageModalOpen(rowData));
	};

	const handleInstallPackage = () => {
		dispatch(openIsInstallPackageModalOpen(rowData));
	};

	if(rowData.config_url==null && rowData.status?.toLowerCase()=='installed'){
		return null;
	}

	return (
		<Menu as="div" className="relative flex">
			<Menu.Button
				data-cy="three_dots_menu"
				className="flex w-full justify-center focus:outline-none"
				ref={(ref) => setReferenceElement(ref)}
			>
				<TableRowKebabIcon className="text-[#5048ED]" />
			</Menu.Button>
			<Transition
				as={Fragment}
				ref={(ref) => setPopperElement(ref)}
				style={styles['popper']}
				{...attributes['popper']}
			>
				<Menu.Items className="absolute right-0 top-[30px] w-[186px] origin-top-right rounded-[4px] bg-white shadow-table-menu focus:outline-none">
					<div className="p-[4px]">
						{rowData?.status === 'Installed' ? null : (
							<Menu.Item>
								{({ active }) => (
									<button
										data-cy="install_package"
										type="button"
										className="flex w-full"
										onClick={handleInstallPackage}
									>
										<div
											className={`${
												active ? 'bg-[#F0F3F4]' : ''
											} flex w-full flex-col rounded-[2px] px-[12px] py-[8px]`}
										>
											<span className="text-start font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
												Install Package
											</span>
										</div>
									</button>
								)}
							</Menu.Item>
						)}

						{rowData?.status === 'Installed' ? (
							<Menu.Item>
								{({ active }) => (
									<button
										data-cy="configure_package_button"
										type="button"
										className="flex w-full"
										onClick={handleConfiurePackage}
									>
										<div
											className={`${
												active ? 'bg-[#F0F3F4]' : ''
											} flex w-full flex-col rounded-[2px] px-[12px] py-[8px]`}
										>
											<span className="text-start font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
												Configure Package
											</span>
										</div>
									</button>
								)}
							</Menu.Item>
						) : null}
					</div>
				</Menu.Items>
			</Transition>
		</Menu>
	);
}
