import { Dialog, Transition } from '@headlessui/react';
import { Fragment, useState, useEffect } from 'react';

import { useField, Formik, FieldArray, Field, ErrorMessage } from 'formik';
import * as Yup from 'yup';
import { get } from 'lodash';
import { transformToFormDataOrder } from '../../../../utils/helper';
import useApi from '../../../../hooks/useApi';

import { useSelector, useDispatch } from 'react-redux';
import {
	closeIsAddThemeModalOpen,
	selectIsAddThemeModalOpen,
} from '../../slice';

import { ReactComponent as ModalCloseIcon } from '../../../../assets/images/svg/modal-close-icon.svg';
import { ReactComponent as BorderRadiusIcon } from '../../../../assets/images/svg/border-radius-icon.svg';

import FileUpload from '../../../../components/Form/FileUpload';
import ColorPicker from '../AppThemeConfiguration/ColorPicker';

const AddThemeForm = ({ closeModal }) => {
	const triggerApi = useApi();
	let initialValues = {
		theme_name: '',
	};

	let validationSchema = Yup.object({
		theme_name: Yup.string().required('Required'),
	});

	let onSubmit = (values) => {
		let tempValues = values;

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
						<div className="flex grow flex-col gap-[40px] pr-[64px]">
							<div className="flex flex-col gap-[4px]">
								<label
									htmlFor="theme_name"
									className="font-lato text-form-xs font-semibold text-[#A3ABB1]"
								>
									Theme Name
								</label>
								<input
									id="theme_name"
									name="theme_name"
									type="text"
									onChange={formik.handleChange}
									onBlur={formik.handleBlur}
									value={formik.values.theme_name}
									className="rounded-[6px] border border-[#DDE2E5] px-[16px] py-[14px] font-lato placeholder:text-[#9A9A9A] hover:outline-0 focus:outline-0"
									placeholder="Enter"
								/>
								{formik.touched.theme_name && formik.errors.theme_name ? (
									<div className="font-lato text-form-xs text-[#cc3300]">
										{formik.errors.theme_name}
									</div>
								) : null}
							</div>
							<div className="flex flex-col gap-[16px]">
								<h4 className="font-source-sans-pro text-[18px] font-semibold leading-[24px] tracking-[-0.2px] text-[#212429]">
									Color
								</h4>

								<ColorPicker
									data={{
										id: 'primary_color',
										label: 'Primary Color',
										formik: formik,
									}}
								/>
								<ColorPicker
									data={{
										id: 'secondary_color',
										label: 'Secondary Color (optional)',
										formik: formik,
									}}
								/>
								<ColorPicker
									data={{
										id: 'background_color',
										label: 'Background Color',
										formik: formik,
									}}
								/>
							</div>
							<div className="flex flex-col gap-[16px]">
								<h4 className="font-source-sans-pro text-[18px] font-semibold leading-[24px] tracking-[-0.2px] text-[#212429]">
									Typography
								</h4>
								<div className="flex flex-col gap-[4px]">
									<label
										htmlFor="font_family"
										className="font-lato text-form-xs font-semibold text-[#A3ABB1]"
									>
										Font Family
									</label>
									<input
										id="font_family"
										name="font_family"
										type="text"
										onChange={formik.handleChange}
										onBlur={formik.handleBlur}
										value={formik.values.font_family}
										className="rounded-[6px] border border-[#DDE2E5] px-[16px] py-[14px] font-lato placeholder:text-[#9A9A9A] hover:outline-0 focus:outline-0"
										placeholder="Enter"
									/>
									{formik.touched.font_family && formik.errors.font_family ? (
										<div className="font-lato text-form-xs text-[#cc3300]">
											{formik.errors.font_family}
										</div>
									) : null}
								</div>
							</div>
							<div className="flex flex-col gap-[16px]">
								<h4 className="font-source-sans-pro text-[18px] font-semibold leading-[24px] tracking-[-0.2px] text-[#212429]">
									Button/CTA
								</h4>
								<div className="flex flex-col gap-[4px]">
									<label
										htmlFor="corner_radius"
										className="font-lato text-form-xs font-semibold text-[#A3ABB1]"
									>
										Corner Radius
									</label>
									<div className="relative flex w-full gap-[16px] rounded-[6px] border border-[#DDE2E5] px-[16px] py-[14px] font-lato text-[#212429]">
										<input
											id="corner_radius"
											name="corner_radius"
											type="text"
											onChange={formik.handleChange}
											onBlur={formik.handleBlur}
											value={formik.values.corner_radius}
											className="w-full placeholder:text-[#9A9A9A] hover:outline-0 focus:outline-0"
											placeholder="Enter"
										/>
										<span className="text-[#6C747D]">px</span>
										<BorderRadiusIcon />
									</div>
									{formik.touched.corner_radius &&
									formik.errors.corner_radius ? (
										<div className="font-lato text-form-xs text-[#cc3300]">
											{formik.errors.corner_radius}
										</div>
									) : null}
								</div>
								<ColorPicker
									data={{
										id: 'cta_color',
										label: 'CTA Color',
										formik: formik,
									}}
								/>
								<ColorPicker
									data={{
										id: 'border-color',
										label: 'Border Color',
										formik: formik,
									}}
								/>
								<ColorPicker
									data={{
										id: 'font-color-on-cta',
										label: 'Font Color on CTA',
										formik: formik,
									}}
								/>
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

export default function AddThemeModal() {
	const isAddThemeModalOpen = useSelector(selectIsAddThemeModalOpen);
	const dispatch = useDispatch();

	function closeModal() {
		dispatch(closeIsAddThemeModalOpen());
	}

	return (
		<>
			<Transition appear show={isAddThemeModalOpen} as={Fragment}>
				<Dialog as="div" className="relative z-10" onClose={closeModal}>
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
												Add App Theme
											</h4>
										</div>
									</Dialog.Title>
									<AddThemeForm closeModal={closeModal} />
								</Dialog.Panel>
							</div>
						</div>
					</Transition.Child>
				</Dialog>
			</Transition>
		</>
	);
}
