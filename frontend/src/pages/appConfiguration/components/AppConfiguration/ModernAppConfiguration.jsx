import React, { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Formik } from 'formik';
import * as Yup from 'yup';
import { get } from 'lodash';
import { selectAppConfigurationData, toggleRerenderPage } from '../../slice';
import useApi from '../../../../hooks/useApi';
import { transformToFormData } from '../../../../utils/form';
import { useParams } from 'react-router-dom';
import InputField from '../../../../components/Form/InputField';
import TextareaField from '../../../../components/Form/TextareaField';
import FileUpload from '../../../../components/Form/FileUpload';
import SelectField from '../../../../components/Form/SelectField';
import InputFieldArray from '../../../../components/Form/InputFieldArray';
import CheckboxField from '../../../../components/Form/CheckboxField';
import { ReactComponent as EachAppIcon } from '../../../../assets/images/svg/each-app-icon.svg';
import { ReactComponent as SingleFileIcon } from '../../../../assets/images/svg/single-file.svg';
import { getRepoName } from '../../../../utils/helper';

const ModernAppConfiguration = () => {
	const [isEditMode, setIsEditMode] = useState(false);
	const [isSaving, setIsSaving] = useState(false);
	const dispatch = useDispatch();
	const triggerApi = useApi();
	const { appId } = useParams();
	
	const appConfigurationData = useSelector(selectAppConfigurationData);
	
	if (!appConfigurationData) {
		return (
			<div className="flex items-center justify-center h-64">
				<div className="text-center">
					<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#5048ED] mx-auto mb-4"></div>
					<p className="text-[#6B7280]">Loading configuration...</p>
				</div>
			</div>
		);
	}

	const appData = appConfigurationData?.app;

	// Initial values for form
	const initialValues = {
		name: appData?.name ?? '',
		description: appData?.description ?? '',
		logo: '',
		fav_icon: '',
		domains: appData?.domains?.map((eachDomain) => eachDomain.domain) ?? [''],
		timezone: appData?.timezone ?? '',
		date_format: appData?.date_format ?? '',
		datetime_format: appData?.datetime_format ?? '',
		repo_url: appData?.extra_config?.git_config?.repo_url ?? '',
		dev: appData?.extra_config?.git_config?.branch?.dev ?? '',
		prod: appData?.extra_config?.git_config?.branch?.prod ?? '',
		staging: appData?.extra_config?.git_config?.branch?.staging ?? '',
		sync_packages: appData?.extra_config?.sync_packages ?? true 
	};

	// Validation schema
	const validationSchema = Yup.object({
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

	// Handle form submission
	const handleSubmit = async (values) => {
		setIsSaving(true);
		
		let tempValues = { ...values };
		if (!tempValues['logo']) {
			delete tempValues['logo'];
		}

		if (!tempValues['fav_icon']) {
			delete tempValues['fav_icon'];
		}

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

		try {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/`,
				type: 'PUT',
				loader: true,
				payload: dynamicFormData,
			});

			if (success && response) {
				dispatch(toggleRerenderPage());
				setIsEditMode(false);
			}
		} catch (error) {
			console.error('Error saving configuration:', error);
		} finally {
			setIsSaving(false);
		}
	};

	// Info item component for view mode
	const InfoItem = ({ label, value, isLink = false, href = '', isImage = false, defaultIcon = null }) => (
		<div className="flex items-start gap-[16px] py-[16px] border-b border-[#F3F4F6] last:border-b-0">
			<span className="min-w-[180px] text-[13px] font-medium text-[#6B7280]">{label}</span>
			<div className="flex-1">
				{isImage ? (
					value ? (
						<img src={value} className="h-[48px] w-[48px] object-contain rounded-[8px]" alt={label} />
					) : (
						defaultIcon || <EachAppIcon className="h-[48px] w-[48px]" />
					)
				) : isLink ? (
					<a href={href} target="_blank" rel="noopener noreferrer" className="text-[14px] font-medium text-[#5048ED] hover:underline">
						{value}
					</a>
				) : (
					<span className="text-[14px] font-medium text-[#111827]">{value || 'Not configured'}</span>
				)}
			</div>
		</div>
	);

	// Section card component
	const SectionCard = ({ title, icon, children }) => (
		<div className="bg-white rounded-[16px] border border-[#E5E7EB] p-[24px]">
			<div className="flex items-center gap-[12px] mb-[20px]">
				<div className="flex h-[40px] w-[40px] items-center justify-center rounded-[10px] bg-[#EFF6FF]">
					{icon}
				</div>
				<h3 className="text-[16px] font-semibold text-[#111827]">{title}</h3>
			</div>
			{children}
		</div>
	);

	return (
		<div className="max-w-[1200px] mx-auto">
			{/* Header */}
			<div className="flex items-center justify-between mb-[32px]">
				<div>
					<h2 className="text-[24px] font-semibold text-[#111827] mb-[4px]">Basic Information</h2>
					<p className="text-[14px] text-[#6B7280]">Manage your application details and configuration</p>
				</div>
				{!isEditMode && (
					<button
						onClick={() => setIsEditMode(true)}
						className="flex items-center gap-[8px] px-[16px] py-[8px] bg-[#5048ED] text-white rounded-[8px] hover:bg-[#4338CA] transition-colors"
					>
						<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
							<path d="M11.334 2.00004C11.5091 1.82494 11.7169 1.68605 11.9457 1.59129C12.1745 1.49653 12.4197 1.44775 12.6673 1.44775C12.915 1.44775 13.1602 1.49653 13.389 1.59129C13.6178 1.68605 13.8256 1.82494 14.0007 2.00004C14.1757 2.17513 14.3146 2.38297 14.4094 2.61178C14.5042 2.84059 14.5529 3.08577 14.5529 3.33337C14.5529 3.58097 14.5042 3.82615 14.4094 4.05496C14.3146 4.28377 14.1757 4.49161 14.0007 4.66671L5.00065 13.6667L1.33398 14.6667L2.33398 11L11.334 2.00004Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
						</svg>
						<span className="font-medium text-[14px]">Edit Details</span>
					</button>
				)}
			</div>

			{/* Content */}
			{isEditMode ? (
				<Formik
					initialValues={initialValues}
					validationSchema={validationSchema}
					onSubmit={handleSubmit}
					enableReinitialize={true}
				>
					{(formik) => {
						const { values, setFieldValue, handleSubmit, errors, touched } = formik;
						
						return (
							<form onSubmit={handleSubmit} className="space-y-[24px]">
								{/* Basic Information */}
								<SectionCard
									title="Basic Information"
									icon={
										<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
											<path d="M10 10C11.6569 10 13 8.65685 13 7C13 5.34315 11.6569 4 10 4C8.34315 4 7 5.34315 7 7C7 8.65685 8.34315 10 10 10Z" fill="#E0E7FF"/>
											<path d="M10 11C7.238 11 5 13.238 5 16H15C15 13.238 12.762 11 10 11Z" fill="#E0E7FF"/>
											<circle cx="10" cy="10" r="8" stroke="#5048ED" strokeWidth="1.5"/>
											<path d="M10 1V3M10 17V19M19 10H17M3 10H1" stroke="#5048ED" strokeWidth="1.5" strokeLinecap="round"/>
										</svg>
									}
								>
									<div className="space-y-[16px]">
										<InputField
											key="name"
											label="App Name"
											name="name"
											id="name"
											placeholder="Enter app name"
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
											placeholder="Enter app description"
											value={get(formik.values, 'description', '')}
											onChange={formik.handleChange}
											formik={formik}
										/>
									</div>
								</SectionCard>

								{/* Branding */}
								<SectionCard
									title="Branding"
									icon={
										<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
											<rect x="3" y="3" width="14" height="14" rx="2" fill="#E0E7FF"/>
											<path d="M7 13L12 7M7 7H12V13" stroke="#5048ED" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
											<circle cx="13" cy="13" r="1" fill="#5048ED"/>
											<circle cx="7" cy="7" r="1" fill="#5048ED"/>
										</svg>
									}
								>
									<div className="grid grid-cols-1 md:grid-cols-2 gap-[16px]">
										<FileUpload
											formik={formik}
											label={'Logo'}
											id={'logo'}
											fileValue={appData?.logo || ''}
										/>
										<FileUpload
											formik={formik}
											label={'Favicon'}
											id={'fav_icon'}
											fileValue={appData?.fav_icon || ''}
										/>
									</div>
								</SectionCard>

								{/* Domain & Regional Settings */}
								<SectionCard
									title="Domain & Regional Settings"
									icon={
										<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
											<circle cx="10" cy="10" r="7" fill="#E0E7FF"/>
											<circle cx="10" cy="10" r="8" stroke="#5048ED" strokeWidth="1.5"/>
											<path d="M2 10H18" stroke="#5048ED" strokeWidth="1.5"/>
											<path d="M10 2C10 2 13 5 13 10C13 15 10 18 10 18" stroke="#5048ED" strokeWidth="1.5"/>
											<path d="M10 2C10 2 7 5 7 10C7 15 10 18 10 18" stroke="#5048ED" strokeWidth="1.5"/>
											<circle cx="6" cy="10" r="1" fill="#5048ED"/>
											<circle cx="14" cy="10" r="1" fill="#5048ED"/>
										</svg>
									}
								>
									<div className="space-y-[16px]">
										<InputFieldArray
											key="domains"
											label="Domains"
											name="domains"
											id="domains"
											placeholder="Enter domain"
											value={get(formik.values, 'domains', '')}
											onChange={formik.handleChange}
											formik={formik}
										/>
										<div className="grid grid-cols-1 md:grid-cols-3 gap-[16px]">
											<SelectField
												key="timezone"
												label="Time Zone"
												name="timezone"
												id="timezone"
												placeholder="Select time zone"
												value={get(formik.values, 'timezone', '')}
												optionsDataName="timezone"
												optionsData={appConfigurationData?.dropdown_options?.timezones ?? []}
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
												optionsData={appConfigurationData?.dropdown_options?.date_formats ?? []}
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
												optionsData={appConfigurationData?.dropdown_options?.datetime_formats ?? []}
												formik={formik}
											/>
										</div>
									</div>
								</SectionCard>

								{/* Repository Configuration */}
								<SectionCard
									title="Repository Configuration"
									icon={
										<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
											<path d="M5 5H15V15C15 16.1046 14.1046 17 13 17H7C5.89543 17 5 16.1046 5 15V5Z" fill="#E0E7FF"/>
											<path d="M5 5C5 3.89543 5.89543 3 7 3H13C14.1046 3 15 3.89543 15 5" stroke="#5048ED" strokeWidth="1.5"/>
											<path d="M8 7V13M12 7V13" stroke="#5048ED" strokeWidth="1.5" strokeLinecap="round"/>
											<path d="M10 10H8M12 10H10" stroke="#5048ED" strokeWidth="1.5" strokeLinecap="round"/>
											<circle cx="10" cy="10" r="2" fill="#5048ED"/>
										</svg>
									}
								>
									<div className="space-y-[16px]">
										<InputField
											key="repo_url"
											label="Repository URL"
											name="repo_url"
											id="repo_url"
											placeholder="https://github.com/user/repo"
											value={get(formik.values, 'repo_url', '')}
											onChange={formik.handleChange}
											formik={formik}
										/>
										{values.repo_url && (
											<div className="grid grid-cols-1 md:grid-cols-3 gap-[16px]">
												<InputField
													key="dev"
													label="Development Branch"
													name="dev"
													id="dev"
													placeholder="dev"
													value={get(formik.values, 'dev', '')}
													onChange={formik.handleChange}
													formik={formik}
												/>
												<InputField
													key="staging"
													label="Staging Branch"
													name="staging"
													id="staging"
													placeholder="staging"
													value={get(formik.values, 'staging', '')}
													onChange={formik.handleChange}
													formik={formik}
												/>
												<InputField
													key="prod"
													label="Production Branch"
													name="prod"
													id="prod"
													placeholder="main"
													value={get(formik.values, 'prod', '')}
													onChange={formik.handleChange}
													formik={formik}
												/>
											</div>
										)}
										<div className="pt-[8px]">
											<CheckboxField
												key="sync_packages"
												label="Sync Packages"
												content="Automatically sync packages from repository"
												name="sync_packages"
												id="sync_packages"
												value={get(formik.values, 'sync_packages', '')}
												onChange={formik.handleChange}
												formik={formik}
											/>
										</div>
									</div>
								</SectionCard>

								{/* Action Buttons */}
								<div className="flex justify-end gap-[12px] pt-[8px]">
									<button
										type="button"
										onClick={() => setIsEditMode(false)}
										className="px-[16px] py-[8px] border border-[#E5E7EB] text-[#6B7280] rounded-[8px] hover:bg-[#F9FAFB] transition-colors"
									>
										Cancel
									</button>
									<button
										type="submit"
										disabled={isSaving}
										className="px-[16px] py-[8px] bg-[#5048ED] text-white rounded-[8px] hover:bg-[#4338CA] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
									>
										{isSaving ? 'Saving...' : 'Save Changes'}
									</button>
								</div>
							</form>
						);
					}}
				</Formik>
			) : (
				// View Mode
				<div className="space-y-[24px]">
					{/* Basic Information */}
					<SectionCard
						title="Basic Information"
						icon={
							<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
								<path d="M10 10C11.6569 10 13 8.65685 13 7C13 5.34315 11.6569 4 10 4C8.34315 4 7 5.34315 7 7C7 8.65685 8.34315 10 10 10Z" fill="#E0E7FF"/>
								<path d="M10 11C7.238 11 5 13.238 5 16H15C15 13.238 12.762 11 10 11Z" fill="#E0E7FF"/>
								<circle cx="10" cy="10" r="8" stroke="#5048ED" strokeWidth="1.5"/>
								<path d="M10 1V3M10 17V19M19 10H17M3 10H1" stroke="#5048ED" strokeWidth="1.5" strokeLinecap="round"/>
							</svg>
						}
					>
						<div>
							<InfoItem 
								label="App Name" 
								value={appData?.name} 
							/>
							<InfoItem 
								label="Description" 
								value={
									<pre className="whitespace-pre-wrap font-sans text-[14px] text-[#111827]">
										{appData?.description}
									</pre>
								} 
							/>
						</div>
					</SectionCard>

					{/* Branding */}
					<SectionCard
						title="Branding"
						icon={
							<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
								<rect x="3" y="3" width="14" height="14" rx="2" fill="#E0E7FF"/>
								<path d="M7 13L12 7M7 7H12V13" stroke="#5048ED" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
								<circle cx="13" cy="13" r="1" fill="#5048ED"/>
								<circle cx="7" cy="7" r="1" fill="#5048ED"/>
							</svg>
						}
					>
						<div className="grid grid-cols-2 gap-[16px]">
							<InfoItem 
								label="Logo" 
								value={appData?.logo} 
								isImage={true}
							/>
							<InfoItem 
								label="Favicon" 
								value={appData?.fav_icon} 
								isImage={true}
							/>
						</div>
					</SectionCard>

					{/* Domain & Regional Settings */}
					<SectionCard
						title="Domain & Regional Settings"
						icon={
							<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
								<circle cx="10" cy="10" r="7" fill="#E0E7FF"/>
								<circle cx="10" cy="10" r="8" stroke="#5048ED" strokeWidth="1.5"/>
								<path d="M2 10H18" stroke="#5048ED" strokeWidth="1.5"/>
								<path d="M10 2C10 2 13 5 13 10C13 15 10 18 10 18" stroke="#5048ED" strokeWidth="1.5"/>
								<path d="M10 2C10 2 7 5 7 10C7 15 10 18 10 18" stroke="#5048ED" strokeWidth="1.5"/>
								<circle cx="6" cy="10" r="1" fill="#5048ED"/>
								<circle cx="14" cy="10" r="1" fill="#5048ED"/>
							</svg>
						}
					>
						<div>
							<InfoItem 
								label="Domains" 
								value={
									<div className="flex flex-col gap-[8px]">
										{appData?.domains?.map((eachDomain, key) => (
											<a
												href={`http://${eachDomain?.domain}`}
												target="_blank"
												rel="noopener noreferrer"
												key={key}
												className="text-[14px] font-medium text-[#5048ED] hover:underline"
											>
												{eachDomain.domain}
											</a>
										))}
									</div>
								} 
							/>
							<InfoItem 
								label="Timezone" 
								value={appData?.timezone} 
							/>
							<InfoItem 
								label="Date Format" 
								value={appData?.date_format_display} 
							/>
							<InfoItem 
								label="Date-Time Format" 
								value={appData?.datetime_format_display} 
							/>
						</div>
					</SectionCard>

					{/* Repository Configuration */}
					<SectionCard
						title="Repository Configuration"
						icon={
							<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
								<path d="M5 5H15V15C15 16.1046 14.1046 17 13 17H7C5.89543 17 5 16.1046 5 15V5Z" fill="#E0E7FF"/>
								<path d="M5 5C5 3.89543 5.89543 3 7 3H13C14.1046 3 15 3.89543 15 5" stroke="#5048ED" strokeWidth="1.5"/>
								<path d="M8 7V13M12 7V13" stroke="#5048ED" strokeWidth="1.5" strokeLinecap="round"/>
								<path d="M10 10H8M12 10H10" stroke="#5048ED" strokeWidth="1.5" strokeLinecap="round"/>
								<circle cx="10" cy="10" r="2" fill="#5048ED"/>
							</svg>
						}
					>
						<div>
							<InfoItem 
								label="Repository URL" 
								value={appData?.extra_config?.git_config?.repo_url ? getRepoName(appData.extra_config.git_config.repo_url) : 'Not configured'}
								isLink={!!appData?.extra_config?.git_config?.repo_url}
								href={appData?.extra_config?.git_config?.repo_url}
							/>
							{appData?.extra_config?.git_config?.repo_url && (
								<>
									<InfoItem 
										label="Development Branch" 
										value={appData?.extra_config?.git_config?.branch?.dev} 
									/>
									<InfoItem 
										label="Staging Branch" 
										value={appData?.extra_config?.git_config?.branch?.staging} 
									/>
									<InfoItem 
										label="Production Branch" 
										value={appData?.extra_config?.git_config?.branch?.prod} 
									/>
								</>
							)}
							<InfoItem 
								label="Package Sync" 
								value={appData?.extra_config?.sync_packages ? 'Enabled' : 'Disabled'} 
							/>
							<InfoItem 
								label="Template" 
								value={
									appData?.app_template ? (
										<a 
											href={appData.app_template} 
											target="_blank"
											rel="noopener noreferrer"
											className="inline-flex items-center gap-[8px] text-[#5048ED] hover:underline"
										>
											<SingleFileIcon className="w-[16px] h-[16px]" />
											<span>View Template</span>
										</a>
									) : (
										'No template found'
									)
								} 
							/>
						</div>
					</SectionCard>
				</div>
			)}
		</div>
	);
};

export default ModernAppConfiguration;