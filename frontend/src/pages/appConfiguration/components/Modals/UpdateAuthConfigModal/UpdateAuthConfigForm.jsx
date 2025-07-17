import React, { useState } from "react";
import { useDispatch } from "react-redux";
import { Formik } from "formik";
import * as Yup from "yup";
import { toggleRerenderPage } from "../../../slice";
import InputField from "../../../../../components/Form/InputField";
import SelectField from "../../../../../components/Form/SelectField";
import CheckboxField from "../../../../../components/Form/CheckboxField";
import SubmitButton from "../../../../../components/Form/SubmitButton";

const UpdateAuthConfigForm = ({ closeModal }) => {
	const dispatch = useDispatch();
	const [updateAuthConfigLoading, setUpdateAuthConfigLoading] = useState(false);
	
	// Mock initial values - will be populated from API later
	const initialValues = {
		login_methods: {
			password: {
				enabled: true,
				forgot_password_enabled: true,
				password_reset_link_expiry_hours: 24,
			},
			otp: {
				enabled: false,
			},
			sso: {
				enabled: false,
			},
			oidc: {
				enabled: false,
			},
			allowed_usernames: "email",
		},
		session_policy: {
			max_concurrent_sessions: 0,
			force_logout_on_password_change: false,
		},
		password_policy: {
			min_length: 8,
			allow_change: true,
			require_numbers: true,
			require_lowercase: true,
			require_uppercase: true,
			require_special_chars: true,
			password_expiry_days: 90,
			password_history_count: 3,
		},
		two_factor_auth: {
			required: true,
			allowedMethods: "email",
		},
	};

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
			allowed_usernames: Yup.string().required("Username type is required"),
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
			allowedMethods: Yup.string().required("At least one method is required"),
		}),
	});

	const handleSubmit = async (values) => {
		setUpdateAuthConfigLoading(true);
		
		// Simulate API call delay
		await new Promise(resolve => setTimeout(resolve, 1000));
		
		// Log the values for now - will be replaced with actual API call later
		console.log("Auth config values to be saved:", values);
		
		// Close modal and trigger re-render
		dispatch(toggleRerenderPage());
		closeModal();
		
		setUpdateAuthConfigLoading(false);
	};

	const usernameOptions = [
		{ id: "email", label: "Email" },
		{ id: "username", label: "Username" },
		{ id: "phone", label: "Phone Number" },
	];

	const twoFactorMethodOptions = [
		{ id: "email", label: "Email" },
		{ id: "sms", label: "SMS" },
		{ id: "authenticator", label: "Authenticator App" },
	];

	return (
		<div className="complete-hidden-scroll-style flex h-[calc(100vh-130px)] max-h-[700px] flex-col gap-[32px] overflow-y-auto px-[20px] pb-[20px]">
			<Formik
				initialValues={initialValues}
				validationSchema={validationSchema}
				onSubmit={handleSubmit}
				enableReinitialize={true}
			>
				{(formik) => {
					const { values, setFieldValue, handleSubmit, isValid, dirty } = formik;
					return (
					<form
						onSubmit={handleSubmit}
						className="flex flex-col gap-[24px]"
					>
						{/* Login Methods Section */}
						<div className="flex flex-col gap-[16px]">
							<div className="flex items-center gap-[8px]">
								<div className="flex h-[24px] w-[24px] items-center justify-center rounded-[4px] bg-[#346BD4]">
									<svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
										<path d="M9 6V4.5C9 2.84315 7.65685 1.5 6 1.5C4.34315 1.5 3 2.84315 3 4.5V6M2.5 6H9.5C9.77614 6 10 6.22386 10 6.5V10.5C10 10.7761 9.77614 11 9.5 11H2.5C2.22386 11 2 10.7761 2 10.5V6.5C2 6.22386 2.22386 6 2.5 6Z" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
									</svg>
								</div>
								<h3 className="font-lato text-[16px] font-bold leading-[20px] text-[#212429]">
									Login Methods
								</h3>
							</div>
							<div className="flex flex-col gap-[16px] rounded-[8px] border border-[#DDE2E5] bg-[#F8F9FA] p-[20px]">
								<CheckboxField
									name="login_methods.password.enabled"
									label="Enable Password Login"
									value={values.login_methods.password.enabled}
									onChange={(e) => setFieldValue("login_methods.password.enabled", e.target.checked)}
								/>
								{values.login_methods.password.enabled && (
									<div className="flex flex-col gap-[16px] rounded-[6px] border border-[#E5E7EB] bg-white p-[16px] ml-[24px]">
										<CheckboxField
											name="login_methods.password.forgot_password_enabled"
											label="Enable Forgot Password"
											value={values.login_methods.password.forgot_password_enabled}
											onChange={(e) => setFieldValue("login_methods.password.forgot_password_enabled", e.target.checked)}
										/>
										<InputField
											name="login_methods.password.password_reset_link_expiry_hours"
											label="Password Reset Link Expiry (Hours)"
											type="number"
											value={values.login_methods.password.password_reset_link_expiry_hours}
											onChange={(e) => setFieldValue("login_methods.password.password_reset_link_expiry_hours", parseInt(e.target.value))}
										/>
									</div>
								)}
								<CheckboxField
									name="login_methods.otp.enabled"
									label="Enable OTP Login"
									value={values.login_methods.otp.enabled}
									onChange={(e) => setFieldValue("login_methods.otp.enabled", e.target.checked)}
								/>
								<CheckboxField
									name="login_methods.sso.enabled"
									label="Enable SSO Login"
									value={values.login_methods.sso.enabled}
									onChange={(e) => setFieldValue("login_methods.sso.enabled", e.target.checked)}
								/>
								<CheckboxField
									name="login_methods.oidc.enabled"
									label="Enable OIDC Login"
									value={values.login_methods.oidc.enabled}
									onChange={(e) => setFieldValue("login_methods.oidc.enabled", e.target.checked)}
								/>
								<SelectField
									name="login_methods.allowed_usernames"
									label="Allowed Username Types"
									optionsData={usernameOptions}
									value={values.login_methods.allowed_usernames || ""}
									placeholder="Select username types"
									formik={{ setFieldValue }}
								/>
							</div>
						</div>

						{/* Session Policy Section */}
						<div className="flex flex-col gap-[16px]">
							<div className="flex items-center gap-[8px]">
								<div className="flex h-[24px] w-[24px] items-center justify-center rounded-[4px] bg-[#346BD4]">
									<svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
										<path d="M6 1V6L9 9" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
										<circle cx="6" cy="6" r="5" stroke="white" strokeWidth="1.5"/>
									</svg>
								</div>
								<h3 className="font-lato text-[16px] font-bold leading-[20px] text-[#212429]">
									Session Policy
								</h3>
							</div>
							<div className="flex flex-col gap-[16px] rounded-[8px] border border-[#DDE2E5] bg-[#F8F9FA] p-[20px]">
								<InputField
									name="session_policy.max_concurrent_sessions"
									label="Max Concurrent Sessions (0 = unlimited)"
									type="number"
									value={values.session_policy.max_concurrent_sessions}
									onChange={(e) => setFieldValue("session_policy.max_concurrent_sessions", parseInt(e.target.value) || 0)}
								/>
								<CheckboxField
									name="session_policy.force_logout_on_password_change"
									label="Force Logout on Password Change"
									value={values.session_policy.force_logout_on_password_change}
									onChange={(e) => setFieldValue("session_policy.force_logout_on_password_change", e.target.checked)}
								/>
							</div>
						</div>

						{/* Password Policy Section */}
						<div className="flex flex-col gap-[16px]">
							<div className="flex items-center gap-[8px]">
								<div className="flex h-[24px] w-[24px] items-center justify-center rounded-[4px] bg-[#346BD4]">
									<svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
										<path d="M8.25 4.5V3.75C8.25 2.09315 6.90685 0.75 5.25 0.75C3.59315 0.75 2.25 2.09315 2.25 3.75V4.5M1.5 4.5H9C9.27614 4.5 9.5 4.72386 9.5 5V9.5C9.5 9.77614 9.27614 10 9 10H1.5C1.22386 10 1 9.77614 1 9.5V5C1 4.72386 1.22386 4.5 1.5 4.5Z" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
										<circle cx="5.25" cy="7.25" r="0.5" fill="white"/>
									</svg>
								</div>
								<h3 className="font-lato text-[16px] font-bold leading-[20px] text-[#212429]">
									Password Policy
								</h3>
							</div>
							<div className="flex flex-col gap-[16px] rounded-[8px] border border-[#DDE2E5] bg-[#F8F9FA] p-[20px]">
								<InputField
									name="password_policy.min_length"
									label="Minimum Password Length"
									type="number"
									value={values.password_policy.min_length}
									onChange={(e) => setFieldValue("password_policy.min_length", parseInt(e.target.value))}
								/>
								<CheckboxField
									name="password_policy.allow_change"
									label="Allow Password Change"
									value={values.password_policy.allow_change}
									onChange={(e) => setFieldValue("password_policy.allow_change", e.target.checked)}
								/>
								<CheckboxField
									name="password_policy.require_numbers"
									label="Require Numbers"
									value={values.password_policy.require_numbers}
									onChange={(e) => setFieldValue("password_policy.require_numbers", e.target.checked)}
								/>
								<CheckboxField
									name="password_policy.require_lowercase"
									label="Require Lowercase Letters"
									value={values.password_policy.require_lowercase}
									onChange={(e) => setFieldValue("password_policy.require_lowercase", e.target.checked)}
								/>
								<CheckboxField
									name="password_policy.require_uppercase"
									label="Require Uppercase Letters"
									value={values.password_policy.require_uppercase}
									onChange={(e) => setFieldValue("password_policy.require_uppercase", e.target.checked)}
								/>
								<CheckboxField
									name="password_policy.require_special_chars"
									label="Require Special Characters"
									value={values.password_policy.require_special_chars}
									onChange={(e) => setFieldValue("password_policy.require_special_chars", e.target.checked)}
								/>
								<InputField
									name="password_policy.password_expiry_days"
									label="Password Expiry (Days)"
									type="number"
									value={values.password_policy.password_expiry_days}
									onChange={(e) => setFieldValue("password_policy.password_expiry_days", parseInt(e.target.value))}
								/>
								<InputField
									name="password_policy.password_history_count"
									label="Password History Count"
									type="number"
									value={values.password_policy.password_history_count}
									onChange={(e) => setFieldValue("password_policy.password_history_count", parseInt(e.target.value))}
								/>
							</div>
						</div>

						{/* Two-Factor Authentication Section */}
						<div className="flex flex-col gap-[16px]">
							<div className="flex items-center gap-[8px]">
								<div className="flex h-[24px] w-[24px] items-center justify-center rounded-[4px] bg-[#346BD4]">
									<svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
										<path d="M6 1L7.5 2.25H10.5V5.25L9 6.75L10.5 8.25V11.25H7.5L6 9.75L4.5 11.25H1.5V8.25L3 6.75L1.5 5.25V2.25H4.5L6 1Z" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
										<circle cx="6" cy="6" r="1.5" stroke="white" strokeWidth="1.5"/>
									</svg>
								</div>
								<h3 className="font-lato text-[16px] font-bold leading-[20px] text-[#212429]">
									Two-Factor Authentication
								</h3>
							</div>
							<div className="flex flex-col gap-[16px] rounded-[8px] border border-[#DDE2E5] bg-[#F8F9FA] p-[20px]">
								<CheckboxField
									name="two_factor_auth.required"
									label="Require Two-Factor Authentication"
									value={values.two_factor_auth.required}
									onChange={(e) => setFieldValue("two_factor_auth.required", e.target.checked)}
								/>
								<SelectField
									name="two_factor_auth.allowedMethods"
									label="Allowed Two-Factor Methods"
									optionsData={twoFactorMethodOptions}
									value={values.two_factor_auth.allowedMethods || ""}
									placeholder="Select two-factor methods"
									formik={{ setFieldValue }}
								/>
							</div>
						</div>

						{/* Submit Button */}
						<div className="sticky bottom-0 flex justify-end border-t border-[#DDE2E5] bg-white pt-[20px]">
							<SubmitButton
								formik={formik}
								label="Save Authentication Configuration"
							/>
						</div>
					</form>
					);
				}}
			</Formik>
		</div>
	);
};

export default UpdateAuthConfigForm;