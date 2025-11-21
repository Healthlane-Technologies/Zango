import { Formik } from 'formik';
import { get } from 'lodash';
import { useLayoutEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import * as Yup from 'yup';
import InputField from '../../../../../components/Form/InputField';
import MultiSelectField from '../../../../../components/Form/MultiSelectField';
import CheckboxField from '../../../../../components/Form/CheckboxField';
import CountryCodeSelector from '../../../../../components/Form/CountryCodeSelector';
import SubmitButton from '../../../../../components/Form/SubmitButton';
import useApi from '../../../../../hooks/useApi';
import { transformToFormData } from '../../../../../utils/form';
import {
	selectAppUserManagementData,
	selectAppUserManagementFormData,
	toggleRerenderPage,
} from '../../../slice';
import { countryCodeList } from '../../../../../utils/countryCodes';
import toast from 'react-hot-toast';
import Notifications from '../../../../../components/Notifications';

const EditUserDetailsForm = ({ closeModal }) => {
	let { appId } = useParams();
	const dispatch = useDispatch();
	const [countryCode,setCountryCode] = useState({
		name: 'India',
		  dial_code: '+91',
		  code: 'IN',
  	})

	const appUserManagementData = useSelector(selectAppUserManagementData);
	let appUserManagementFormData = useSelector(
		selectAppUserManagementFormData
	);

	const triggerApi = useApi();

	const twoFactorMethodOptions = [
		{ id: "email", label: "Email" },
		{ id: "sms", label: "SMS" },
	];

	const MultiSelectChips = ({ label, name, options, value, onChange, description, twoFactorEnabled = false }) => (
		<div className="space-y-[12px]">
			<div>
				<label className="font-lato text-[12px] font-semibold text-[#A3ABB1] uppercase tracking-[0.5px]">
					{label}
				</label>
				{description && (
					<p className="font-lato text-[10px] leading-[14px] text-[#6B7280] mt-[2px]">
						{description}
					</p>
				)}
			</div>
			<div className="flex flex-wrap gap-[8px]">
				{options.map((option) => {
					const isSelected = Array.isArray(value) ? value.includes(option.id) : value === option.id;
					const isDisabled = twoFactorEnabled && isSelected;
					return (
						<button
							key={option.id}
							type="button"
							disabled={isDisabled}
							onClick={() => {
								if (isDisabled) return;
								const currentValue = Array.isArray(value) ? value : [value];
								const newValue = isSelected
									? currentValue.filter(v => v !== option.id)
									: [...currentValue, option.id];
								onChange(newValue);
							}}
							className={`px-[12px] py-[6px] rounded-[6px] border font-lato text-[12px] font-medium transition-all duration-200 flex items-center gap-[6px] ${
								isSelected
									? `border-[#5048ED] bg-[#5048ED] text-white ${isDisabled ? 'opacity-75 cursor-not-allowed' : ''}`
									: 'border-[#E5E7EB] bg-white text-[#6B7280] hover:border-[#5048ED] hover:bg-[#F8FAFC]'
							}`}
						>
							{isSelected && (
								<svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
									<path d="M10 3L4.5 8.5L2 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
								</svg>
							)}
							{option.label}
						</button>
					);
				})}
			</div>
		</div>
	);

	const ToggleCard = ({ title, description, name, value, onChange, children }) => (
		<div className={`rounded-[8px] border transition-all duration-200 ${
			value ? 'border-[#5048ED] bg-[#F8FAFC]' : 'border-[#E5E7EB] bg-white'
		}`}>
			<div className="p-[12px]">
				<div className="flex items-start gap-[8px]">
					<CheckboxField
						name={name}
						value={value}
						onChange={onChange}
					/>
					<div className="flex-1">
						<h4 className="font-lato text-[12px] font-semibold leading-[16px] text-[#111827]">
							{title}
						</h4>
						{description && (
							<p className="font-lato text-[10px] leading-[14px] text-[#6B7280] mt-[2px]">
								{description}
							</p>
						)}
					</div>
				</div>
				{value && children && (
					<div className="mt-[12px] pl-[24px] space-y-[8px]">
						{children}
					</div>
				)}
			</div>
		</div>
	);

	let pn_country_code = appUserManagementFormData?.pn_country_code ?? '+91'
	useLayoutEffect(()=>{
		if(appUserManagementFormData?.mobile=='' || appUserManagementFormData?.mobile==null){
			pn_country_code = appUserManagementData?.pn_country_code ?? '+91'
		}
		let countryCodeObj = countryCodeList.find((c)=>c.dial_code===pn_country_code)
		setCountryCode(countryCodeObj)
	},[])

	
	let initialValues = {
		name: appUserManagementFormData?.name ?? '',
		email: appUserManagementFormData?.email ?? '',
		mobile: (appUserManagementFormData?.mobile=='' || appUserManagementFormData?.mobile==null)? '': pn_country_code.length!=null?appUserManagementFormData?.mobile.slice(pn_country_code.length):appUserManagementFormData?.mobile,
		roles: appUserManagementFormData?.roles?.map((eachApp) => eachApp.id) ?? [],
		two_factor_auth: {
			required: appUserManagementFormData?.auth_config?.two_factor_auth?.required ?? false,
			allowedMethods: appUserManagementFormData?.auth_config?.two_factor_auth?.allowedMethods ?? [],
		},
	};

	let validationSchema = Yup.object().shape(
		{
			name: Yup.string().required('Required'),
			email: Yup.string().when(['mobile'], {
				is: (mobile) => {
					if (!mobile) return true;
				},
				then: Yup.string().email('Invalid email address').required('Required'),
				otherwise: Yup.string(),
			}),
			mobile: Yup.string().when(['email'], {
				is: (email) => {
					if (!email) return true;
				},
				then: Yup.string().required('Required'),
			}),
			roles: Yup.array().min(1, 'Minimun one is required').required('Required'),
			two_factor_auth: Yup.object({
				required: Yup.boolean(),
				allowedMethods: Yup.array().when('required', {
					is: true,
					then: (schema) => schema.min(1, 'At least one method is required'),
					otherwise: (schema) => schema,
				}),
			}),
		},
		[
			['name'],
			['mobile', 'email'],
			['email', 'mobile'],
			['roles'],
		]
	);

	let onSubmit = (values) => {
		let tempValues = values
		if(values.mobile){
			tempValues = {...values,mobile:countryCode?.dial_code+values.mobile}
		}

		// Create auth_config object from two_factor_auth
		const auth_config = {
			two_factor_auth: tempValues.two_factor_auth
		};
		
		// Remove the original two_factor_auth field
		delete tempValues.two_factor_auth;
		
		let dynamicFormData = transformToFormData(tempValues);
		
		dynamicFormData.append('auth_config', JSON.stringify(auth_config));

		const makeApiCall = async () => {
			const { success } = await triggerApi({
				url: `/api/v1/apps/${appId}/users/${appUserManagementFormData?.id}/`,
				type: 'PUT',
				loader: true,
				payload: dynamicFormData,
			});

			if (success) {
				closeModal();
				dispatch(toggleRerenderPage());
			}else{
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
				const profilePic = appUserManagementFormData?.profile_pic;
				const userInitials = appUserManagementFormData?.name
					? appUserManagementFormData.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
					: 'U';

				return (
					<form
						className="complete-hidden-scroll-style flex grow flex-col overflow-y-auto"
						onSubmit={formik.handleSubmit}
					>
						<div className="flex grow flex-col gap-[20px] pb-[20px] px-[40px] [&_input]:!py-[10px] [&_input]:!text-[13px]">
							{/* User Profile Section */}
							<div className="flex items-center gap-[16px] p-[16px] bg-[#F9FAFB] rounded-[12px] border border-[#E5E7EB] max-w-[800px]">
								<div className="relative">
									{profilePic ? (
										<img
											src={profilePic}
											alt={appUserManagementFormData?.name || 'User'}
											className="w-[64px] h-[64px] rounded-full object-cover border-2 border-white shadow-sm"
										/>
									) : (
										<div className="w-[64px] h-[64px] rounded-full bg-gradient-to-br from-[#5048ED] to-[#7C3AED] flex items-center justify-center border-2 border-white shadow-sm">
											<span className="text-[24px] font-semibold text-white">{userInitials}</span>
										</div>
									)}
									<div className="absolute -bottom-1 -right-1 w-[20px] h-[20px] bg-[#10B981] rounded-full border-2 border-white"></div>
								</div>
								<div className="flex-1">
									<h3 className="font-lato text-[16px] font-semibold text-[#111827] mb-[4px]">
										{appUserManagementFormData?.name || 'User Profile'}
									</h3>
									<p className="font-lato text-[12px] text-[#6B7280]">
										{appUserManagementFormData?.email || appUserManagementFormData?.mobile || 'No contact info'}
									</p>
								</div>
							</div>

							{/* Basic Information Section */}
							<div className="space-y-[16px] max-w-[800px]">
								<h3 className="font-lato text-[14px] font-semibold text-[#111827] flex items-center gap-[8px]">
									<svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[#5048ED]">
										<path d="M8 8a3 3 0 100-6 3 3 0 000 6zM8 10c-4 0-7 2-7 4v1h14v-1c0-2-3-4-7-4z" fill="currentColor"/>
									</svg>
									Basic Information
								</h3>

								<div className="max-w-[550px]">
									<InputField
										key="name"
										label="Full Name"
										name="name"
										id="name"
										placeholder="Enter full name of the user"
										value={get(formik.values, 'name', '')}
										onChange={formik.handleChange}
										formik={formik}
									/>
								</div>

								<div className="grid grid-cols-1 md:grid-cols-2 gap-[16px] max-w-[550px]">
									<InputField
										key="email"
										label="Email"
										name="email"
										id="email"
										placeholder="user@example.com"
										value={get(formik.values, 'email', '')}
										onChange={formik.handleChange}
										formik={formik}
									/>

									<div className="flex flex-col gap-[4px]">
										<label
											htmlFor="mobile"
											className="font-lato text-[12px] font-semibold text-[#A3ABB1] uppercase tracking-[0.5px]"
										>
											Mobile
										</label>
										<div className="flex gap-[12px] rounded-[6px] border border-[#DDE2E5] px-[12px] focus-within:border-[#5048ED] focus-within:ring-1 focus-within:ring-[#5048ED] transition-all">
											<span className="font-lato text-[#6C747D]">
												<CountryCodeSelector
													countryCode={countryCode}
													setCountryCode={setCountryCode}
												/>
											</span>
											<input
												id="mobile"
												name="mobile"
												type="number"
												onChange={formik.handleChange}
												onBlur={formik.handleBlur}
												value={formik.values.mobile}
												className="flex-1 py-[8px] font-lato text-[13px] placeholder:text-[#9A9A9A] hover:outline-0 focus:outline-0 bg-transparent"
												placeholder="00000 00000"
											/>
										</div>
										{formik.touched.mobile && formik.errors.mobile ? (
											<div className="font-lato text-[11px] text-[#EF4444] mt-[4px]">
												{formik.errors.mobile}
											</div>
										) : null}
									</div>
								</div>
							</div>

							{/* Access & Roles Section */}
							<div className="space-y-[16px] max-w-[800px]">
								<h3 className="font-lato text-[14px] font-semibold text-[#111827] flex items-center gap-[8px]">
									<svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[#5048ED]">
										<path d="M8 2L3 5v3c0 3.04 1.88 5.64 5 6 3.12-.36 5-3 5-6V5l-5-3z" fill="currentColor" fillOpacity="0.3"/>
										<path d="M8 2L3 5v3c0 3.04 1.88 5.64 5 6 3.12-.36 5-3 5-6V5l-5-3z" stroke="currentColor" strokeWidth="1.2" fill="none"/>
									</svg>
									Access & Roles
								</h3>

								<div className="max-w-[550px]">
									<MultiSelectField
										key="roles"
										label="User Role"
										name="roles"
										id="roles"
										placeholder="Select roles"
										value={get(formik.values, 'roles', [])}
										optionsDataName="roles"
										optionsData={
											appUserManagementData?.dropdown_options?.roles ?? []
										}
										formik={formik}
									/>
								</div>
							</div>

							{/* Two-Factor Authentication Section */}
							<div className="space-y-[16px] max-w-[800px]">
								<h3 className="font-lato text-[14px] font-semibold text-[#111827] flex items-center gap-[8px]">
									<svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[#5048ED]">
										<rect x="3" y="6" width="10" height="7" rx="1" fill="currentColor" fillOpacity="0.3"/>
										<path d="M5 6V4a3 3 0 016 0v2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
										<circle cx="8" cy="10" r="1" fill="currentColor"/>
									</svg>
									Two-Factor Authentication
								</h3>

								<div className="max-w-[550px]">
									<ToggleCard
										title="Require Two-Factor Authentication"
										description="Make 2FA mandatory for this user"
										name="two_factor_auth.required"
										value={get(formik.values, 'two_factor_auth.required', false)}
										onChange={(e) => {
											const isEnabled = e.target.checked;
											formik.setFieldValue('two_factor_auth.required', isEnabled);
											if (isEnabled) {
												formik.setFieldValue('two_factor_auth.allowedMethods', ['email', 'sms']);
											} else {
												formik.setFieldValue('two_factor_auth.allowedMethods', []);
											}
										}}
									>
										<MultiSelectChips
											name="two_factor_auth.allowedMethods"
											label="Allowed Methods"
											description="Select available methods for two-factor authentication"
											options={twoFactorMethodOptions}
											value={get(formik.values, 'two_factor_auth.allowedMethods', [])}
											onChange={(value) => formik.setFieldValue('two_factor_auth.allowedMethods', value)}
											twoFactorEnabled={get(formik.values, 'two_factor_auth.required', false)}
										/>
									</ToggleCard>
								</div>
							</div>
						</div>

						<div className="sticky bottom-0 flex gap-[12px] bg-[#ffffff] pt-[24px] px-[40px] border-t border-[#E5E7EB]">
							<button
								type="button"
								onClick={closeModal}
								className="px-[16px] py-[10px] rounded-[8px] border border-[#E5E7EB] font-lato text-[14px] font-medium text-[#6B7280] hover:bg-[#F9FAFB] transition-colors"
							>
								Cancel
							</button>
							<SubmitButton
								label={'Save Changes'}
								formik={formik}
								allowDisabled={false}
							/>
						</div>
					</form>
				);
			}}
		</Formik>
	);
};

export default EditUserDetailsForm;
