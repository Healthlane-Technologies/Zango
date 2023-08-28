import { Dialog, Transition } from '@headlessui/react';
import { Fragment, useState, useEffect } from 'react';

import { useField, Formik, FieldArray, Field, ErrorMessage } from 'formik';
import * as Yup from 'yup';
import { get } from 'lodash';
import { transformToFormDataOrder } from '../../../../utils/helper';
import useApi from '../../../../hooks/useApi';

import { useSelector, useDispatch } from 'react-redux';
import {
	closeIsDeactivateUserModalOpen,
	selectIsDeactivateUserModalOpen,
} from '../../slice';

import { ReactComponent as ModalCloseIcon } from '../../../../assets/images/svg/modal-close-icon.svg';
import { ReactComponent as DeactivateUserIcon } from '../../../../assets/images/svg/deactivate-user-icon.svg';

const DeactivateUserForm = ({ closeModal }) => {
	const triggerApi = useApi();
	let initialValues = {
		full_name: '',
		email: '',
		phone: '',
	};

	let validationSchema = Yup.object({
		full_name: Yup.string().required('Required'),
		email: Yup.string().email('Invalid email address').required('Required'),
		phone: Yup.string()
			.min(9, 'Must be 9 digits')
			.max(9, 'Must be 9 digits')
			.required('Required'),
	});

	let onSubmit = (values) => {
		let tempValues = values;
		if (tempValues['phone']) {
			tempValues['phone'] = '+91' + tempValues['phone'];
		}

		let dynamicFormData = transformToFormDataOrder(tempValues);

		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/generate-order/`,
				type: 'POST',
				loader: true,
				payload: dynamicFormData,
			});

			if (success && response) {
				closeModal();
			}
		};

		makeApiCall();
	};

	return (
		<Formik
			initialValues={initialValues}
			validationSchema={validationSchema}
			onSubmit={onSubmit}
		>
			{(formik) => {
				return (
					<form
						className="complete-hidden-scroll-style flex grow flex-col gap-4 overflow-y-auto"
						onSubmit={formik.handleSubmit}
					>
						<div className="flex grow flex-col gap-[16px]">
							<div className="flex grow flex-col items-center justify-center gap-[16px]">
								<DeactivateUserIcon />
								<p className="max-w-[201px] text-center font-lato text-[16px] leading-[24px] tracking-[0.2px] text-[#212429]">
									Sure you want to deactivate Darrell Steward’s profile?
								</p>
							</div>
							<p className="flex flex-col font-lato text-[14px] leading-[20px] tracking-[0.2px] text-[#212429]">
								<span>Note:</span>
								<span>
									This action will not delete the user’s profile and can be
									reactivated anytime later.
								</span>
							</p>
						</div>
						<div className="sticky bottom-0 flex flex-col gap-[8px] bg-[#ffffff] pt-[24px] font-lato text-[#696969]">
							<button
								type="submit"
								className="flex w-full items-center justify-center rounded-[4px] bg-danger-red px-[16px] py-[10px] font-lato text-[14px] font-bold leading-[20px] text-white disabled:opacity-[0.38]"
								// disabled={!(formik.isValid && formik.dirty)}
							>
								<span>Deactivate User</span>
							</button>
						</div>
					</form>
				);
			}}
		</Formik>
	);
};

export default function DeactivateUserModal() {
	const isDeactivateUserModalOpen = useSelector(
		selectIsDeactivateUserModalOpen
	);
	const dispatch = useDispatch();

	function closeModal() {
		dispatch(closeIsDeactivateUserModalOpen());
	}

	return (
		<>
			<Transition appear show={isDeactivateUserModalOpen} as={Fragment}>
				<Dialog as="div" className="relative z-10" onClose={closeModal}>
					<Transition.Child
						as={Fragment}
						enter="ease-out duration-300"
						enterFrom="opacity-0"
						enterTo="opacity-100"
						leave="ease-in duration-200"
						leaveFrom="opacity-100"
						leaveTo="opacity-0"
					>
						<div className="fixed inset-0 bg-black bg-opacity-[.67]" />
					</Transition.Child>

					<div className="fixed inset-0 overflow-y-auto">
						<div className="flex h-screen max-h-screen min-h-full grow items-center justify-center text-center md:justify-end">
							<Transition.Child
								as={Fragment}
								enter="ease-out duration-300"
								enterFrom="opacity-0 scale-95"
								enterTo="opacity-100 scale-100"
								leave="ease-in duration-200"
								leaveFrom="opacity-100 scale-100"
								leaveTo="opacity-0 scale-95"
							>
								<Dialog.Panel className="relative flex h-screen max-h-screen min-h-full w-full max-w-[498px] transform flex-col gap-[32px] overflow-hidden bg-white px-[24px] pt-[52px] pb-[40px] text-left align-middle shadow-xl transition-all md:pl-[32px] md:pr-[72px] md:pt-[32px]">
									<div className="flex justify-end md:absolute md:top-0 md:right-0">
										<button
											type="button"
											className="flex justify-end focus:outline-none md:absolute md:top-[16px] md:right-[16px]"
											onClick={closeModal}
										>
											<ModalCloseIcon />
										</button>
									</div>
									<Dialog.Title as="div" className="flex flex-col gap-2">
										<div className="flex flex-col gap-[2px]">
											<h4 className="font-source-sans-pro text-[22px] font-semibold leading-[28px]">
												Deactivate Darrel’s Profile
											</h4>
										</div>
									</Dialog.Title>
									<DeactivateUserForm closeModal={closeModal} />
								</Dialog.Panel>
							</Transition.Child>
						</div>
					</div>
				</Dialog>
			</Transition>
		</>
	);
}
