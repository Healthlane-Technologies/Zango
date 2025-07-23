import React, { useState } from "react";
import { useDispatch } from "react-redux";
import { useNavigate } from "react-router-dom";
import { Formik } from "formik";
import * as Yup from "yup";
import { toggleRerenderPage } from "../../slice";
import InputField from "../../../../components/Form/InputField";
import BreadCrumbs from "../../../app/components/BreadCrumbs";
import { useSelector } from "react-redux";
import { selectAppConfigurationData } from '../../slice';
import useApi from "../../../../hooks/useApi";
import { transformToFormData } from "../../../../utils/form";
import { useParams } from "react-router-dom";

const AuthConfigurationForm = () => {
	const dispatch = useDispatch();
	const navigate = useNavigate();
	const [isSubmitting, setIsSubmitting] = useState(false);
	const triggerApi = useApi();

	const appConfigurationData = useSelector(selectAppConfigurationData);
	const auth_config = appConfigurationData?.app?.auth_config;
	const { appId } = useParams();

	const validationSchema = Yup.object({
		login_methods: Yup.object({
			password: Yup.object({
				enabled: Yup.boolean(),
				forgot_password_enabled: Yup.boolean(),
				password_reset_link_expiry_hours: Yup.number()
					.min(1, "Must be at least 1 hour")
					.max(168, "Must be less than 168 hours (7 days)"),
			}),
			otp: Yup.object({
				enabled: Yup.boolean(),
			}),
			sso: Yup.object({
				enabled: Yup.boolean(),
			}),
			oidc: Yup.object({
				enabled: Yup.boolean(),
			}),
			allowed_usernames: Yup.array().min(1, "At least one username type is required"),
		}),
		session_policy: Yup.object({
			max_concurrent_sessions: Yup.number().min(0, "Cannot be negative"),
			force_logout_on_password_change: Yup.boolean(),
		}),
		password_policy: Yup.object({
			min_length: Yup.number().min(4, "Minimum length must be at least 4").max(128, "Maximum length is 128"),
			allow_change: Yup.boolean(),
			require_numbers: Yup.boolean(),
			require_lowercase: Yup.boolean(),
			require_uppercase: Yup.boolean(),
			require_special_chars: Yup.boolean(),
			password_expiry_days: Yup.number().min(1, "Must be at least 1 day").max(365, "Must be less than 365 days"),
			password_history_count: Yup.number().min(0, "Cannot be negative").max(24, "Maximum is 24"),
		}),
		two_factor_auth: Yup.object({
			required: Yup.boolean(),
			allowedMethods: Yup.array().min(1, "At least one method is required"),
		}),
	});

	let onSubmit = (values) => {
		const cleanedAuthConfig = values;
		
		if (Object.keys(cleanedAuthConfig).length === 0) {
			console.warn('No configuration changes to save');
			return;
		}
		
		const tempValues = {
			auth_config: JSON.stringify(cleanedAuthConfig)
		};

		const dynamicFormData = transformToFormData(tempValues);

		const makeApiCall = async () => {
			setIsSubmitting(true);
			try {
				const { response, success } = await triggerApi({
					url: `/api/v1/apps/${appId}/`,
					type: 'PUT',
					loader: true,
					payload: dynamicFormData,
				});

				if (success && response) {
					dispatch(toggleRerenderPage());
					window.location.reload();
				}
			} catch (error) {
				console.error('Error saving configuration:', error);
			} finally {
				setIsSubmitting(false);
			}
		};

		makeApiCall();
	};

	const handleCancel = () => {
		navigate(-1);
	};

	const usernameOptions = [
		{ id: "email", label: "Email" },
		{ id: "phone", label: "Phone Number" },
	];

	const passwordResetOptions = [
		{ id: "email", label: "Email" },
		{ id: "sms", label: "SMS" },
	]

	const loginOTPMethodOptions = [
		{ id: "email", label: "Email" },
		{ id: "sms", label: "SMS" },
	];

	const twoFactorMethodOptions = [
		{ id: "email", label: "Email" },
		{ id: "sms", label: "SMS" },
	];

	const MultiSelectChips = ({ label, name, options, value, onChange, description, disabledOptions = [], requiredOptions = [] }) => (
		<div className="space-y-[16px]">
			<div>
				<label className="font-source-sans-pro text-[14px] font-semibold text-[#111827] mb-[4px] block">
					{label}
				</label>
				{description && (
					<p className="font-lato text-[13px] leading-[18px] text-[#6B7280]">
						{description}
					</p>
				)}
			</div>
			<div className="flex flex-wrap gap-[12px]">
				{options.map((option) => {
					const isSelected = Array.isArray(value) ? value.includes(option.id) : value === option.id;
					const isDisabled = disabledOptions.includes(option.id);
					const isRequired = requiredOptions.includes(option.id);
					const cannotUnselect = isRequired && isSelected;
					return (
						<button
							key={option.id}
							type="button"
							disabled={isDisabled}
							onClick={() => {
								if (isDisabled) return;
								if (cannotUnselect) return; // Prevent unselecting required options
								const currentValue = Array.isArray(value) ? value : [value];
								const newValue = isSelected
									? currentValue.filter(v => v !== option.id)
									: [...currentValue, option.id];
								onChange(newValue);
							}}
							className={`relative px-[20px] py-[12px] rounded-[10px] border-2 font-lato text-[14px] font-medium transition-all duration-200 flex items-center gap-[8px] transform hover:scale-[1.02] ${
								isDisabled
									? 'border-[#E5E7EB] bg-[#F3F4F6] text-[#9CA3AF] cursor-not-allowed opacity-50'
									: cannotUnselect
									? 'border-[#5048ED] bg-[#5048ED] text-white shadow-lg cursor-not-allowed'
									: isSelected
									? 'border-[#5048ED] bg-[#5048ED] text-white shadow-lg'
									: 'border-[#E5E7EB] bg-white text-[#6B7280] hover:border-[#5048ED] hover:bg-[#F8FAFC] hover:shadow-md'
							}`}
						>
							{isSelected && (
								<>
									<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
										<path d="M13.5 4.5L6 12L2.5 8.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
									</svg>
									<div className="absolute -top-[2px] -right-[2px] w-[8px] h-[8px] bg-[#10B981] rounded-full border-2 border-white"></div>
								</>
							)}
							{option.label}
						</button>
					);
				})}
			</div>
		</div>
	);

	const ToggleSwitch = ({ checked, onChange, disabled = false }) => (
		<button
			type="button"
			onClick={() => !disabled && onChange(!checked)}
			disabled={disabled}
			className={`relative inline-flex h-[24px] w-[44px] items-center rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-[#5048ED] focus:ring-offset-2 ${
				checked 
					? 'bg-[#5048ED] shadow-md' 
					: 'bg-[#E5E7EB] hover:bg-[#D1D5DB]'
			} ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
		>
			<span
				className={`inline-block h-[20px] w-[20px] transform rounded-full bg-white shadow-lg transition-transform duration-200 ${
					checked ? 'translate-x-[22px]' : 'translate-x-[2px]'
				}`}
			/>
		</button>
	);

	const ToggleCard = ({ title, description, name, value, onChange, children, disabled = false }) => (
		<div className={`group rounded-[12px] border-2 transition-all duration-300 hover:shadow-md ${
			value 
				? 'border-[#5048ED] bg-gradient-to-br from-[#EFF6FF] to-[#DBEAFE] shadow-sm' 
				: 'border-[#E5E7EB] bg-white hover:border-[#D1D5DB]'
		}`}>
			<div className="p-[20px]">
				<div className="flex items-start justify-between">
					<div className="flex-1 mr-[16px]">
						<div className="flex items-center gap-[12px] mb-[4px]">
							<h4 className={`font-source-sans-pro text-[16px] font-semibold leading-[24px] transition-colors duration-200 ${
								value ? 'text-[#5048ED]' : 'text-[#111827]'
							}`}>
								{title}
							</h4>
							{value && (
								<span className="inline-flex items-center gap-[4px] px-[8px] py-[2px] rounded-full bg-[#5048ED] text-white text-[10px] font-medium">
									<svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
										<path d="M10 3L4.5 8.5L2 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
									</svg>
									ACTIVE
								</span>
							)}
						</div>
						{description && (
							<p className={`font-lato text-[13px] leading-[18px] transition-colors duration-200 ${
								value ? 'text-[#5048ED]/80' : 'text-[#6B7280]'
							}`}>
								{description}
							</p>
						)}
					</div>
					<div className="flex-shrink-0">
						<ToggleSwitch
							checked={value}
							onChange={(checked) => onChange({ target: { checked } })}
							disabled={disabled}
						/>
					</div>
				</div>
				{value && children && (
					<div className="mt-[20px] pt-[16px] border-t border-[#5048ED]/20 space-y-[16px]">
						{children}
					</div>
				)}
			</div>
		</div>
	);

	const [activeTab, setActiveTab] = useState("login");

	const tabs = [
		{ id: "login", label: "Login Methods", icon: "🔐" },
		{ id: "session", label: "Session Policy", icon: "⏰" },
		{ id: "password", label: "Password Policy", icon: "🔒" },
		{ id: "2fa", label: "Two-Factor Auth", icon: "🛡️" }
	];

	// Show loading state while data is being fetched
	if (!appConfigurationData || !auth_config) {
		return (
			<div className="min-h-screen bg-gradient-to-br from-[#F8FAFC] to-[#E2E8F0] flex items-center justify-center">
				<div className="text-center">
					<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#5048ED] mx-auto mb-4"></div>
					<p className="text-[#6B7280] font-lato">Loading configuration...</p>
				</div>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-gradient-to-br from-[#F8FAFC] to-[#E2E8F0]">
			{/* Header */}
			<div className="bg-white border-b border-[#E5E7EB] px-[40px] py-[20px] shadow-sm">
				<BreadCrumbs />
				<div className="flex items-center justify-between mt-[12px]">
					<div className="flex items-center gap-[16px]">
						<div className="flex h-[48px] w-[48px] items-center justify-center rounded-[12px] bg-[#5048ED] shadow-lg">
							<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
								<path d="M18 12V10C18 6.68629 15.3137 4 12 4C8.68629 4 6 6.68629 6 10V12M5 12H19C19.5523 12 20 12.4477 20 13V20C20 20.5523 19.5523 21 19 21H5C4.44772 21 4 20.5523 4 20V13C4 12.4477 4.44772 12 5 12Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
							</svg>
						</div>
						<div>
							<h1 className="font-source-sans-pro text-[28px] font-bold leading-[36px] text-[#111827]">
								Authentication Settings
							</h1>
							<p className="font-lato text-[16px] leading-[24px] text-[#6B7280]">
								Configure security policies and authentication methods
							</p>
						</div>
					</div>
					<div className="flex gap-[12px]">
						<button
							type="button"
							onClick={handleCancel}
							className="px-[24px] py-[12px] border-2 border-[#E5E7EB] text-[#6B7280] bg-white rounded-[10px] font-semibold text-[16px] hover:border-[#D1D5DB] hover:bg-[#F9FAFB] transition-all duration-200"
						>
							Cancel
						</button>
						<button
							type="submit"
							form="auth-config-form"
							disabled={isSubmitting}
							className="px-[24px] py-[12px] bg-[#5048ED] text-white rounded-[10px] font-semibold text-[16px] hover:bg-[#3d38c7] transition-all duration-200 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
						>
							{isSubmitting ? 'Saving...' : 'Save Changes'}
						</button>
					</div>
				</div>
			</div>

			{/* Main Content */}
			<div className="flex">
				{/* Sidebar Tabs */}
				<div className="w-[280px] bg-white border-r border-[#E5E7EB] min-h-screen shadow-sm">
					<div className="p-[24px]">
						<h3 className="font-source-sans-pro text-[18px] font-semibold text-[#111827] mb-[16px]">
							Configuration Sections
						</h3>
						<div className="space-y-[8px]">
							{tabs.map((tab) => (
								<button
									key={tab.id}
									onClick={() => setActiveTab(tab.id)}
									className={`w-full flex items-center gap-[12px] px-[16px] py-[12px] rounded-[8px] text-left font-medium transition-all duration-200 ${
										activeTab === tab.id
											? 'bg-[#5048ED] text-white shadow-md'
											: 'text-[#6B7280] hover:bg-[#F8FAFC] hover:text-[#111827]'
									}`}
								>
									<span className="text-[20px]">{tab.icon}</span>
									<span className="font-lato text-[14px]">{tab.label}</span>
								</button>
							))}
						</div>
					</div>
				</div>

				{/* Content Area */}
				<div className="flex-1 p-[40px]">
					<Formik
						initialValues={auth_config}
						validationSchema={validationSchema}
						onSubmit={onSubmit}
						enableReinitialize={true}
					>
						{(formik) => {
							const { values, setFieldValue, handleSubmit, isValid, dirty } = formik;
							
							const renderTabContent = () => {
								switch (activeTab) {
									case "login":
										return (
											<div className="space-y-[32px]">
												<div className="bg-white rounded-[16px] shadow-lg border border-[#E5E7EB] p-[32px]">
													<div className="flex items-center gap-[16px] mb-[24px]">
														<div className="flex h-[40px] w-[40px] items-center justify-center rounded-[10px] bg-[#5048ED]">
															<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
																<path d="M15 10V8C15 5.23858 12.7614 3 10 3C7.23858 3 5 5.23858 5 8V10M4 10H16C16.5523 10 17 10.4477 17 11V17C17 17.5523 16.5523 18 16 18H4C3.44772 18 3 17.5523 3 17V11C3 10.4477 3.44772 10 4 10Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
															</svg>
														</div>
														<div>
															<h2 className="font-source-sans-pro text-[20px] font-bold text-[#111827]">Login Methods</h2>
															<p className="font-lato text-[14px] text-[#6B7280]">Configure available authentication methods</p>
														</div>
													</div>
													
													<div className="space-y-[24px]">
															<ToggleCard
																title="Password Authentication"
																description="Allow users to log in with email/username and password"
																name="login_methods.password.enabled"
																value={values?.login_methods?.password?.enabled}
																onChange={(e) => setFieldValue("login_methods.password.enabled", e.target.checked)}
															>
																
																<div className="max-w-2xl">
																	<MultiSelectChips
																		name="login_methods.password.allowed_usernames"
																		label="Allowed Username Types"
																		description="Select the types of username users can use to log in"
																		options={usernameOptions}
																		value={values?.login_methods?.password?.allowed_usernames || []}
																		onChange={(value) => setFieldValue("login_methods.password.allowed_usernames", value)}
																	/>
																</div>
																
																<div className="grid grid-cols-1 md:grid-cols-2 gap-[20px]">
																	
																	<ToggleCard
																		title="Forgot Password"
																		description="Enable password reset functionality"
																		name="password_policy.reset.enabled"
																		value={values?.password_policy?.reset?.enabled}
																		onChange={(e) => setFieldValue("password_policy.reset.enabled", e.target.checked)}
																	>
																		<div className="space-y-[16px]">
																			<label className="font-source-sans-pro text-[14px] font-semibold text-[#111827] mb-[4px] block">
																				Reset Method Type
																			</label>
																			<div className="flex gap-[12px]">
																				<button
																					type="button"
																					onClick={() => {
																						setFieldValue("password_policy.reset.by_code", true);
																						setFieldValue("password_policy.reset.by_email", false);
																					}}
																					className={`px-[20px] py-[12px] rounded-[10px] border-2 font-lato text-[14px] font-medium transition-all duration-200 flex items-center gap-[8px] transform hover:scale-[1.02] ${
																						values?.password_policy?.reset?.by_code === true
																							? 'border-[#5048ED] bg-[#5048ED] text-white shadow-lg'
																							: 'border-[#E5E7EB] bg-white text-[#6B7280] hover:border-[#5048ED] hover:bg-[#F8FAFC] hover:shadow-md'
																					}`}
																				>
																					Code
																				</button>
																				<button
																					type="button"
																					onClick={() => {
																						setFieldValue("password_policy.reset.by_email", true);
																						setFieldValue("password_policy.reset.by_code", false);
																						// When link is selected, ensure email is selected and remove SMS
																						setFieldValue("password_policy.reset.allowed_methods", ["email"]);
																					}}
																					className={`px-[20px] py-[12px] rounded-[10px] border-2 font-lato text-[14px] font-medium transition-all duration-200 flex items-center gap-[8px] transform hover:scale-[1.02] ${
																						values?.password_policy?.reset?.by_email === true
																							? 'border-[#5048ED] bg-[#5048ED] text-white shadow-lg'
																							: 'border-[#E5E7EB] bg-white text-[#6B7280] hover:border-[#5048ED] hover:bg-[#F8FAFC] hover:shadow-md'
																					}`}
																				>
																					Link
																				</button>
																			</div>
																			<p className="font-lato text-[13px] leading-[18px] text-[#6B7280]">
																				Choose whether users receive a code to enter or a direct reset link
																			</p>
																		</div>
																		<InputField
																			name="password_policy.reset.expiry"
																			label="Reset Link Expiry (Seconds)"
																			type="number"
																			value={values?.password_policy?.reset?.expiry}
																			onChange={(e) => setFieldValue("password_policy.reset.expiry", parseInt(e.target.value))}
																		/>
																		<MultiSelectChips
																			name="password_policy.reset.allowed_methods"
																			label="Password reset methods"
																			description="Select the method which user can use to get forgot password code/link"
																			options={passwordResetOptions}
																			value={values?.password_policy?.reset?.allowed_methods || []}
																			onChange={(value) => {
																				setFieldValue("password_policy.reset.allowed_methods", value);
																			}}
																			disabledOptions={values?.password_policy?.reset?.by_email === true ? ["sms"] : []}
																			requiredOptions={values?.password_policy?.reset?.by_email === true ? ["email"] : []}
																		/>
																		<ToggleCard
																			title="Login After Reset"
																			description="Automatically log in users after successful password reset"
																			name="password_policy.reset.login_after_reset"
																			value={values?.password_policy?.reset?.login_after_reset}
																			onChange={(e) => setFieldValue("password_policy.reset.login_after_reset", e.target.checked)}
																		/>
																	</ToggleCard>
																	
																</div>
															</ToggleCard>

														<div className="grid grid-cols-1 md:grid-cols-3 gap-[20px]">
															<div>
																<ToggleCard
																	title="OTP Authentication"
																	description="One Time Password integration"
																	name="login_methods.otp.enabled"
																	value={values?.login_methods?.otp?.enabled}
																	onChange={(e) => setFieldValue("login_methods.otp.enabled", e.target.checked)}
																>
																	<MultiSelectChips
																		name="login_methods.otp.allowed_methods"
																		label="Allowed OTP Methods"
																		description="Select the types of OTP methods allowed for login"
																		options={loginOTPMethodOptions}
																		value={values?.login_methods?.otp?.allowed_methods || []}
																		onChange={(value) => setFieldValue("login_methods.otp.allowed_methods", value)}
																	/>
																</ToggleCard>

															</div>
															<ToggleCard
																title="SSO Authentication"
																description="Single Sign-On integration"
																name="login_methods.sso.enabled"
																value={values?.login_methods?.sso?.enabled}
																onChange={(e) => setFieldValue("login_methods.sso.enabled", e.target.checked)}
															/>
															<ToggleCard
																title="OIDC Authentication"
																description="OpenID Connect integration"
																name="login_methods.oidc.enabled"
																value={values?.login_methods?.oidc?.enabled}
																onChange={(e) => setFieldValue("login_methods.oidc.enabled", e.target.checked)}
															/>
														</div>
													</div>
												</div>
											</div>
										);
									
									case "session":
										return (
											<div className="space-y-[32px]">
												<div className="bg-white rounded-[16px] shadow-lg border border-[#E5E7EB] p-[32px]">
													<div className="flex items-center gap-[16px] mb-[24px]">
														<div className="flex h-[40px] w-[40px] items-center justify-center rounded-[10px] bg-[#5048ED]">
															<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
																<path d="M10 2V10L15 15" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
																<circle cx="10" cy="10" r="8" stroke="white" strokeWidth="2"/>
															</svg>
														</div>
														<div>
															<h2 className="font-source-sans-pro text-[20px] font-bold text-[#111827]">Session Policy</h2>
															<p className="font-lato text-[14px] text-[#6B7280]">Configure session management settings</p>
														</div>
													</div>
													
													
													<div className="grid grid-cols-1 md:grid-cols-2 gap-[24px]">
														<InputField
															name="session_policy.max_concurrent_sessions"
															label="Max Concurrent Sessions"
															type="number"
															value={values?.session_policy?.max_concurrent_sessions}
															onChange={(e) => setFieldValue("session_policy.max_concurrent_sessions", parseInt(e.target.value) || 0)}
														/>
														<ToggleCard
															title="Force Logout on Password Change"
															description="Automatically log out all sessions when password changes"
															name="session_policy.force_logout_on_password_change"
															value={values?.session_policy?.force_logout_on_password_change}
															onChange={(e) => setFieldValue("session_policy.force_logout_on_password_change", e.target.checked)}
														/>
													</div>
												</div>
											</div>
										);
									
									case "password":
										return (
											<div className="space-y-[32px]">
												<div className="bg-white rounded-[16px] shadow-lg border border-[#E5E7EB] p-[32px]">
													<div className="flex items-center gap-[16px] mb-[24px]">
														<div className="flex h-[40px] w-[40px] items-center justify-center rounded-[10px] bg-[#5048ED]">
															<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
																<path d="M14 8V6C14 3.79086 12.2091 2 10 2C7.79086 2 6 3.79086 6 6V8M5 8H15C15.5523 8 16 8.44772 16 9V16C16 16.5523 15.5523 17 15 17H5C4.44772 17 4 16.5523 4 16V9C4 8.44772 4.44772 8 5 8Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
																<circle cx="10" cy="12.5" r="1.5" fill="white"/>
															</svg>
														</div>
														<div>
															<h2 className="font-source-sans-pro text-[20px] font-bold text-[#111827]">Password Policy</h2>
															<p className="font-lato text-[14px] text-[#6B7280]">Define password requirements and security rules</p>
														</div>
													</div>
													

													<div className="space-y-[24px]">
														<div className="grid grid-cols-1 md:grid-cols-2 gap-[24px]">
															<InputField
																name="password_policy.min_length"
																label="Minimum Password Length"
																type="number"
																value={values?.password_policy?.min_length}
																onChange={(e) => setFieldValue("password_policy.min_length", parseInt(e.target.value))}
															/>
															<InputField
																name="password_policy.password_expiry_days"
																label="Password Expiry (Days)"
																type="number"
																value={values?.password_policy?.password_expiry_days}
																onChange={(e) => setFieldValue("password_policy.password_expiry_days", parseInt(e.target.value))}
															/>
														</div>

														<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-[20px]">
															<ToggleCard
																title="Allow Password Change"
																description="Users can change their passwords"
																name="password_policy.allow_change"
																value={values?.password_policy?.allow_change}
																onChange={(e) => setFieldValue("password_policy.allow_change", e.target.checked)}
															/>
															<ToggleCard
																title="Require Numbers"
																description="Passwords must contain numbers"
																name="password_policy.require_numbers"
																value={values?.password_policy?.require_numbers}
																onChange={(e) => setFieldValue("password_policy.require_numbers", e.target.checked)}
															/>
															<ToggleCard
																title="Require Lowercase"
																description="Passwords must contain lowercase letters"
																name="password_policy.require_lowercase"
																value={values?.password_policy?.require_lowercase}
																onChange={(e) => setFieldValue("password_policy.require_lowercase", e.target.checked)}
															/>
															<ToggleCard
																title="Require Uppercase"
																description="Passwords must contain uppercase letters"
																name="password_policy.require_uppercase"
																value={values?.password_policy?.require_uppercase}
																onChange={(e) => setFieldValue("password_policy.require_uppercase", e.target.checked)}
															/>
															<ToggleCard
																title="Require Special Characters"
																description="Passwords must contain special characters"
																name="password_policy.require_special_chars"
																value={values?.password_policy?.require_special_chars}
																onChange={(e) => setFieldValue("password_policy.require_special_chars", e.target.checked)}
															/>
														</div>


														<div className="max-w-md">
															<InputField
																name="password_policy.password_history_count"
																label="Password History Count"
																type="number"
																value={values?.password_policy?.password_history_count}
																onChange={(e) => setFieldValue("password_policy.password_history_count", parseInt(e.target.value))}
															/>
														</div>

													</div>
												</div>
											</div>
										);
									
									case "2fa":
										return (
											<div className="space-y-[32px]">
												<div className="bg-white rounded-[16px] shadow-lg border border-[#E5E7EB] p-[32px]">
													<div className="flex items-center gap-[16px] mb-[24px]">
														<div className="flex h-[40px] w-[40px] items-center justify-center rounded-[10px] bg-[#5048ED]">
															<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
																<path d="M10 2L12.5 4.5H17.5V9.5L15 12L17.5 14.5V19.5H12.5L10 17L7.5 19.5H2.5V14.5L5 12L2.5 9.5V4.5H7.5L10 2Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
																<circle cx="10" cy="10" r="2.5" stroke="white" strokeWidth="2"/>
															</svg>
														</div>
														<div>
															<h2 className="font-source-sans-pro text-[20px] font-bold text-[#111827]">Two-Factor Authentication</h2>
															<p className="font-lato text-[14px] text-[#6B7280]">Configure additional security layer</p>
														</div>
													</div>

														<div className="space-y-[24px]">
																<ToggleCard
																	title="Require Two-Factor Authentication"
																	description="Make 2FA mandatory for all users"
																	name="two_factor_auth.required"
																	value={values?.two_factor_auth?.required}
																	onChange={(e) => setFieldValue("two_factor_auth.required", e.target.checked)}
																>
																	<div className="space-y-[24px]">
																		
																			<div className="max-w-2xl">
																				<MultiSelectChips
																					name="two_factor_auth.allowed_methods"
																					label="Allowed Two-Factor Methods"
																					description="Select available methods for two-factor authentication"
																					options={twoFactorMethodOptions}
																					value={values?.two_factor_auth?.allowed_methods || []}
																					onChange={(value) => setFieldValue("two_factor_auth.allowed_methods", value)}
																				/>
																			</div>
																		
																		
																		<div className="max-w-2xl">
																			<InputField
																				name="two_factor_auth.email_hook"
																				label="Email Hook URL"
																				description="Webhook URL for email-based two-factor authentication"
																				type="url"
																				placeholder="https://your-domain.com/email-2fa-hook"
																				value={values?.two_factor_auth?.email_hook || ""}
																				onChange={(e) => setFieldValue("two_factor_auth.email_hook", e.target.value)}
																			/>
																		</div>
																		
																		<div className="max-w-2xl">
																			<InputField
																				name="two_factor_auth.sms_hook"
																				label="SMS Hook URL"
																				description="Webhook URL for SMS-based two-factor authentication"
																				type="url"
																				placeholder="https://your-domain.com/sms-2fa-hook"
																				value={values?.two_factor_auth?.sms_hook || ""}
																				onChange={(e) => setFieldValue("two_factor_auth.sms_hook", e.target.value)}
																			/>
																		</div>
																	</div>
																</ToggleCard>
														</div>
												</div>
											</div>
										);
									
									default:
										return null;
								}
							};
							
							return (
								<form id="auth-config-form" onSubmit={handleSubmit}>
									{renderTabContent()}
								</form>
							);
						}}
					</Formik>
				</div>
			</div>
		</div>
	);
};

export default AuthConfigurationForm;
