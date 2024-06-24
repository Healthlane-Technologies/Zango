import { Formik } from 'formik';
import { get } from 'lodash';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import * as Yup from 'yup';
import FileUpload from '../../../../../components/Form/FileUpload';
import InputField from '../../../../../components/Form/InputField';
import InputFieldArray from '../../../../../components/Form/InputFieldArray';
import SelectField from '../../../../../components/Form/SelectField';
import SubmitButton from '../../../../../components/Form/SubmitButton';
import TextareaField from '../../../../../components/Form/TextareaField';
import useApi from '../../../../../hooks/useApi';
import { transformToFormData } from '../../../../../utils/form';

import { selectAppConfigurationData, toggleRerenderPage } from '../../../slice';

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
						<div className="flex grow flex-col gap-[16px] pr-[32px]">
							<InputField
								key="name"
								label="App Name"
								name="name"
								id="name"
								placeholder="Enter"
								value={get(formik.values, 'name', '')}
								onChange={formik.handleChange}
								formik={formik}
								disabled
							/>

							<TextareaField
								key="description"
								label="Description"
								name="description"
								id="description"
								placeholder="Enter"
								value={get(formik.values, 'description', '')}
								onChange={formik.handleChange}
								formik={formik}
							/>

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

							<InputFieldArray
								key="domains"
								label="Domain"
								name="domains"
								id="domains"
								placeholder="Enter"
								value={get(formik.values, 'domains', '')}
								onChange={formik.handleChange}
								formik={formik}
							/>

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
							<SubmitButton
								label={'Update Details'}
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

export default UpdateAppDetailsForm;
