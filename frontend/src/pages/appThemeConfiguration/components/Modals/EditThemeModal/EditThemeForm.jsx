import { Formik } from 'formik';
import { get } from 'lodash';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import * as Yup from 'yup';
import { ReactComponent as BorderRadiusIcon } from '../../../../../assets/images/svg/border-radius-icon.svg';
import InputField from '../../../../../components/Form/InputField';
import SelectField from '../../../../../components/Form/SelectField';
import SubmitButton from '../../../../../components/Form/SubmitButton';
import useApi from '../../../../../hooks/useApi';
import { getFontFamily } from '../../../../../utils/fonts';
import { transformToFormDataStringify } from '../../../../../utils/form';
import {
	selectAppThemeConfigurationFormData,
	toggleRerenderPage,
} from '../../../slice';
import ColorPicker from '../../AppThemeConfiguration/ColorPicker';

const EditThemeForm = ({ closeModal }) => {
	let { appId } = useParams();
	const dispatch = useDispatch();

	const appThemeConfigurationFormData = useSelector(
		selectAppThemeConfigurationFormData
	);
	const triggerApi = useApi();
	console.log('appThemeConfigurationFormData', appThemeConfigurationFormData);
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
				font_family:
					appThemeConfigurationFormData?.config?.typography?.font_family ??
					'Open Sans',
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
							<InputField
								key="name"
								label="Theme Name"
								name="name"
								id="name"
								placeholder="Enter"
								value={get(formik.values, 'name', '')}
								onChange={formik.handleChange}
								formik={formik}
							/>
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
									label="Font"
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
							<SubmitButton
								label={'Save'}
								allowDisabled={false}
								formik={formik}
							/>
						</div>
					</form>
				);
			}}
		</Formik>
	);
};

export default EditThemeForm;
