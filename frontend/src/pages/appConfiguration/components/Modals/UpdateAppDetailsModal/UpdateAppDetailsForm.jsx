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
import CheckboxField from '../../../../../components/Form/CheckboxField';
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
		repo_url: appConfigurationData?.app?.extra_config?.git_config?.repo_url ?? '',
		dev: appConfigurationData?.app?.extra_config?.git_config?.branch?.dev ?? '',
		prod: appConfigurationData?.app?.extra_config?.git_config?.branch?.prod ?? '',
		staging: appConfigurationData?.app?.extra_config?.git_config?.branch?.staging ?? '',
		sync_packages: appConfigurationData?.app?.extra_config?.sync_packages ?? true 
	};

	let validationSchema = Yup.object({
		name: Yup.string().required('Required'),
		description: Yup.string().required('Required'),
		domains: Yup.array().of(Yup.string().required('Required')),
		repo_url: Yup.string().url('Must be a valid URL').nullable().when(['dev', 'prod', 'staging'], {
			is: (dev, prod, staging) => dev || prod || staging,
			then: Yup.string().required('Required'),
			otherwise: Yup.string().notRequired(),
		  }),
		dev: Yup.string().nullable(),
		prod: Yup.string().nullable(),
		staging: Yup.string().nullable(),
		sync_packages: Yup.boolean()
	});


	let onSubmit = (values) => {
		let tempValues = { ...values };
		if (!tempValues['logo']) {
			delete tempValues['logo'];
		}

		if (!tempValues['fav_icon']) {
			delete tempValues['fav_icon'];
		}

		const existingGitConfig = appConfigurationData?.app?.extra_config?.git_config || {};
		let extra_config = {
			git_config: {
			  branch: {
				dev: tempValues.dev || null,
				prod: tempValues.prod || null,
				staging: tempValues.staging || null
			  },
			  repo_url: tempValues.repo_url || null
			},
			sync_packages: tempValues.sync_packages
		};
		if (!extra_config.git_config.repo_url) {
			extra_config.git_config.repo_url = null;
		}

		if (!extra_config.git_config.repo_url && 
			!extra_config.git_config.branch.dev && 
			!extra_config.git_config.branch.prod && 
			!extra_config.git_config.branch.staging) {
			extra_config.git_config = {};
		}
		
		delete tempValues.dev;
		delete tempValues.prod;
		delete tempValues.staging;
		delete tempValues.repo_url;
		delete tempValues.sync_packages;
		
		tempValues.extra_config = JSON.stringify(extra_config);
		
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
			} else {
				tempValues.dev = extra_config?.git_config?.branch?.dev;
				tempValues.prod = extra_config?.git_config?.branch?.prod;
				tempValues.staging = extra_config?.git_config?.branch?.staging;
				tempValues.repo_url = extra_config?.git_config?.repo_url;
				tempValues.sync_packages = extra_config?.sync_packages;
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
							<InputField
								key="repo_url"
								label="Repo URL"
								name="repo_url"
								id="repo_url"
								placeholder="Enter"
								value={get(formik.values, 'repo_url', '')}
								onChange={formik.handleChange}
								formik={formik}
							/>
							<InputField
								key="dev"
								label="Development Branch"
								name="dev"
								id="name"
								placeholder="Enter"
								value={get(formik.values, 'dev', '')}
								onChange={formik.handleChange}
								formik={formik}
							/>
							<InputField
								key="prod"
								label="Production Branch"
								name="prod"
								id="prod"
								placeholder="Enter"
								value={get(formik.values, 'prod', '')}
								onChange={formik.handleChange}
								formik={formik}
							/>
							<InputField
								key="staging"
								label="Staging Branch"
								name="staging"
								id="staging"
								placeholder="Enter"
								value={get(formik.values, 'staging', '')}
								onChange={formik.handleChange}
								formik={formik}
							/>
							<CheckboxField
								key="sync_packages"
								label="Sync Packages"
								content=""
								name="sync_packages"
								id="sync_packages"
								placeholder=""
								value={get(formik.values, 'sync_packages', '')}
								onChange={formik.handleChange}
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
