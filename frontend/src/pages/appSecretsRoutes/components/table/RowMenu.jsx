import { Menu, Transition } from '@headlessui/react';
import { Fragment, useState } from 'react';
import toast from 'react-hot-toast';
import { usePopper } from 'react-popper';
import { useDispatch, useSelector } from 'react-redux';
import { ReactComponent as TableRowKebabIcon } from '../../../../assets/images/svg/table-row-kebab-icon.svg';
import Notifications from '../../../../components/Notifications';
import {
	selectAppSecretsFormData,
	setAppSecretsFormData,
	setEditSecretModalOpen,
	toggleRerenderPage,
} from '../../slice/Index';
import useApi from '../../../../hooks/useApi';
import { useParams } from 'react-router-dom';
// import {
// 	openIsActivateUserModalOpen,
// 	openIsDeactivateUserModalOpen,
// 	openIsEditUserDetailModalOpen,
// 	openIsResetPasswordModalOpen,
// } from '../../slice';

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
	const appSecretsFormData = useSelector(selectAppSecretsFormData);

	const triggerApi = useApi();
	let { appId } = useParams();

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

	const handleEditClick = () => {
		dispatch(setEditSecretModalOpen(true));
		dispatch(setAppSecretsFormData(rowData));

		// Open your modal here
	};

	const handleDelete = () => {
		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/secrets/?secret_id=${rowData?.id}`,
				type: 'DELETE',
				loader: true,
			});

			if (success) {
				dispatch(toggleRerenderPage());
			}
		};

		makeApiCall();
	};

	// const handleEditUserDetails = () => {
	// 	dispatch(openIsEditUserDetailModalOpen(rowData));
	// };

	// const handleDeactivateUser = () => {
	// 	dispatch(openIsDeactivateUserModalOpen(rowData));
	// };

	// const handleActivateUser = () => {
	// 	dispatch(openIsActivateUserModalOpen(rowData));
	// };

	// const handleResetUserPassword = () => {
	// 	dispatch(openIsResetPasswordModalOpen(rowData));
	// };

	const handleStatusChange = async (status) => {
		const payload = new FormData()

		payload.append('is_active', status);
		
		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/secrets/?secret_id=${rowData?.id}`,
			type: 'PUT',
			payload: payload,
			loader: true,
		});

		if (success) {
			dispatch(toggleRerenderPage());
		}
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
									data-cy="secrets_mark_active_button"
									type="button"
									className="flex w-full"
									onClick={handleEditClick}
								>
									<div
										className={`${
											active ? 'bg-[#F0F3F4]' : ''
										} flex w-full flex-col rounded-[2px] px-[12px] py-[8px]`}
									>
										<span className="text-start font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
											Edit
										</span>
										<span className="text-start font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#6C747D]">
											Edit your secret
										</span>
									</div>
								</button>
							)}
						</Menu.Item>

						{rowData?.is_active ? (
							<Menu.Item>
								{({ active }) => (
									<button
										data-cy="secrets_mark_inactive_button"
										type="button"
										className="flex w-full"
										onClick={() => handleStatusChange(false)}
									>
										<div
											className={`${
												active ? 'bg-[#F0F3F4]' : ''
											} flex w-full flex-col rounded-[2px] px-[12px] py-[8px]`}
										>
											<span className="text-start font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#AA2113]">
												Mark Inactive
											</span>
											<span className="text-start font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#6C747D]">
												disable secret access to the app
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
										className="flex w-full"
										onClick={() => handleStatusChange(true)}
									>
										<div
											className={`${
												active ? 'bg-[#F0F3F4]' : ''
											} flex w-full flex-col rounded-[2px] px-[12px] py-[8px]`}
										>
											<span className="text-start font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#229470]">
												Make Active
											</span>
											<span className="text-start font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#6C747D]">
												enable secret access to the app
											</span>
										</div>
									</button>
								)}
							</Menu.Item>
						)}

						<Menu.Item>
							{({ active }) => (
								<button
									data-cy="delete_secret_button"
									type="button"
									onClick={handleDelete}
									className="flex  w-full"
								>
									<div
										className={`${
											active ? 'bg-[#F0F3F4]' : ''
										} flex w-full flex-col rounded-[2px] px-[12px] py-[8px]`}
									>
										<span className="text-start font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#AA2113]">
											Delete
										</span>
										<span className="text-start font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#6C747D]">
											this will remove the secret
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
