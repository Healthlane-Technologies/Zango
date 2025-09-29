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
import DomainFieldArray from '../../../../components/Form/DomainFieldArray';
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
		domains: appData?.domains?.length > 0 
			? (() => {
				const domainObjs = appData.domains.map((eachDomain) => ({
					domain: eachDomain.domain,
					is_primary: eachDomain.is_primary || false
				}));
				// If no domain is marked as primary, mark the first one as primary
				const hasPrimary = domainObjs.some(d => d.is_primary);
				if (!hasPrimary && domainObjs.length > 0) {
					domainObjs[0].is_primary = true;
				}
				return domainObjs;
			})()
			: [{ domain: '', is_primary: true }],
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
		domains: Yup.array()
			.of(
				Yup.object({
					domain: Yup.string().required('Domain is required'),
					is_primary: Yup.boolean()
				})
			)
			.min(1, 'At least one domain is required')
			.test('has-primary', 'Exactly one domain must be marked as primary', function(domains) {
				if (!domains || domains.length === 0) return false;
				const primaryCount = domains.filter(d => d.is_primary).length;
				return primaryCount === 1;
			}),
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

		// Transform domains back to the expected format for the API
		if (tempValues.domains && Array.isArray(tempValues.domains)) {
			tempValues.domains = tempValues.domains
				.filter(domainObj => domainObj.domain && domainObj.domain.trim() !== '')
				.map(domainObj => ({
					domain: domainObj.domain,
					is_primary: domainObj.is_primary || false
				}));
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
		
		// Handle domains separately for proper submission
		const domainsData = tempValues.domains;
		delete tempValues.domains;
		
		let dynamicFormData = transformToFormData(tempValues);
		
		// Add domains as JSON string for proper backend processing
		if (domainsData && Array.isArray(domainsData)) {
			dynamicFormData.append('domains', JSON.stringify(domainsData));
		}

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
						const { values, handleSubmit } = formik;
						
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
										<DomainFieldArray
											key="domains"
											label="Domains"
											name="domains"
											id="domains"
											placeholder="Enter domain"
											value={get(formik.values, 'domains', [])}
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
											<div key={key} className="flex items-center gap-[8px]">
												<a
													href={`http://${eachDomain?.domain}`}
													target="_blank"
													rel="noopener noreferrer"
													className="text-[14px] font-medium text-[#5048ED] hover:underline"
												>
													{eachDomain.domain}
												</a>
												{eachDomain.is_primary && (
													<span className="inline-flex items-center px-[8px] py-[2px] rounded-[12px] bg-[#10B981] text-white text-[11px] font-medium">
														Primary
													</span>
												)}
											</div>
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
						</div>
					</SectionCard>

					{/* Template Configuration */}
					{appData?.app_template && (
						<SectionCard
							title="Template Configuration"
							icon={
								<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
									<path d="M4 4C4 2.89543 4.89543 2 6 2H14C15.1046 2 16 2.89543 16 4V16C16 17.1046 15.1046 18 14 18H6C4.89543 18 4 17.1046 4 16V4Z" fill="#E0E7FF"/>
									<path d="M4 4C4 2.89543 4.89543 2 6 2H14C15.1046 2 16 2.89543 16 4V16C16 17.1046 15.1046 18 14 18H6C4.89543 18 4 17.1046 4 16V4Z" stroke="#5048ED" strokeWidth="1.5"/>
									<path d="M7 6H13M7 9H13M7 12H10" stroke="#5048ED" strokeWidth="1.5" strokeLinecap="round"/>
									<circle cx="10" cy="14" r="1.5" fill="#5048ED"/>
								</svg>
							}
						>
							<div>
								<InfoItem 
									label="Template File" 
									value={
										<a 
											href={appData.app_template} 
											target="_blank"
											rel="noopener noreferrer"
											className="inline-flex items-center gap-[8px] text-[#5048ED] hover:underline"
										>
											<SingleFileIcon className="w-[16px] h-[16px]" />
											<span>Download Template</span>
										</a>
									} 
								/>
								<InfoItem 
									label="Template Status" 
									value={
										<span className="inline-flex items-center px-[8px] py-[2px] rounded-[12px] text-[11px] font-medium bg-[#10B981] text-white">
											Configured
										</span>
									} 
								/>
								<InfoItem 
									label="File Type" 
									value={
										<span className="inline-flex items-center gap-[4px]">
											<span className="text-[14px] font-mono bg-[#F3F4F6] px-[6px] py-[1px] rounded-[4px] text-[#374151]">
												{appData.app_template?.split('.').pop()?.toUpperCase() || 'ZIP'}
											</span>
										</span>
									} 
								/>
								<InfoItem 
									label="Template URL" 
									value={
										<span className="text-[12px] font-mono text-[#6B7280] break-all">
											{appData.app_template}
										</span>
									} 
								/>
							</div>
						</SectionCard>
					)}

					{/* Deployment Config */}
					<SectionCard
						title="Deployment Config"
						icon={
							<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
								<path d="M10 2L13 9H20L14.5 13.5L17 20L10 16L3 20L5.5 13.5L0 9H7L10 2Z" fill="#E0E7FF"/>
								<path d="M10 2L13 9H20L14.5 13.5L17 20L10 16L3 20L5.5 13.5L0 9H7L10 2Z" stroke="#5048ED" strokeWidth="1.5" strokeLinejoin="round"/>
								<circle cx="10" cy="10" r="2" fill="#5048ED"/>
							</svg>
						}
					>
						<div>
							{/* Environment Configurations */}
							{appData?.deployment_config && Object.keys(appData.deployment_config).length > 0 ? (
								<InfoItem 
									label="Environment Configurations" 
									value={
										<div className="space-y-[12px]">
											{Object.entries(appData.deployment_config).map(([environment, config]) => (
												<div key={environment} className="bg-[#F9FAFB] rounded-[8px] p-[12px] border border-[#E5E7EB]">
													<div className="flex items-center justify-between mb-[8px]">
														<span className="text-[12px] font-semibold text-[#374151] uppercase tracking-wide">
															{environment}
														</span>
														<span className={`inline-flex items-center px-[6px] py-[1px] rounded-[6px] text-[10px] font-medium ${
															environment === 'main' ? 'bg-[#10B981] text-white' :
															environment === 'staging' ? 'bg-[#F59E0B] text-white' :
															environment === 'notifications' ? 'bg-[#8B5CF6] text-white' :
															'bg-[#6B7280] text-white'
														}`}>
															{environment === 'main' ? 'PROD' : 
															 environment === 'staging' ? 'STAGE' :
															 environment === 'notifications' ? 'NOTIFY' : 
															 'DEV'}
														</span>
													</div>
													{typeof config === 'object' && config !== null ? (
														<div className="space-y-[4px]">
															{Object.entries(config).map(([key, value]) => (
																<div key={key} className="flex items-center justify-between text-[12px]">
																	<span className="text-[#6B7280] font-medium capitalize">{key}:</span>
																	<span className="text-[#111827] font-mono bg-[#F3F4F6] px-[6px] py-[1px] rounded-[4px]">
																		{String(value)}
																	</span>
																</div>
															))}
														</div>
													) : (
														<div className="text-[12px]">
															<span className="text-[#6B7280] font-medium">Value:</span>
															<span className="text-[#111827] font-mono bg-[#F3F4F6] px-[6px] py-[1px] rounded-[4px] ml-[8px]">
																{String(config)}
															</span>
														</div>
													)}
												</div>
											))}
										</div>
									} 
								/>
							) : (
								<InfoItem 
									label="Environment Configurations" 
									value="No deployment configuration available" 
								/>
							)}

							{appData?.suspended_on && (
								<InfoItem 
									label="Suspended On" 
									value={new Date(appData.suspended_on).toLocaleString()} 
								/>
							)}
							{appData?.deleted_on && (
								<InfoItem 
									label="Deleted On" 
									value={new Date(appData.deleted_on).toLocaleString()} 
								/>
							)}
						</div>
					</SectionCard>
				</div>
			)}
		</div>
	);
};

export default ModernAppConfiguration;