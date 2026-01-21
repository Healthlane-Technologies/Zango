import { Formik } from 'formik';
import { get } from 'lodash';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import * as Yup from 'yup';
import InputField from '../../../../../components/Form/InputField';
import FontFamilySelectField from '../../../../../components/Form/FontFamilySelectField';
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

	const themeColors = appThemeConfigurationFormData?.config?.color || {};
	const themeButton = appThemeConfigurationFormData?.config?.button || {};

	let initialValues = {
		name: appThemeConfigurationFormData?.name ?? '',
		config: {
			color: {
				primary:
					themeColors?.primary ?? '#000000',
				secondary:
					themeColors?.secondary ?? '#E1D6AE',
				background:
					themeColors?.background ?? '#ffffff',
				gray:
					themeColors?.gray ?? '#717680',
				success:
					themeColors?.success ?? '#52c41a',
				warning:
					themeColors?.warning ?? '#faad14',
				error:
					themeColors?.error ?? '#AA4A44',
				info:
					themeColors?.info ?? '#1890ff',
			},
			button: {
				color: themeButton?.color ?? '#ffffff',
				background: themeButton?.background ?? '#5048ED',
				border_color: themeButton?.border_color ?? '#C7CED3',
				border_radius: themeButton?.border_radius ?? '10',
			},
			typography: {
				font_family:
					appThemeConfigurationFormData?.config?.typography?.font_family ??
					'-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, \'Helvetica Neue\', Arial, sans-serif',
				font_size_base:
					appThemeConfigurationFormData?.config?.typography?.font_size_base ?? '14px',
				line_height:
					appThemeConfigurationFormData?.config?.typography?.line_height ?? 1.5715,
			},
		},
	};

	let validationSchema = Yup.object({
		name: Yup.string().required('Required'),
		config: Yup.object({
			color: Yup.object({
				primary: Yup.string().required('Required'),
				secondary: Yup.string(),
				background: Yup.string(),
				gray: Yup.string().required('Required'),
				success: Yup.string().required('Required'),
				warning: Yup.string().required('Required'),
				error: Yup.string().required('Required'),
				info: Yup.string().required('Required'),
			}),
			button: Yup.object({
				color: Yup.string(),
				background: Yup.string(),
				border_color: Yup.string(),
				border_radius: Yup.string(),
			}),
			typography: Yup.object({
				font_family: Yup.string().required('Required'),
				font_size_base: Yup.string().required('Required'),
				line_height: Yup.number().required('Required'),
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
									Colors
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
										label: 'Secondary Color',
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
								<ColorPicker
									data={{
										id: 'config.color.gray',
										label: 'Gray Color',
										formik: formik,
									}}
								/>
								<ColorPicker
									data={{
										id: 'config.color.success',
										label: 'Success Color',
										formik: formik,
									}}
								/>
								<ColorPicker
									data={{
										id: 'config.color.warning',
										label: 'Warning Color',
										formik: formik,
									}}
								/>
								<ColorPicker
									data={{
										id: 'config.color.error',
										label: 'Error Color',
										formik: formik,
									}}
								/>
								<ColorPicker
									data={{
										id: 'config.color.info',
										label: 'Info Color',
										formik: formik,
									}}
								/>
							</div>
							<div className="flex flex-col gap-[16px]">
								<h4 className="font-source-sans-pro text-[18px] font-semibold leading-[24px] tracking-[-0.2px] text-[#212429]">
									Button
								</h4>
								<ColorPicker
									data={{
										id: 'config.button.color',
										label: 'Button Text Color',
										formik: formik,
									}}
								/>
								<ColorPicker
									data={{
										id: 'config.button.background',
										label: 'Button Background',
										formik: formik,
									}}
								/>
								<ColorPicker
									data={{
										id: 'config.button.border_color',
										label: 'Button Border Color',
										formik: formik,
									}}
								/>
								<InputField
									key="config.button.border_radius"
									label="Button Border Radius"
									name="config.button.border_radius"
									id="config.button.border_radius"
									placeholder="e.g., 10"
									value={get(formik.values, 'config.button.border_radius', '')}
									onChange={formik.handleChange}
									formik={formik}
								/>
							</div>
							<div className="flex flex-col gap-[16px]">
								<h4 className="font-source-sans-pro text-[18px] font-semibold leading-[24px] tracking-[-0.2px] text-[#212429]">
									Typography
								</h4>
								<FontFamilySelectField
									key="config.typography.font_family"
									label="Font Family"
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
								<InputField
									key="config.typography.font_size_base"
									label="Base Font Size"
									name="config.typography.font_size_base"
									id="config.typography.font_size_base"
									placeholder="e.g., 14px"
									value={get(formik.values, 'config.typography.font_size_base', '')}
									onChange={formik.handleChange}
									formik={formik}
								/>
								<InputField
									key="config.typography.line_height"
									label="Line Height"
									name="config.typography.line_height"
									id="config.typography.line_height"
									placeholder="e.g., 1.5715"
									type="number"
									step="0.0001"
									value={get(formik.values, 'config.typography.line_height', '')}
									onChange={formik.handleChange}
									formik={formik}
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
