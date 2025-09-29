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
	let initialValues = {
		name: appThemeConfigurationFormData?.name ?? '',
		config: {
			colors: {
				primary:
					appThemeConfigurationFormData?.config?.colors?.primary ?? '#000000',
				gray:
					appThemeConfigurationFormData?.config?.colors?.gray ?? '#717680',
				success:
					appThemeConfigurationFormData?.config?.colors?.success ?? '#52c41a',
				warning:
					appThemeConfigurationFormData?.config?.colors?.warning ?? '#faad14',
				error:
					appThemeConfigurationFormData?.config?.colors?.error ?? '#AA4A44',
				info:
					appThemeConfigurationFormData?.config?.colors?.info ?? '#1890ff',
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
			colors: Yup.object({
				primary: Yup.string().required('Required'),
				gray: Yup.string().required('Required'),
				success: Yup.string().required('Required'),
				warning: Yup.string().required('Required'),
				error: Yup.string().required('Required'),
				info: Yup.string().required('Required'),
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
										id: 'config.colors.primary',
										label: 'Primary Color',
										formik: formik,
									}}
								/>
								<ColorPicker
									data={{
										id: 'config.colors.gray',
										label: 'Gray Color',
										formik: formik,
									}}
								/>
								<ColorPicker
									data={{
										id: 'config.colors.success',
										label: 'Success Color',
										formik: formik,
									}}
								/>
								<ColorPicker
									data={{
										id: 'config.colors.warning',
										label: 'Warning Color',
										formik: formik,
									}}
								/>
								<ColorPicker
									data={{
										id: 'config.colors.error',
										label: 'Error Color',
										formik: formik,
									}}
								/>
								<ColorPicker
									data={{
										id: 'config.colors.info',
										label: 'Info Color',
										formik: formik,
									}}
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
