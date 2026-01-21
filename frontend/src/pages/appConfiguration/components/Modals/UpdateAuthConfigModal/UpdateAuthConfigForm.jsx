import { useState } from "react";
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
	const [setUpdateAuthConfigLoading] = useState(false);

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
		oauth_providers: {
			google: {
				enabled: false,
				client_id: "",
				client_secret: "",
				redirect_uri: "",
			},
			github: {
				enabled: false,
				client_id: "",
				client_secret: "",
				redirect_uri: "",
			},
			microsoft: {
				enabled: false,
				client_id: "",
				client_secret: "",
				redirect_uri: "",
			},
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
		oauth_providers: Yup.object({
			google: Yup.object({
				enabled: Yup.boolean(),
				client_id: Yup.string().when('enabled', {
					is: true,
					then: Yup.string().required('Client ID is required'),
					otherwise: Yup.string()
				}),
				client_secret: Yup.string().when('enabled', {
					is: true,
					then: Yup.string().required('Client Secret is required'),
					otherwise: Yup.string()
				}),
				redirect_uri: Yup.string().when('enabled', {
					is: true,
					then: Yup.string().required('Redirect URI is required'),
					otherwise: Yup.string()
				}),
			}),
			github: Yup.object({
				enabled: Yup.boolean(),
				client_id: Yup.string().when('enabled', {
					is: true,
					then: Yup.string().required('Client ID is required'),
					otherwise: Yup.string()
				}),
				client_secret: Yup.string().when('enabled', {
					is: true,
					then: Yup.string().required('Client Secret is required'),
					otherwise: Yup.string()
				}),
				redirect_uri: Yup.string().when('enabled', {
					is: true,
					then: Yup.string().required('Redirect URI is required'),
					otherwise: Yup.string()
				}),
			}),
			microsoft: Yup.object({
				enabled: Yup.boolean(),
				client_id: Yup.string().when('enabled', {
					is: true,
					then: Yup.string().required('Client ID is required'),
					otherwise: Yup.string()
				}),
				client_secret: Yup.string().when('enabled', {
					is: true,
					then: Yup.string().required('Client Secret is required'),
					otherwise: Yup.string()
				}),
				redirect_uri: Yup.string().when('enabled', {
					is: true,
					then: Yup.string().required('Redirect URI is required'),
					otherwise: Yup.string()
				}),
			}),
		}),
		session_policy: Yup.object({
			max_concurrent_sessions: Yup.number(),
			force_logout_on_password_change: Yup.boolean(),
		}),
		password_policy: Yup.object({
			min_length: Yup.number(),
			allow_change: Yup.boolean(),
			require_numbers: Yup.boolean(),
			require_lowercase: Yup.boolean(),
			require_uppercase: Yup.boolean(),
			require_special_chars: Yup.boolean(),
			password_expiry_days: Yup.number(),
			password_history_count: Yup.number(),
		}),
		two_factor_auth: Yup.object({
			required: Yup.boolean(),
			allowedMethods: Yup.string().required("At least one method is required"),
		}),
	});

	const handleSubmit = async (values) => {
		setUpdateAuthConfigLoading(true);

		try {
			// Separate OAuth providers data from main auth config
			const { oauth_providers, ...authConfigData } = values;

			// TODO: Replace with actual API calls
			// 1. Submit main auth configuration (excluding OAuth providers)
			console.log("Auth config values to be saved:", authConfigData);

			// 2. Submit OAuth providers to separate endpoint /api/v1/apps/<tenant_id>/oauth-providers/
			console.log("OAuth providers data to be saved:", oauth_providers);

			// Simulate API call delay
			await new Promise(resolve => setTimeout(resolve, 1000));

			// Close modal and trigger re-render
			dispatch(toggleRerenderPage());
			closeModal();
		} catch (error) {
			console.error("Error submitting auth configuration:", error);
			// TODO: Show error message to user
		} finally {
			setUpdateAuthConfigLoading(false);
		}
	};

	const usernameOptions = [
		{ id: "email", label: "Email" },
		{ id: "username", label: "Username" },
	];

	const allowedMethodsOptions = [
		{ id: "email", label: "Email" },
		{ id: "sms", label: "SMS" },
	];

	return (
		<Formik
			initialValues={initialValues}
			validationSchema={validationSchema}
			onSubmit={handleSubmit}
		>
			{(formikState) => {
				const { values, setFieldValue, handleSubmit } = formikState;
				return (
					<form
						className="complete-hidden-scroll-style flex grow flex-col overflow-y-auto"
						onSubmit={handleSubmit}
					>
						<div className="flex grow flex-col gap-[20px] pb-[20px] px-[40px] [&_input]:!py-[10px] [&_input]:!text-[13px]">
							{/* Login Methods Section */}
							<div className="space-y-[16px]">
								<h3 className="font-lato text-[14px] font-semibold text-[#111827] border-b border-[#E5E7EB] pb-[8px]">
									Login Methods
								</h3>
								<div className="space-y-[12px]">
									<CheckboxField
										name="login_methods.password.enabled"
										label="Password Authentication"
										value={values.login_methods?.password?.enabled}
										onChange={(e) => setFieldValue("login_methods.password.enabled", e.target.checked)}
										formik={formikState}
									/>
									<CheckboxField
										name="login_methods.otp.enabled"
										label="OTP Authentication"
										value={values.login_methods?.otp?.enabled}
										onChange={(e) => setFieldValue("login_methods.otp.enabled", e.target.checked)}
										formik={formikState}
									/>
									<CheckboxField
										name="login_methods.sso.enabled"
										label="SSO Authentication"
										value={values.login_methods?.sso?.enabled}
										onChange={(e) => setFieldValue("login_methods.sso.enabled", e.target.checked)}
										formik={formikState}
									/>
									<CheckboxField
										name="login_methods.oidc.enabled"
										label="OIDC Authentication"
										value={values.login_methods?.oidc?.enabled}
										onChange={(e) => setFieldValue("login_methods.oidc.enabled", e.target.checked)}
										formik={formikState}
									/>
									<SelectField
										name="login_methods.allowed_usernames"
										label="Allowed Username Type"
										options={usernameOptions}
										value={values.login_methods?.allowed_usernames}
										onChange={(e) => setFieldValue("login_methods.allowed_usernames", e.target.value)}
										formik={formikState}
									/>
								</div>
							</div>

							{/* OAuth Providers Section */}
							<div className="space-y-[16px]">
								<h3 className="font-lato text-[14px] font-semibold text-[#111827] border-b border-[#E5E7EB] pb-[8px]">
									OAuth Providers
								</h3>
								<div className="grid grid-cols-1 md:grid-cols-2 gap-[16px]">
									{/* Google OAuth */}
									<div className="space-y-[12px]">
										<CheckboxField
											name="oauth_providers.google.enabled"
											label="Google OAuth"
											value={values.oauth_providers?.google?.enabled}
											onChange={(e) => setFieldValue("oauth_providers.google.enabled", e.target.checked)}
											formik={formikState}
										/>
										{values.oauth_providers?.google?.enabled && (
											<>
												<InputField
													name="oauth_providers.google.client_id"
													label="Client ID"
													value={values.oauth_providers?.google?.client_id}
													onChange={(e) => setFieldValue("oauth_providers.google.client_id", e.target.value)}
													formik={formikState}
												/>
												<InputField
													name="oauth_providers.google.client_secret"
													label="Client Secret"
													type="password"
													value={values.oauth_providers?.google?.client_secret}
													onChange={(e) => setFieldValue("oauth_providers.google.client_secret", e.target.value)}
													formik={formikState}
												/>
												<InputField
													name="oauth_providers.google.redirect_uri"
													label="Redirect URI"
													value={values.oauth_providers?.google?.redirect_uri}
													onChange={(e) => setFieldValue("oauth_providers.google.redirect_uri", e.target.value)}
													formik={formikState}
												/>
											</>
										)}
									</div>

									{/* GitHub OAuth */}
									<div className="space-y-[12px]">
										<CheckboxField
											name="oauth_providers.github.enabled"
											label="GitHub OAuth"
											value={values.oauth_providers?.github?.enabled}
											onChange={(e) => setFieldValue("oauth_providers.github.enabled", e.target.checked)}
											formik={formikState}
										/>
										{values.oauth_providers?.github?.enabled && (
											<>
												<InputField
													name="oauth_providers.github.client_id"
													label="Client ID"
													value={values.oauth_providers?.github?.client_id}
													onChange={(e) => setFieldValue("oauth_providers.github.client_id", e.target.value)}
													formik={formikState}
												/>
												<InputField
													name="oauth_providers.github.client_secret"
													label="Client Secret"
													type="password"
													value={values.oauth_providers?.github?.client_secret}
													onChange={(e) => setFieldValue("oauth_providers.github.client_secret", e.target.value)}
													formik={formikState}
												/>
												<InputField
													name="oauth_providers.github.redirect_uri"
													label="Redirect URI"
													value={values.oauth_providers?.github?.redirect_uri}
													onChange={(e) => setFieldValue("oauth_providers.github.redirect_uri", e.target.value)}
													formik={formikState}
												/>
											</>
										)}
									</div>

									{/* Microsoft OAuth */}
									<div className="space-y-[12px]">
										<CheckboxField
											name="oauth_providers.microsoft.enabled"
											label="Microsoft OAuth"
											value={values.oauth_providers?.microsoft?.enabled}
											onChange={(e) => setFieldValue("oauth_providers.microsoft.enabled", e.target.checked)}
											formik={formikState}
										/>
										{values.oauth_providers?.microsoft?.enabled && (
											<>
												<InputField
													name="oauth_providers.microsoft.client_id"
													label="Client ID"
													value={values.oauth_providers?.microsoft?.client_id}
													onChange={(e) => setFieldValue("oauth_providers.microsoft.client_id", e.target.value)}
													formik={formikState}
												/>
												<InputField
													name="oauth_providers.microsoft.client_secret"
													label="Client Secret"
													type="password"
													value={values.oauth_providers?.microsoft?.client_secret}
													onChange={(e) => setFieldValue("oauth_providers.microsoft.client_secret", e.target.value)}
													formik={formikState}
												/>
												<InputField
													name="oauth_providers.microsoft.redirect_uri"
													label="Redirect URI"
													value={values.oauth_providers?.microsoft?.redirect_uri}
													onChange={(e) => setFieldValue("oauth_providers.microsoft.redirect_uri", e.target.value)}
													formik={formikState}
												/>
											</>
										)}
									</div>
								</div>
							</div>

							{/* Session Policy Section */}
							<div className="space-y-[16px]">
								<h3 className="font-lato text-[14px] font-semibold text-[#111827] border-b border-[#E5E7EB] pb-[8px]">
									Session Policy
								</h3>
								<div className="grid grid-cols-1 md:grid-cols-2 gap-[16px]">
									<InputField
										name="session_policy.max_concurrent_sessions"
										label="Max Concurrent Sessions"
										type="number"
										value={values.session_policy?.max_concurrent_sessions}
										onChange={(e) => setFieldValue("session_policy.max_concurrent_sessions", parseInt(e.target.value))}
										formik={formikState}
									/>
									<CheckboxField
										name="session_policy.force_logout_on_password_change"
										label="Force Logout on Password Change"
										value={values.session_policy?.force_logout_on_password_change}
										onChange={(e) => setFieldValue("session_policy.force_logout_on_password_change", e.target.checked)}
										formik={formikState}
									/>
								</div>
							</div>

							{/* Password Policy Section */}
							<div className="space-y-[16px]">
								<h3 className="font-lato text-[14px] font-semibold text-[#111827] border-b border-[#E5E7EB] pb-[8px]">
									Password Policy
								</h3>
								<div className="grid grid-cols-1 md:grid-cols-2 gap-[16px]">
									<InputField
										name="password_policy.min_length"
										label="Minimum Length"
										type="number"
										value={values.password_policy?.min_length}
										onChange={(e) => setFieldValue("password_policy.min_length", parseInt(e.target.value))}
										formik={formikState}
									/>
									<InputField
										name="password_policy.password_expiry_days"
										label="Password Expiry Days"
										type="number"
										value={values.password_policy?.password_expiry_days}
										onChange={(e) => setFieldValue("password_policy.password_expiry_days", parseInt(e.target.value))}
										formik={formikState}
									/>
									<InputField
										name="password_policy.password_history_count"
										label="Password History Count"
										type="number"
										value={values.password_policy?.password_history_count}
										onChange={(e) => setFieldValue("password_policy.password_history_count", parseInt(e.target.value))}
										formik={formikState}
									/>
									<CheckboxField
										name="password_policy.allow_change"
										label="Allow Password Change"
										value={values.password_policy?.allow_change}
										onChange={(e) => setFieldValue("password_policy.allow_change", e.target.checked)}
										formik={formikState}
									/>
									<CheckboxField
										name="password_policy.require_numbers"
										label="Require Numbers"
										value={values.password_policy?.require_numbers}
										onChange={(e) => setFieldValue("password_policy.require_numbers", e.target.checked)}
										formik={formikState}
									/>
									<CheckboxField
										name="password_policy.require_lowercase"
										label="Require Lowercase"
										value={values.password_policy?.require_lowercase}
										onChange={(e) => setFieldValue("password_policy.require_lowercase", e.target.checked)}
										formik={formikState}
									/>
									<CheckboxField
										name="password_policy.require_uppercase"
										label="Require Uppercase"
										value={values.password_policy?.require_uppercase}
										onChange={(e) => setFieldValue("password_policy.require_uppercase", e.target.checked)}
										formik={formikState}
									/>
									<CheckboxField
										name="password_policy.require_special_chars"
										label="Require Special Characters"
										value={values.password_policy?.require_special_chars}
										onChange={(e) => setFieldValue("password_policy.require_special_chars", e.target.checked)}
										formik={formikState}
									/>
								</div>
							</div>

							{/* Two-Factor Authentication Section */}
							<div className="space-y-[16px]">
								<h3 className="font-lato text-[14px] font-semibold text-[#111827] border-b border-[#E5E7EB] pb-[8px]">
									Two-Factor Authentication
								</h3>
								<div className="grid grid-cols-1 md:grid-cols-2 gap-[16px]">
									<CheckboxField
										name="two_factor_auth.required"
										label="Require 2FA"
										value={values.two_factor_auth?.required}
										onChange={(e) => setFieldValue("two_factor_auth.required", e.target.checked)}
										formik={formikState}
									/>
									<SelectField
										name="two_factor_auth.allowedMethods"
										label="Allowed Methods"
										options={allowedMethodsOptions}
										value={values.two_factor_auth?.allowedMethods}
										onChange={(e) => setFieldValue("two_factor_auth.allowedMethods", e.target.value)}
										formik={formikState}
									/>
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
								formik={formikState}
								allowDisabled={false}
							/>
						</div>
					</form>
				);
			}}
		</Formik>
	);
};

export default UpdateAuthConfigForm;
