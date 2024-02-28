import { Dialog, Transition } from '@headlessui/react';
import { Field, FieldArray, Formik } from 'formik';
import { get } from 'lodash';
import { Fragment } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import * as Yup from 'yup';
import { ReactComponent as DeleteIcon } from '../../../../assets/images/svg/delete-icon.svg';
import { ReactComponent as ModalCloseIcon } from '../../../../assets/images/svg/modal-close-icon.svg';
import FileUpload from '../../../../components/Form/FileUpload';
import SelectField from '../../../../components/Form/SelectField';
import useApi from '../../../../hooks/useApi';
import { transformToFormData } from '../../../../utils/helper';
import {
	closeIsUpdateAppDetailsModalOpen,
	selectAppConfigurationData,
	selectIsUpdateAppDetailsModalOpen,
	toggleRerenderPage,
} from '../../slice';

const UpdateAppDetailsForm = ({ closeModal }) => {
	let { appId } = useParams();
	const dispatch = useDispatch();

	const appConfigurationData = useSelector(selectAppConfigurationData);
	const triggerApi = useApi();
	let initialValues = {
		name: appConfigurationData?.app?.name ?? '',
		description: appConfigurationData?.app?.description ?? '',
		logo: '',
		fav_icon: '',
		domains: appConfigurationData?.app?.domains?.map(
			(eachDomain) => eachDomain.domain
		) ?? [''],
		timezone: appConfigurationData?.app?.timezone ?? '',
		date_format: appConfigurationData?.app?.date_format ?? '',
		datetime_format: appConfigurationData?.app?.datetime_format ?? '',
	};

	let validationSchema = Yup.object({
		name: Yup.string().required('Required'),
		description: Yup.string().required('Required'),
		domains: Yup.array().of(Yup.string().required('Required')),
	});

	let onSubmit = (values) => {
		let tempValues = values;
		if (!tempValues['logo']) {
			delete tempValues['logo'];
		}

		if (!tempValues['fav_icon']) {
			delete tempValues['fav_icon'];
		}

		let dynamicFormData = transformToFormData(tempValues);

		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/`,
				type: 'PUT',
				loader: true,
				payload: dynamicFormData,
			});

			if (success && response) {
				closeModal();
				dispatch(toggleRerenderPage());
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
									htmlFor="name"
									className="font-lato text-form-xs font-semibold text-[#A3ABB1]"
								>
									App Name
								</label>
								<input
									id="name"
									name="name"
									type="text"
									onChange={formik.handleChange}
									onBlur={formik.handleBlur}
									value={formik.values.name}
									className="rounded-[6px] border border-[#DDE2E5] px-[16px] py-[14px] font-lato placeholder:text-[#9A9A9A] hover:outline-0 focus:outline-0"
									placeholder="Enter"
									disabled
								/>
								{formik.touched.name && formik.errors.name ? (
									<div className="font-lato text-form-xs text-[#cc3300]">
										{formik.errors.name}
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

							<FileUpload
								formik={formik}
								label={'Logo'}
								id={'logo'}
								fileValue={appConfigurationData?.app?.logo || ''}
							/>

							<FileUpload
								formik={formik}
								label={'Fav Icon'}
								id={'fav_icon'}
								fileValue={appConfigurationData?.app?.fav_icon || ''}
							/>

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
																<div className="relative flex flex-col gap-[8px]">
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
																				onClick={() =>
																					arrayHelpers.remove(index)
																				}
																				className="absolute inset-y-0 right-[-32px]"
																			>
																				<DeleteIcon />
																			</button>
																		) : null}
																	</div>

																	{meta.touched && meta.error && (
																		<div className="font-lato text-form-xs text-[#cc3300]">
																			{meta.error}
																		</div>
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
							<SelectField
								key="timezone"
								label="Time Zone"
								name="timezone"
								id="timezone"
								placeholder="Select time zone"
								value={get(formik.values, 'timezone', '')}
								optionsDataName="timezone"
								optionsData={
									appConfigurationData?.dropdown_options?.timezones ?? []
								}
								formik={formik}
							/>
							<SelectField
								key="date_format"
								label="Date Format"
								name="date_format"
								id="date_format"
								placeholder="Select date format"
								value={get(formik.values, 'date_format', '')}
								optionsDataName="date_format"
								optionsData={
									appConfigurationData?.dropdown_options?.date_formats ?? []
								}
								formik={formik}
							/>
							<SelectField
								key="datetime_format"
								label="Date Time Format"
								name="datetime_format"
								id="datetime_format"
								placeholder="Select date time format"
								value={get(formik.values, 'datetime_format', '')}
								optionsDataName="datetime_format"
								optionsData={
									appConfigurationData?.dropdown_options?.datetime_formats ?? []
								}
								formik={formik}
							/>
						</div>
						<div className="sticky bottom-0 flex flex-col gap-[8px] bg-[#ffffff] pt-[24px] font-lato text-[#696969]">
							<button
								type="submit"
								className="flex w-full items-center justify-center rounded-[4px] bg-primary px-[16px] py-[10px] font-lato text-[14px] font-bold leading-[20px] text-white disabled:opacity-[0.38]"
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
				<Dialog as="div" className="relative z-10" onClose={() => {}}>
					<Transition.Child
						as={Fragment}
						enter="ease-in-out duration-700"
						enterFrom="opacity-0"
						enterTo="opacity-100"
						leave="ease-in-out duration-700"
						leaveFrom="opacity-100"
						leaveTo="opacity-0"
					>
						<div className="fixed inset-0 bg-black bg-opacity-[.67]" />
					</Transition.Child>

					<Transition.Child
						as={Fragment}
						enter="transform transition ease-in-out duration-500"
						enterFrom="translate-x-full"
						enterTo="translate-x-0"
						leave="transform transition ease-in-out duration-500"
						leaveFrom="translate-x-0"
						leaveTo="translate-x-full"
					>
						<div className="fixed inset-0 overflow-y-auto">
							<div className="flex h-screen max-h-screen min-h-full grow items-center justify-center text-center md:justify-end">
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
							</div>
						</div>
					</Transition.Child>
				</Dialog>
			</Transition>
		</>
	);
}
