import { Dialog, Transition } from '@headlessui/react';
import { Formik } from 'formik';
import { get } from 'lodash';
import { Fragment } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import * as Yup from 'yup';
import { ReactComponent as BorderRadiusIcon } from '../../../../assets/images/svg/border-radius-icon.svg';
import { ReactComponent as ModalCloseIcon } from '../../../../assets/images/svg/modal-close-icon.svg';
import SelectField from '../../../../components/Form/SelectField';
import useApi from '../../../../hooks/useApi';
import { getFontFamily } from '../../../../utils/fonts';
import { transformToFormDataStringify } from '../../../../utils/helper';
import {
	closeIsEditThemeModalOpen,
	selectAppThemeConfigurationFormData,
	selectIsEditThemeModalOpen,
	toggleRerenderPage,
} from '../../slice';
import ColorPicker from '../AppThemeConfiguration/ColorPicker';

const EditThemeForm = ({ closeModal }) => {
	let { appId } = useParams();
	const dispatch = useDispatch();

	const appThemeConfigurationFormData = useSelector(
		selectAppThemeConfigurationFormData
	);
	const triggerApi = useApi();
	let initialValues = {
		name: appThemeConfigurationFormData?.name ?? '',
		config: {
			color: {
				primary:
					appThemeConfigurationFormData?.config?.color?.primary ?? '#5048ED',
				secondary:
					appThemeConfigurationFormData?.config?.color?.secondary ?? '#ffffff',
				background:
					appThemeConfigurationFormData?.config?.color?.background ?? '#ffffff',
			},
			typography: {
				font_family: 'Open Sans',
			},
			button: {
				border_radius:
					appThemeConfigurationFormData?.config?.button?.border_radius ?? '',
				color:
					appThemeConfigurationFormData?.config?.button?.color ?? '#ffffff',
				border_color:
					appThemeConfigurationFormData?.config?.button?.border_color ??
					'#C7CED3',
				background:
					appThemeConfigurationFormData?.config?.button?.background ??
					'#5048ED',
			},
		},
	};

	let validationSchema = Yup.object({
		name: Yup.string().required('Required'),
		config: Yup.object({
			color: Yup.object({
				primary: Yup.string().required('Required'),
				secondary: Yup.string().required('Required'),
				background: Yup.string().required('Required'),
			}),
			typography: Yup.object({
				font_family: Yup.string().required('Required'),
			}),
			button: Yup.object({
				border_radius: Yup.string().required('Required'),
				color: Yup.string().required('Required'),
				border_color: Yup.string().required('Required'),
				background: Yup.string().required('Required'),
			}),
		}),
	});

	let onSubmit = (values) => {
		let tempValues = values;

		let dynamicFormData = transformToFormDataStringify(tempValues);

		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/themes/${appThemeConfigurationFormData?.id}/`,
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
						<div className="flex grow flex-col gap-[40px] pr-[64px]">
							<div className="flex flex-col gap-[4px]">
								<label
									htmlFor="name"
									className="font-lato text-form-xs font-semibold text-[#A3ABB1]"
								>
									Theme Name
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
								/>
								{formik.touched.name && formik.errors.name ? (
									<div className="font-lato text-form-xs text-[#cc3300]">
										{formik.errors.name}
									</div>
								) : null}
							</div>
							<div className="flex flex-col gap-[16px]">
								<h4 className="font-source-sans-pro text-[18px] font-semibold leading-[24px] tracking-[-0.2px] text-[#212429]">
									Color
								</h4>
								<ColorPicker
									data={{
										id: 'config.color.primary',
										label: 'Primary Color',
										formik: formik,
									}}
								/>
								<ColorPicker
									data={{
										id: 'config.color.secondary',
										label: 'Secondary Color (optional)',
										formik: formik,
									}}
								/>
								<ColorPicker
									data={{
										id: 'config.color.background',
										label: 'Background Color',
										formik: formik,
									}}
								/>
							</div>
							<div className="flex flex-col gap-[16px]">
								<h4 className="font-source-sans-pro text-[18px] font-semibold leading-[24px] tracking-[-0.2px] text-[#212429]">
									Typography
								</h4>
								<SelectField
									key="config.typography.font_family"
									label="Time Zone"
									name="config.typography.font_family"
									id="config.typography.font_family"
									placeholder="Select font family"
									value={get(
										formik.values,
										'config.typography.font_family',
										''
									)}
									optionsDataName="config.typography.font_family"
									optionsData={getFontFamily() ?? []}
									formik={formik}
								/>
							</div>
							<div className="flex flex-col gap-[16px]">
								<h4 className="font-source-sans-pro text-[18px] font-semibold leading-[24px] tracking-[-0.2px] text-[#212429]">
									Button/CTA
								</h4>
								<div className="flex flex-col gap-[4px]">
									<label
										htmlFor="config.button.border_radius"
										className="font-lato text-form-xs font-semibold text-[#A3ABB1]"
									>
										Corner Radius
									</label>
									<div className="relative flex w-full gap-[16px] rounded-[6px] border border-[#DDE2E5] px-[16px] py-[14px] font-lato text-[#212429]">
										<input
											id="config.button.border_radius"
											name="config.button.border_radius"
											type="text"
											pattern="[0-9]+"
											onChange={formik.handleChange}
											onBlur={formik.handleBlur}
											value={get(
												formik.values,
												'config.button.border_radius',
												'#ffffff'
											)}
											className="w-full placeholder:text-[#9A9A9A] hover:outline-0 focus:outline-0"
											placeholder="Enter"
										/>
										<span className="text-[#6C747D]">px</span>
										<BorderRadiusIcon />
									</div>
									{get(formik.touched, 'config.button.border_radius', '') &&
									get(formik.errors, 'config.button.border_radius', '') ? (
										<div className="font-lato text-form-xs text-[#cc3300]">
											{get(formik.errors, 'config.button.border_radius', '')}
										</div>
									) : null}
								</div>
								<ColorPicker
									data={{
										id: 'config.button.background',
										label: 'CTA Color',
										formik: formik,
									}}
								/>
								<ColorPicker
									data={{
										id: 'config.button.border_color',
										label: 'Border Color',
										formik: formik,
									}}
								/>
								<ColorPicker
									data={{
										id: 'config.button.color',
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
								// disabled={!(formik.isValid && formik.dirty)}
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

export default function EditThemeModal() {
	const isEditThemeModalOpen = useSelector(selectIsEditThemeModalOpen);
	const dispatch = useDispatch();

	function closeModal() {
		dispatch(closeIsEditThemeModalOpen());
	}

	return (
		<>
			<Transition appear show={isEditThemeModalOpen} as={Fragment}>
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
												Edit App Theme
											</h4>
										</div>
									</Dialog.Title>
									<EditThemeForm closeModal={closeModal} />
								</Dialog.Panel>
							</div>
						</div>
					</Transition.Child>
				</Dialog>
			</Transition>
		</>
	);
}
