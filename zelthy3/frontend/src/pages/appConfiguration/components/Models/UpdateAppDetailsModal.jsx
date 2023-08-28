import { Dialog, Transition } from '@headlessui/react';
import { Fragment, useState, useEffect } from 'react';

import { useField, Formik, FieldArray, Field, ErrorMessage } from 'formik';
import * as Yup from 'yup';
import { get } from 'lodash';
import { transformToFormDataOrder } from '../../../../utils/helper';
import useApi from '../../../../hooks/useApi';

import { useSelector, useDispatch } from 'react-redux';
import {
	closeIsUpdateAppDetailsModalOpen,
	selectIsUpdateAppDetailsModalOpen,
} from '../../slice';

import { ReactComponent as ModalCloseIcon } from '../../../../assets/images/svg/modal-close-icon.svg';
import { ReactComponent as DeleteIcon } from '../../../../assets/images/svg/delete-icon.svg';
import { ReactComponent as UploadIcon } from '../../../../assets/images/svg/upload-icon.svg';
import { ReactComponent as UploadCloseIcon } from '../../../../assets/images/svg/upload-close-icon.svg';

import shortid from 'shortid';
import FileUpload from '../../../../components/Form/FileUpload';

const UpdateAppDetailsForm = ({ closeModal }) => {
	const triggerApi = useApi();
	let initialValues = {
		app_name: '',
		description: '',
		logo: '',
		fav_icon: '',
		domain: [],
		domains: [''],
		time_zome: '',
		date_time_format: '',
	};

	let validationSchema = Yup.object({
		app_name: Yup.string().required('Required'),
		// domains: Yup.array().of(Yup.string().required('Required')),
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
						<div className="flex grow flex-col gap-[16px] pr-[64px]">
							<div className="flex flex-col gap-[4px]">
								<label
									htmlFor="app_name"
									className="font-lato text-form-xs font-semibold text-[#A3ABB1]"
								>
									Full Name
								</label>
								<input
									id="app_name"
									name="app_name"
									type="text"
									onChange={formik.handleChange}
									onBlur={formik.handleBlur}
									value={formik.values.app_name}
									className="rounded-[6px] border border-[#DDE2E5] px-[16px] py-[14px] font-lato placeholder:text-[#9A9A9A] hover:outline-0 focus:outline-0"
									placeholder="Enter"
								/>
								{formik.touched.app_name && formik.errors.app_name ? (
									<div className="font-lato text-form-xs text-[#cc3300]">
										{formik.errors.app_name}
									</div>
								) : null}
							</div>
							<div className="flex flex-col gap-[4px]">
								<label
									htmlFor="description"
									className="font-lato text-form-xs font-semibold text-[#A3ABB1]"
								>
									Description
								</label>
								<textarea
									id="description"
									name="description"
									type="text"
									onChange={formik.handleChange}
									onBlur={formik.handleBlur}
									value={formik.values.description}
									className="min-h-[89px] rounded-[6px] border border-[#DDE2E5] px-[16px] py-[14px] font-lato placeholder:text-[#9A9A9A] hover:outline-0 focus:outline-0"
									placeholder="Enter"
								/>
								{formik.touched.description && formik.errors.description ? (
									<div className="font-lato text-form-xs text-[#cc3300]">
										{formik.errors.description}
									</div>
								) : null}
							</div>
							<FileUpload formik={formik} label={'Logo'} id={'logo'} />
							<FileUpload formik={formik} label={'Fav Icon'} id={'fav_icon'} />
							<div className="flex flex-col gap-[4px]">
								<label
									htmlFor="domain"
									className="font-lato text-form-xs font-semibold text-[#A3ABB1]"
								>
									Domain
								</label>

								{formik.touched.domain && formik.errors.domain ? (
									<div className="font-lato text-form-xs text-[#cc3300]">
										{formik.errors.domain}
									</div>
								) : null}

								<FieldArray
									name="domains"
									render={(arrayHelpers) => (
										<div className="flex flex-col gap-[12px]">
											<div className="flex flex-col gap-[8px]">
												{formik?.values?.domains?.map((domain, index) => (
													<div key={index}>
														<Field name={`domains.${index}`}>
															{({ field, form, meta }) => (
																<div className="relative flex">
																	<input
																		type="text"
																		{...field}
																		className="w-full rounded-[6px] border border-[#DDE2E5] px-[16px] py-[14px] font-lato placeholder:text-[#9A9A9A] hover:outline-0 focus:outline-0"
																		placeholder="Enter"
																	/>
																	{formik?.values?.domains?.length > 1 ? (
																		<button
																			type="button"
																			onClick={() => arrayHelpers.remove(index)}
																			className="absolute inset-y-0 right-[-32px]"
																		>
																			<DeleteIcon />
																		</button>
																	) : null}

																	{meta.touched && meta.error && (
																		<div className="error">{meta.error}</div>
																	)}
																</div>
															)}
														</Field>
													</div>
												))}{' '}
											</div>
											<button
												type="button"
												onClick={() => arrayHelpers.push('')}
												className="w-fit"
											>
												<span className="font-lato text-[14px] font-bold leading-[20px] text-primary">
													+ Add more domain
												</span>
											</button>
										</div>
									)}
								/>
							</div>
							<div className="flex flex-col gap-[4px]">
								<label
									htmlFor="time_zome"
									className="font-lato text-form-xs font-semibold text-[#A3ABB1]"
								>
									Time Zone
								</label>
								<input
									id="time_zome"
									name="time_zome"
									type="text"
									onChange={formik.handleChange}
									onBlur={formik.handleBlur}
									value={formik.values.time_zome}
									className="rounded-[6px] border border-[#DDE2E5] px-[16px] py-[14px] font-lato placeholder:text-[#9A9A9A] hover:outline-0 focus:outline-0"
									placeholder="Enter"
								/>
								{formik.touched.time_zome && formik.errors.time_zome ? (
									<div className="font-lato text-form-xs text-[#cc3300]">
										{formik.errors.time_zome}
									</div>
								) : null}
							</div>
							<div className="flex flex-col gap-[4px]">
								<label
									htmlFor="date_time_format"
									className="font-lato text-form-xs font-semibold text-[#A3ABB1]"
								>
									Date Time Format
								</label>
								<input
									id="date_time_format"
									name="date_time_format"
									type="text"
									onChange={formik.handleChange}
									onBlur={formik.handleBlur}
									value={formik.values.date_time_format}
									className="rounded-[6px] border border-[#DDE2E5] px-[16px] py-[14px] font-lato placeholder:text-[#9A9A9A] hover:outline-0 focus:outline-0"
									placeholder="Enter"
								/>
								{formik.touched.date_time_format &&
								formik.errors.date_time_format ? (
									<div className="font-lato text-form-xs text-[#cc3300]">
										{formik.errors.date_time_format}
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
								<span>Update Details</span>
							</button>
						</div>
					</form>
				);
			}}
		</Formik>
	);
};

export default function UpdateAppDetailsModal() {
	const isUpdateAppDetailsModalOpen = useSelector(
		selectIsUpdateAppDetailsModalOpen
	);
	const dispatch = useDispatch();

	function closeModal() {
		dispatch(closeIsUpdateAppDetailsModalOpen());
	}

	return (
		<>
			<Transition appear show={isUpdateAppDetailsModalOpen} as={Fragment}>
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
								<Dialog.Panel className="relative flex h-screen max-h-screen min-h-full w-full max-w-[498px] transform flex-col gap-[32px] overflow-hidden bg-white px-[24px] pt-[52px] pb-[40px] text-left align-middle shadow-xl transition-all md:pl-[32px] md:pr-[32px] md:pt-[32px]">
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
												Update App Details
											</h4>
										</div>
									</Dialog.Title>
									<UpdateAppDetailsForm closeModal={closeModal} />
								</Dialog.Panel>
							</Transition.Child>
						</div>
					</div>
				</Dialog>
			</Transition>
		</>
	);
}
