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

	const MultiSelectChips = ({ label, name, options, value, onChange, description }) => (
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
					return (
						<button
							key={option.id}
							type="button"
							onClick={() => {
								const currentValue = Array.isArray(value) ? value : [value];
								const newValue = isSelected
									? currentValue.filter(v => v !== option.id)
									: [...currentValue, option.id];
								onChange(newValue);
							}}
							className={`px-[12px] py-[6px] rounded-[6px] border font-lato text-[12px] font-medium transition-all duration-200 flex items-center gap-[6px] ${
								isSelected
									? 'border-[#5048ED] bg-[#5048ED] text-white'
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
		const auth_config = {};
		
		// Only include two_factor_auth if it's enabled or has custom settings
		if (tempValues.two_factor_auth.required || tempValues.two_factor_auth.allowedMethods.length > 0) {
			auth_config.two_factor_auth = tempValues.two_factor_auth;
		}
		
		// Remove the original two_factor_auth field
		delete tempValues.two_factor_auth;
		
		let dynamicFormData = transformToFormData(tempValues);
		
		// Add auth_config as JSON if it has content
		if (Object.keys(auth_config).length > 0) {
			dynamicFormData.append('auth_config', JSON.stringify(auth_config));
		}

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
				return (
					<form
						className="complete-hidden-scroll-style flex grow flex-col gap-4 overflow-y-auto"
						onSubmit={formik.handleSubmit}
					>
						<div className="flex grow flex-col gap-[16px]">
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
							<InputField
								key="email"
								label="Email"
								name="email"
								id="email"
								placeholder="Enter"
								value={get(formik.values, 'email', '')}
								onChange={formik.handleChange}
								formik={formik}
							/>
							<div className="flex flex-col gap-[4px]">
								<label
									htmlFor="mobile"
									className="font-lato text-form-xs font-semibold text-[#A3ABB1]"
								>
									Mobile
								</label>
								<div className="flex gap-[12px] rounded-[6px] border border-[#DDE2E5] px-[12px]">
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
										className="font-lato placeholder:text-[#9A9A9A] hover:outline-0 focus:outline-0"
										placeholder="00000 00000"
									/>
								</div>
								{formik.touched.mobile && formik.errors.mobile ? (
									<div className="font-lato text-form-xs text-[#cc3300]">
										{formik.errors.mobile}
									</div>
								) : null}
							</div>
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

							{/* Two-Factor Authentication Section */}
							<div className="space-y-[12px]">
								<h3 className="font-lato text-[14px] font-semibold text-[#111827] border-b border-[#E5E7EB] pb-[8px]">
									Two-Factor Authentication
								</h3>
								<ToggleCard
									title="Require Two-Factor Authentication"
									description="Make 2FA mandatory for this user"
									name="two_factor_auth.required"
									value={get(formik.values, 'two_factor_auth.required', false)}
									onChange={(e) => formik.setFieldValue('two_factor_auth.required', e.target.checked)}
								>
									<MultiSelectChips
										name="two_factor_auth.allowedMethods"
										label="Allowed Methods"
										description="Select available methods for two-factor authentication"
										options={twoFactorMethodOptions}
										value={get(formik.values, 'two_factor_auth.allowedMethods', [])}
										onChange={(value) => formik.setFieldValue('two_factor_auth.allowedMethods', value)}
									/>
								</ToggleCard>
							</div>
						</div>
						<div className="sticky bottom-0 flex flex-col gap-[8px] bg-[#ffffff] pt-[24px] font-lato text-[#696969]">
							<SubmitButton
								label={'Save'}
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
