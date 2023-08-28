import { Dialog, Transition } from '@headlessui/react';
import { Fragment, useState, useEffect } from 'react';

import { useField, Formik, FieldArray, Field, ErrorMessage } from 'formik';
import * as Yup from 'yup';
import { get } from 'lodash';
import { transformToFormDataOrder } from '../../../../utils/helper';
import useApi from '../../../../hooks/useApi';

import { useSelector, useDispatch } from 'react-redux';
import {
	closeIsEditUserDetailModalOpen,
	selectIsEditUserDetailModalOpen,
} from '../../slice';

import { ReactComponent as ModalCloseIcon } from '../../../../assets/images/svg/modal-close-icon.svg';

const EditUserDetailsForm = ({ closeModal }) => {
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
							<div className="flex flex-col gap-[4px]">
								<label
									htmlFor="full_name"
									className="font-lato text-form-xs font-semibold text-[#A3ABB1]"
								>
									Full Name
								</label>
								<input
									id="full_name"
									name="full_name"
									type="text"
									onChange={formik.handleChange}
									onBlur={formik.handleBlur}
									value={formik.values.full_name}
									className="rounded-[6px] border border-[#DDE2E5] px-[16px] py-[14px] font-lato placeholder:text-[#9A9A9A] hover:outline-0 focus:outline-0"
									placeholder="Enter full name of the user"
								/>
								{formik.touched.full_name && formik.errors.full_name ? (
									<div className="font-lato text-form-xs text-[#cc3300]">
										{formik.errors.full_name}
									</div>
								) : null}
							</div>
							<div className="flex flex-col gap-[4px]">
								<label
									htmlFor="email"
									className="font-lato text-form-xs font-semibold text-[#A3ABB1]"
								>
									Email
								</label>
								<input
									id="email"
									name="email"
									type="text"
									onChange={formik.handleChange}
									onBlur={formik.handleBlur}
									value={formik.values.email}
									className="rounded-[6px] border border-[#DDE2E5] px-[16px] py-[14px] font-lato placeholder:text-[#9A9A9A] hover:outline-0 focus:outline-0"
									placeholder="Enter"
								/>
								{formik.touched.email && formik.errors.email ? (
									<div className="font-lato text-form-xs text-[#cc3300]">
										{formik.errors.email}
									</div>
								) : null}
							</div>
							<div className="flex flex-col gap-[4px]">
								<label
									htmlFor="phone"
									className="font-lato text-form-xs font-semibold text-[#A3ABB1]"
								>
									Phone (optional)
								</label>
								<div className="flex gap-[12px] rounded-[6px] border border-[#DDE2E5] px-[12px] py-[14px]">
									<span className="font-lato text-[#6C747D]">+91</span>
									<input
										id="phone"
										name="phone"
										type="number"
										onChange={formik.handleChange}
										onBlur={formik.handleBlur}
										value={formik.values.phone}
										className="font-lato placeholder:text-[#9A9A9A] hover:outline-0 focus:outline-0"
										placeholder="000000000"
									/>
								</div>
								{formik.touched.phone && formik.errors.phone ? (
									<div className="font-lato text-form-xs text-[#cc3300]">
										{formik.errors.phone}
									</div>
								) : null}
							</div>
						</div>
						<div className="sticky bottom-0 flex flex-col gap-[8px] bg-[#ffffff] pt-[24px] font-lato text-[#696969]">
							<button
								type="submit"
								className="flex w-full items-center justify-center rounded-[4px] bg-primary px-[16px] py-[10px] font-lato text-[14px] font-bold leading-[20px] text-white disabled:opacity-[0.38]"
								disabled={!(formik.isValid && formik.dirty)}
							>
								<span>Save</span>
							</button>
						</div>
					</form>
				);
			}}
		</Formik>
	);
};

export default function EditUserDetailsModal() {
	const isEditUserDetailModalOpen = useSelector(
		selectIsEditUserDetailModalOpen
	);
	const dispatch = useDispatch();

	function closeModal() {
		dispatch(closeIsEditUserDetailModalOpen());
	}

	return (
		<>
			<Transition appear show={isEditUserDetailModalOpen} as={Fragment}>
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
												Edit User Details
											</h4>
										</div>
									</Dialog.Title>
									<EditUserDetailsForm closeModal={closeModal} />
								</Dialog.Panel>
							</Transition.Child>
						</div>
					</div>
				</Dialog>
			</Transition>
		</>
	);
}
