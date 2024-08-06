import { Menu, Transition } from '@headlessui/react';
import { Fragment, useState } from 'react';
import toast from 'react-hot-toast';
import { usePopper } from 'react-popper';
import { useDispatch } from 'react-redux';
import { ReactComponent as TableRowKebabIcon } from '../../../../assets/images/svg/table-row-kebab-icon.svg';
import Notifications from '../../../../components/Notifications';
import {
	openIsActivateUserModalOpen,
	openIsDeactivateUserModalOpen,
	openIsEditUserDetailModalOpen,
	openIsResetPasswordModalOpen,
} from '../../slice';

const notify = () =>
	toast.custom(
		(t) => (
			<Notifications
				type="success"
				toastRef={t}
				title={'Reset Password Link Sent'}
				description={
					'A reset password link has been shared with Darrell Steward via email.'
				}
			/>
		),
		{
			duration: 5000,
			position: 'bottom-left',
		}
	);

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

	const handleEditUserDetails = () => {
		dispatch(openIsEditUserDetailModalOpen(rowData));
	};

	const handleDeactivateUser = () => {
		dispatch(openIsDeactivateUserModalOpen(rowData));
	};

	const handleActivateUser = () => {
		dispatch(openIsActivateUserModalOpen(rowData));
	};

	const handleResetUserPassword = () => {
		dispatch(openIsResetPasswordModalOpen(rowData));
	};

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
				// @ts-ignore
				ref={(ref) => setPopperElement(ref)}
				style={styles['popper']}
				{...attributes['popper']}
			>
				<Menu.Items className="absolute right-0 top-[30px] w-[186px] origin-top-right rounded-[4px] bg-white shadow-table-menu focus:outline-none">
					<div className="p-[4px]">
						<Menu.Item>
							{({ active }) => (
								<button
									data-cy="edit_user_details_button"
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
											Edit User Details
										</span>
										<span className="text-start font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#6C747D]">
											name, role access.
										</span>
									</div>
								</button>
							)}
						</Menu.Item>
						<Menu.Item>
							{({ active }) => (
								<button
									data-cy="reset_password_button"
									type="button"
									onClick={handleResetUserPassword}
									className="flex  w-full"
								>
									<div
										className={`${
											active ? 'bg-[#F0F3F4]' : ''
										} flex w-full flex-col rounded-[2px] px-[12px] py-[8px]`}
									>
										<span className="text-start font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
											Reset Password
										</span>
										<span className="text-start font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#6C747D]">
											if there is any description
										</span>
									</div>
								</button>
							)}
						</Menu.Item>

						{rowData?.is_active ? (
							<Menu.Item>
								{({ active }) => (
									<button
										data-cy="deactivate_user_button"
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
												Deactivate User
											</span>
											<span className="text-start font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#6C747D]">
												this will not delete the user, but only deactivate them
											</span>
										</div>
									</button>
								)}
							</Menu.Item>
						) : (
							<Menu.Item>
								{({ active }) => (
									<button
										data-cy="activate_user_button"
										type="button"
										className="flex  w-full"
										onClick={handleActivateUser}
									>
										<div
											className={`${
												active ? 'bg-[#F0F3F4]' : ''
											} flex w-full flex-col rounded-[2px] px-[12px] py-[8px]`}
										>
											<span className="text-start font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#229470]">
												Activate User
											</span>
											<span className="text-start font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#6C747D]">
												this will enable it
											</span>
										</div>
									</button>
								)}
							</Menu.Item>
						)}
					</div>
				</Menu.Items>
			</Transition>
		</Menu>
	);
}
