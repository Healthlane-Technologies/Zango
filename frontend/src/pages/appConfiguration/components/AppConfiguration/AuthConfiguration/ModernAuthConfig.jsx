import { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Formik } from 'formik';
import * as Yup from 'yup';
import { selectAppConfigurationData, toggleRerenderPage } from '../../../slice';
import useApi from '../../../../../hooks/useApi';
import { transformToFormData } from '../../../../../utils/form';
import { useParams, useNavigate } from 'react-router-dom';
import InputField from '../../../../../components/Form/InputField';
import AuthSetupModal from './AuthSetupModal';
import RoleOverrideModal from './RoleOverrideModal';
import SAMLProviderModal from './SAMLProviderModal';

const ModernAuthConfig = () => {
	const [activeSection, setActiveSection] = useState('overview');
	const [isEditMode, setIsEditMode] = useState(false);
	const [isSaving, setIsSaving] = useState(false);
	const [roles, setRoles] = useState([]);
	const [loadingRoles, setLoadingRoles] = useState(true);
	const [showAuthSetupModal, setShowAuthSetupModal] = useState(false);
	const [showRoleOverrideModal, setShowRoleOverrideModal] = useState(false);
	const [selectedRoleForOverride, setSelectedRoleForOverride] = useState(null);
	const [showSAMLModal, setShowSAMLModal] = useState(false);
	const [samlProviders, setSAMLProviders] = useState([]);
	const [loadingSAML, setLoadingSAML] = useState(false);
	const [editingSAMLProvider, setEditingSAMLProvider] = useState(null);
	const dispatch = useDispatch();
	const triggerApi = useApi();
	const { appId } = useParams();
	const navigate = useNavigate();
	
	const appConfigurationData = useSelector(selectAppConfigurationData);
	
	// Fetch roles data
	useEffect(() => {
		const fetchRoles = async () => {
			setLoadingRoles(true);
			try {
				const { response, success } = await triggerApi({
					url: `/api/v1/apps/${appId}/roles/?page=1&page_size=100`,
					type: 'GET',
					loader: false,
				});
				if (success && response) {
					// Filter out system/reserved roles to get only user-defined roles
					const reservedRoleNames = ['AnonymousUsers', 'SystemUsers'];
					const allRoles = response?.roles?.records || [];
					const userDefinedRoles = allRoles.filter(role =>
						!reservedRoleNames.includes(role.name)
					);
					setRoles(userDefinedRoles);
				}
			} catch (error) {
				console.error('Error fetching roles:', error);
			} finally {
				setLoadingRoles(false);
			}
		};

		if (appId) {
			fetchRoles();
		}
	}, [appId, triggerApi]);

	// Fetch SAML providers
	useEffect(() => {
		const fetchSAMLProviders = async () => {
			setLoadingSAML(true);
			try {
				const { response, success } = await triggerApi({
					url: `/api/v1/apps/${appId}/saml-providers/`,
					type: 'GET',
					loader: false,
				});
				if (success && response) {
					setSAMLProviders(response.saml_providers || []);
				}
			} catch (error) {
				console.error('Error fetching SAML providers:', error);
			} finally {
				setLoadingSAML(false);
			}
		};

		if (appId) {
			fetchSAMLProviders();
		}
	}, [appId, triggerApi]);
	
	if (!appConfigurationData) {
		return (
			<div className="flex items-center justify-center h-64">
				<div className="text-center">
					<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#5048ED] mx-auto mb-4"></div>
					<p className="text-[#6B7280]">Loading authentication configuration...</p>
				</div>
			</div>
		);
	}

	const authConfig = appConfigurationData?.app?.auth_config;
	
	// Check if authentication has been configured
	const isAuthConfigured = () => {		
		if (!authConfig || Object.keys(authConfig).length === 0) return false;
		
		// Check if auth_config has the expected structure
		// If it has login_methods and password_policy, it's been configured
		return !!(authConfig.login_methods && authConfig.password_policy);
	};

	// Show setup state if auth is not configured
	if (!authConfig || (!isAuthConfigured() && roles.length > 0)) {
		return (
			<>
				<div className="max-w-[800px] mx-auto mt-[40px]">
					<div className="bg-white rounded-[16px] border border-[#E5E7EB] p-[48px] text-center">
						<div className="w-[80px] h-[80px] bg-gradient-to-br from-[#5048ED] to-[#346BD4] rounded-full flex items-center justify-center mx-auto mb-[24px]">
							<svg width="40" height="40" viewBox="0 0 40 40" fill="none">
								<path d="M28 20V16.667C28 11.144 23.522 6.667 18 6.667C12.478 6.667 8 11.144 8 16.667V20M6 20H30C31.105 20 32 20.895 32 22V32C32 33.105 31.105 34 30 34H6C4.895 34 4 33.105 4 32V22C4 20.895 4.895 20 6 20Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
							</svg>
						</div>
						<h3 className="text-[24px] font-semibold text-[#111827] mb-[8px]">Setup Authentication</h3>
						<p className="text-[16px] text-[#6B7280] mb-[32px]">Configure how users sign in and access your application</p>
						<button
							onClick={() => setShowAuthSetupModal(true)}
							className="inline-flex items-center gap-[8px] px-[24px] py-[12px] bg-[#5048ED] text-white rounded-[12px] hover:bg-[#4338CA] transition-colors text-[16px] font-medium shadow-lg hover:shadow-xl transform hover:scale-[1.02]"
						>
							<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
								<path d="M10 5V15M5 10H15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
							</svg>
							Setup Auth Now
						</button>
					</div>
				</div>
				
				{/* Auth Setup Modal */}
				<AuthSetupModal
					show={showAuthSetupModal}
					onClose={() => setShowAuthSetupModal(false)}
					roles={roles}
					onComplete={async (authData) => {
						// Transform to expected format matching the schema
						const authConfig = {
							login_methods: {
								password: {
									enabled: authData.login_methods.password.enabled,
									forgot_password_enabled: authData.login_methods.password.forgot_password_enabled,
									password_reset_link_expiry_hours: 24, // Default
									allowed_usernames: authData.login_methods.allowed_usernames,
								},
								otp: {
									enabled: authData.login_methods.otp.enabled,
									allowed_methods: authData.login_methods.otp.allowed_methods || [],
									email_content: authData.login_methods.otp.email_content || '',
									email_subject: authData.login_methods.otp.email_subject || '',
									email_hook: authData.login_methods.otp.email_webhook || '',
									email_config_key: authData.login_methods.otp.email_config_key || '',
									sms_hook: authData.login_methods.otp.sms_webhook || '',
									sms_content: authData.login_methods.otp.sms_content || '',
									sms_config_key: authData.login_methods.otp.sms_config_key || '',
									sms_extra_data: authData.login_methods.otp.sms_extra_data || '',
									otp_expiry: authData.login_methods.otp.otp_expiry || 300,
								},
								sso: { enabled: authData.login_methods.sso.enabled },
								oidc: { enabled: authData.login_methods.oidc.enabled },
							},
							session_policy: {
								max_concurrent_sessions: authData.session_policy.max_concurrent_sessions,
							},
							password_policy: {
								min_length: authData.password_policy.min_length,
								allow_change: authData.password_policy.allow_change,
								require_numbers: authData.password_policy.require_numbers,
								require_lowercase: authData.password_policy.require_lowercase,
								require_uppercase: authData.password_policy.require_uppercase,
								password_expiry_days: authData.password_policy.password_expiry_days,
								password_repeat_days: authData.password_policy.password_repeat_days,
								require_special_chars: authData.password_policy.require_special_chars,
								password_history_count: authData.password_policy.password_history_count,
								reset: {
									enabled: authData.login_methods.password.forgot_password_enabled,
									expiry: authData.login_methods.password.reset_expiry_minutes * 60, // Convert minutes to seconds
									allowed_methods: (() => {
										const methods = [];
										if (authData.login_methods.password.reset_via_email) methods.push('email');
										if (authData.login_methods.password.reset_via_sms) methods.push('sms');
										return methods.length > 0 ? methods : ['email'];
									})(),
									by_code: authData.login_methods.password.reset_method === 'code',
									by_email: authData.login_methods.password.reset_via_email || false,
									login_after_reset: false,
									max_attempts: 3,
									email_hook: authData.login_methods.password.reset_email_webhook || '',
									email_content: authData.login_methods.password.reset_email_content || '',
									email_subject: authData.login_methods.password.reset_email_subject || '',
									email_config_key: authData.login_methods.password.reset_email_config_key || '',
									sms_hook: authData.login_methods.password.reset_sms_webhook || '',
									sms_content: authData.login_methods.password.reset_sms_content || '',
									sms_config_key: authData.login_methods.password.reset_sms_config_key || '',
									sms_extra_data: authData.login_methods.password.reset_sms_extra_data || '',
								},
							},
							two_factor_auth: {
								required: authData.two_factor_auth.required,
								allowed_methods: authData.two_factor_auth.allowedMethods || [],
								enforced_from: null,
								grace_period_days: null,
								skip_for_sso: false,
								email_hook: authData.two_factor_auth.email_hook || '',
								sms_hook: authData.two_factor_auth.sms_hook || '',
							},
						};

						// Save the configuration
						const tempValues = {
							auth_config: JSON.stringify(authConfig)
						};
						const dynamicFormData = transformToFormData(tempValues);

						try {
							const { response, success } = await triggerApi({
								url: `/api/v1/apps/${appId}/`,
								type: 'PUT',
								loader: true,
								payload: dynamicFormData,
							});

							if (success && response) {
								dispatch(toggleRerenderPage());
								setShowAuthSetupModal(false);
							}
						} catch (error) {
							console.error('Error saving authentication configuration:', error);
						}
					}}
				/>
			</>
		);
	}

	// Navigation sections
	const sections = [
		{ id: 'overview', label: 'Overview', icon: '🏠' },
		{ id: 'login', label: 'Login Methods', icon: '🔐' },
		{ id: 'security', label: 'Security', icon: '🛡️' },
		{ id: 'policies', label: 'Policies', icon: '📋' },
		{ id: 'saml', label: 'SAML Providers', icon: '🔗' },
		{ id: 'role-overrides', label: 'Role Overrides', icon: '👥' }
	];

	// Validation schema for edit mode
	const validationSchema = Yup.object({
		login_methods: Yup.object({
			password: Yup.object({
				enabled: Yup.boolean(),
				forgot_password_enabled: Yup.boolean(),
				password_reset_link_expiry_hours: Yup.number()
					.min(1, "Must be at least 1 hour")
					.max(168, "Must be less than 168 hours (7 days)"),
				allowed_usernames: Yup.array().min(1, "At least one username type is required"),
			}),
			otp: Yup.object({
				enabled: Yup.boolean(),
				allowed_methods: Yup.array().when('enabled', {
					is: true,
					then: (schema) => schema.min(1, "At least one OTP method is required when OTP is enabled"),
					otherwise: (schema) => schema
				}),
				otp_expiry: Yup.number().min(30, "Expiry must be at least 30 seconds").max(3600, "Expiry cannot exceed 3600 seconds"),
			}),
			sso: Yup.object({
				enabled: Yup.boolean(),
			}),
			oidc: Yup.object({
				enabled: Yup.boolean(),
			}),
		}),
		session_policy: Yup.object({
			max_concurrent_sessions: Yup.number().min(0, "Cannot be negative"),
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
			allowed_methods: Yup.array().min(1, "At least one method is required"),
		}),
	});

	// Handle form submission
	const handleSubmit = async (values) => {
		setIsSaving(true);
		
		const cleanedAuthConfig = values;
		const tempValues = {
			auth_config: JSON.stringify(cleanedAuthConfig)
		};

		const dynamicFormData = transformToFormData(tempValues);

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

	// Calculate active login methods
	const activeLoginMethods = [];
	if (authConfig.login_methods?.password?.enabled) activeLoginMethods.push('Password');
	if (authConfig.login_methods?.otp?.enabled) activeLoginMethods.push('OTP');
	if (authConfig.login_methods?.sso?.enabled) activeLoginMethods.push('SSO');
	if (authConfig.login_methods?.oidc?.enabled) activeLoginMethods.push('OIDC');

	const QuickStat = ({ label, value, color = 'blue' }) => {
		const colors = {
			blue: 'bg-[#EFF6FF] text-[#1E40AF]',
			green: 'bg-[#D1FAE5] text-[#065F46]',
			purple: 'bg-[#EDE9FE] text-[#6B21A8]',
			amber: 'bg-[#FEF3C7] text-[#92400E]'
		};

		return (
			<div className="bg-white rounded-[12px] border border-[#E5E7EB] p-[24px]">
				<p className="text-[12px] font-medium text-[#6B7280] mb-[8px]">{label}</p>
				<div className={`inline-flex items-center gap-[8px] px-[12px] py-[6px] rounded-[8px] ${colors[color]}`}>
					<span className="text-[16px] font-semibold">{value}</span>
				</div>
			</div>
		);
	};

	const ConfigToggle = ({ label, enabled, description }) => (
		<div className="flex items-center justify-between py-[16px]">
			<div>
				<p className="text-[14px] font-medium text-[#111827]">{label}</p>
				{description && <p className="text-[12px] text-[#6B7280] mt-[2px]">{description}</p>}
			</div>
			<div className={`relative inline-flex h-[24px] w-[44px] items-center rounded-full transition-colors ${
				enabled ? 'bg-[#10B981]' : 'bg-[#E5E7EB]'
			}`}>
				<span className={`inline-block h-[18px] w-[18px] transform rounded-full bg-white shadow-sm transition-transform ${
					enabled ? 'translate-x-[22px]' : 'translate-x-[3px]'
				}`} />
			</div>
		</div>
	);

	const PolicyItem = ({ label, value, type = 'text' }) => (
		<div className="flex items-center justify-between py-[12px] border-b border-[#F3F4F6] last:border-b-0">
			<span className="text-[13px] text-[#6B7280]">{label}</span>
			{type === 'boolean' ? (
				<span className={`text-[13px] font-medium ${value ? 'text-[#10B981]' : 'text-[#6B7280]'}`}>
					{value ? 'Required' : 'Optional'}
				</span>
			) : (
				<span className="text-[13px] font-medium text-[#111827]">{value}</span>
			)}
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

	const MultiSelectChips = ({ label, name, options, value, onChange, description }) => (
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
					return (
						<button
							key={option.id}
							type="button"
							onClick={() => {
								const currentValue = Array.isArray(value) ? value : [];
								const newValue = isSelected
									? currentValue.filter(v => v !== option.id)
									: [...currentValue, option.id];
								onChange(newValue);
							}}
							className={`relative px-[20px] py-[12px] rounded-[10px] border-2 font-lato text-[14px] font-medium transition-all duration-200 flex items-center gap-[8px] transform hover:scale-[1.02] ${
								isSelected
									? 'border-[#5048ED] bg-[#5048ED] text-white shadow-lg'
									: 'border-[#E5E7EB] bg-white text-[#6B7280] hover:border-[#5048ED] hover:bg-[#F8FAFC] hover:shadow-md'
							}`}
						>
							{isSelected && (
								<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
									<path d="M13.5 4.5L6 12L2.5 8.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
								</svg>
							)}
							{option.label}
						</button>
					);
				})}
			</div>
		</div>
	);

	const usernameOptions = [
		{ id: "email", label: "Email" },
		{ id: "phone", label: "Phone Number" },
		{ id: "username", label: "Username" },
	];

	return (
		<div className="max-w-[1200px] mx-auto">
			{/* Header */}
			<div className="flex items-center justify-between mb-[32px]">
				<div>
					<h2 className="text-[24px] font-semibold text-[#111827] mb-[4px]">Authentication Settings</h2>
					<p className="text-[14px] text-[#6B7280]">Configure how users sign in and access your application</p>
				</div>
				{!isEditMode && roles.length > 0 && isAuthConfigured() && (
					<button
						onClick={() => setShowAuthSetupModal(true)}
						className="flex items-center gap-[8px] px-[16px] py-[8px] bg-[#5048ED] text-white rounded-[8px] hover:bg-[#4338CA] transition-colors"
					>
						<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
							<path d="M11.334 2.00004C11.5091 1.82494 11.7169 1.68605 11.9457 1.59129C12.1745 1.49653 12.4197 1.44775 12.6673 1.44775C12.915 1.44775 13.1602 1.49653 13.389 1.59129C13.6178 1.68605 13.8256 1.82494 14.0007 2.00004C14.1757 2.17513 14.3146 2.38297 14.4094 2.61178C14.5042 2.84059 14.5529 3.08577 14.5529 3.33337C14.5529 3.58097 14.5042 3.82615 14.4094 4.05496C14.3146 4.28377 14.1757 4.49161 14.0007 4.66671L5.00065 13.6667L1.33398 14.6667L2.33398 11L11.334 2.00004Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
						</svg>
						<span className="font-medium text-[14px]">Edit Configuration</span>
					</button>
				)}
			</div>

			{/* No Roles Warning */}
			{!loadingRoles && roles.length === 0 && (
				<div className="mb-[24px] bg-[#FEF3C7] border border-[#F59E0B] rounded-[12px] p-[20px]">
					<div className="flex items-start gap-[16px]">
						<div className="flex-shrink-0">
							<svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-[#F59E0B]">
								<path d="M12 9V13M12 17H12.01M5.07183 19H18.9282C20.4678 19 21.4301 17.3333 20.6603 16L13.7321 4C12.9623 2.66667 11.0377 2.66667 10.2679 4L3.33975 16C2.56992 17.3333 3.53222 19 5.07183 19Z" 
									stroke="currentColor" 
									strokeWidth="2" 
									strokeLinecap="round" 
									strokeLinejoin="round"
								/>
							</svg>
						</div>
						<div className="flex-1">
							<h4 className="text-[16px] font-semibold text-[#92400E] mb-[4px]">User Roles Required</h4>
							<p className="text-[14px] text-[#92400E] mb-[12px]">
								User Roles should be created before setting up authentication. Please create at least one user role to configure authentication settings.
							</p>
							<button
								onClick={() => navigate(`#roles`)}
								className="inline-flex items-center gap-[8px] px-[16px] py-[8px] bg-[#F59E0B] text-white rounded-[8px] hover:bg-[#D97706] transition-colors text-[14px] font-medium"
							>
								<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
									<path d="M8 1V15M1 8H15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
								</svg>
								Create User Roles
							</button>
						</div>
					</div>
				</div>
			)}

			{/* Navigation Pills - Only show when auth is configured and user-defined roles exist */}
			{roles.length > 0 && isAuthConfigured() && (
				<div className="flex gap-[8px] mb-[32px] p-[4px] bg-[#F3F4F6] rounded-[10px] inline-flex">
				{sections.map(section => (
					<button
						key={section.id}
						onClick={() => setActiveSection(section.id)}
						className={`flex items-center gap-[8px] px-[16px] py-[8px] rounded-[8px] text-[14px] font-medium transition-all ${
							activeSection === section.id
								? 'bg-white text-[#111827] shadow-sm'
								: 'text-[#6B7280] hover:text-[#111827]'
						}`}
					>
						<span className="text-[16px]">{section.icon}</span>
						{section.label}
					</button>
				))}
				</div>
			)}

			{/* Content - Only show when auth is configured and user-defined roles exist */}
			{roles.length > 0 && isAuthConfigured() && isEditMode ? (
				<Formik
					initialValues={authConfig}
					validationSchema={validationSchema}
					onSubmit={handleSubmit}
					enableReinitialize={true}
				>
					{(formik) => {
						const { values, setFieldValue, handleSubmit, errors, touched } = formik;
						
						return (
							<form onSubmit={handleSubmit}>
								{activeSection === 'login' && (
									<div className="space-y-[24px]">
										{/* Login Methods Configuration */}
										<div className="bg-white rounded-[16px] border border-[#E5E7EB] p-[24px]">
											<h3 className="text-[16px] font-semibold text-[#111827] mb-[20px]">Login Methods Configuration</h3>
											
											{/* Password Authentication */}
											<div className="mb-[24px] pb-[24px] border-b border-[#F3F4F6]">
												<div className="flex items-center justify-between mb-[16px]">
													<div>
														<h4 className="text-[14px] font-medium text-[#111827]">Password Authentication</h4>
														<p className="text-[12px] text-[#6B7280] mt-[2px]">Traditional username and password login</p>
													</div>
													<ToggleSwitch
														checked={values?.login_methods?.password?.enabled}
														onChange={(checked) => setFieldValue("login_methods.password.enabled", checked)}
													/>
												</div>
												
												{values?.login_methods?.password?.enabled && (
													<div className="ml-[24px] space-y-[16px]">
														<MultiSelectChips
															label="Allowed Username Types"
															description="Select what users can use to log in"
															options={usernameOptions}
															value={values?.login_methods?.password?.allowed_usernames || []}
															onChange={(value) => setFieldValue("login_methods.password.allowed_usernames", value)}
														/>
														
														<div className="flex items-center justify-between">
															<div>
																<p className="text-[13px] font-medium text-[#111827]">Enable Forgot Password</p>
																<p className="text-[11px] text-[#6B7280]">Allow users to reset their passwords</p>
															</div>
															<ToggleSwitch
																checked={values?.login_methods?.password?.forgot_password_enabled}
																onChange={(checked) => setFieldValue("login_methods.password.forgot_password_enabled", checked)}
															/>
														</div>
														
														{values?.login_methods?.password?.forgot_password_enabled && (
															<div className="max-w-[300px]">
																<InputField
																	name="login_methods.password.password_reset_link_expiry_hours"
																	label="Reset Link Expiry (Hours)"
																	type="number"
																	value={values?.login_methods?.password?.password_reset_link_expiry_hours}
																	onChange={(e) => setFieldValue("login_methods.password.password_reset_link_expiry_hours", parseInt(e.target.value))}
																/>
															</div>
														)}
													</div>
												)}
											</div>

											{/* OTP Authentication */}
											<div className="mb-[24px] pb-[24px] border-b border-[#F3F4F6]">
												<div className="flex items-center justify-between mb-[16px]">
													<div>
														<h4 className="text-[14px] font-medium text-[#111827]">One-Time Password (OTP)</h4>
														<p className="text-[12px] text-[#6B7280] mt-[2px]">SMS or email based verification codes</p>
													</div>
													<ToggleSwitch
														checked={values?.login_methods?.otp?.enabled}
														onChange={(checked) => setFieldValue("login_methods.otp.enabled", checked)}
													/>
												</div>

												{values?.login_methods?.otp?.enabled && (
													<div className="ml-[24px] space-y-[16px]">
														<MultiSelectChips
															label="Allowed OTP Methods"
															description="Select delivery methods for one-time passwords"
															options={[
																{ id: "email", label: "Email" },
																{ id: "sms", label: "SMS" }
															]}
															value={values?.login_methods?.otp?.allowed_methods || []}
															onChange={(value) => setFieldValue("login_methods.otp.allowed_methods", value)}
														/>
														<InputField
															name="login_methods.otp.otp_expiry"
															label="OTP Expiry (seconds)"
															description="Time in seconds before OTP expires (30-3600 seconds)"
															type="number"
															value={values?.login_methods?.otp?.otp_expiry}
															onChange={(e) => setFieldValue("login_methods.otp.otp_expiry", parseInt(e.target.value) || 300)}
														/>
													</div>
												)}
											</div>

											{/* Other Login Methods */}
											<div className="space-y-[16px]">
												<div>
													<div className="flex items-center justify-between mb-[16px]">
														<div>
															<h4 className="text-[14px] font-medium text-[#111827]">Single Sign-On (SSO)</h4>
															<p className="text-[12px] text-[#6B7280] mt-[2px]">Enterprise SSO integration</p>
														</div>
														<ToggleSwitch
															checked={values?.login_methods?.sso?.enabled}
															onChange={(checked) => setFieldValue("login_methods.sso.enabled", checked)}
														/>
													</div>

													{values?.login_methods?.sso?.enabled && (
														<div className="ml-[24px] p-[12px] bg-[#F0F9FF] border border-[#E0F2FE] rounded-[8px]">
															<p className="text-[12px] text-[#0369A1] mb-[8px]">
																SAML providers can be configured in the <strong>SAML Providers</strong> section. Click on <strong>Configure SAML Provider</strong> to add or manage providers.
															</p>
															<button
																type="button"
																onClick={() => setActiveSection('saml')}
																className="inline-flex items-center gap-[6px] px-[12px] py-[6px] bg-[#0EA5E9] text-white rounded-[6px] hover:bg-[#0284C7] transition-colors text-[12px] font-medium"
															>
																<svg width="14" height="14" viewBox="0 0 16 16" fill="none">
																	<path d="M8 1V15M1 8H15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
																</svg>
																Go to SAML Configuration
															</button>
														</div>
													)}
												</div>

												<div className="flex items-center justify-between">
													<div>
														<h4 className="text-[14px] font-medium text-[#111827]">OpenID Connect (OIDC)</h4>
														<p className="text-[12px] text-[#6B7280] mt-[2px]">OAuth 2.0 based authentication</p>
													</div>
													<ToggleSwitch
														checked={values?.login_methods?.oidc?.enabled}
														onChange={(checked) => setFieldValue("login_methods.oidc.enabled", checked)}
													/>
												</div>
											</div>
										</div>

										{/* Action Buttons */}
										<div className="flex justify-end gap-[12px]">
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
									</div>
								)}

								{activeSection === 'security' && (
									<div className="grid grid-cols-1 lg:grid-cols-2 gap-[24px]">
										{/* Two-Factor Authentication */}
										<div className="bg-white rounded-[16px] border border-[#E5E7EB] p-[24px]">
											<h3 className="text-[16px] font-semibold text-[#111827] mb-[20px]">Two-Factor Authentication</h3>
											<div className="flex items-center justify-between mb-[16px]">
												<div>
													<p className="text-[14px] font-medium text-[#111827]">Require 2FA for all users</p>
													<p className="text-[12px] text-[#6B7280] mt-[2px]">Additional security layer for user accounts</p>
												</div>
												<ToggleSwitch
													checked={values?.two_factor_auth?.required}
													onChange={(checked) => setFieldValue("two_factor_auth.required", checked)}
												/>
											</div>
											
											{values?.two_factor_auth?.required && (
												<div className="mt-[16px]">
													<MultiSelectChips
														label="Available 2FA Methods"
														options={[
															{ id: "email", label: "Email" },
															{ id: "sms", label: "SMS" },
															{ id: "totp", label: "Authenticator App (TOTP)" },
														]}
														value={values?.two_factor_auth?.allowed_methods || []}
														onChange={(value) => setFieldValue("two_factor_auth.allowed_methods", value)}
													/>
												</div>
											)}
										</div>

										{/* Session Management */}
										<div className="bg-white rounded-[16px] border border-[#E5E7EB] p-[24px]">
											<h3 className="text-[16px] font-semibold text-[#111827] mb-[20px]">Session Management</h3>
											<div className="space-y-[16px]">
												<div>
													<InputField
														name="session_policy.max_concurrent_sessions"
														label="Maximum concurrent sessions (0 = unlimited)"
														type="number"
														value={values?.session_policy?.max_concurrent_sessions}
														onChange={(e) => setFieldValue("session_policy.max_concurrent_sessions", parseInt(e.target.value) || 0)}
													/>
												</div>
												<div className="flex items-center justify-between">
													<div>
														<p className="text-[14px] font-medium text-[#111827]">Force logout on password change</p>
														<p className="text-[12px] text-[#6B7280] mt-[2px]">Terminate all sessions when password is changed</p>
													</div>
													<ToggleSwitch
														checked={values?.session_policy?.force_logout_on_password_change}
														onChange={(checked) => setFieldValue("session_policy.force_logout_on_password_change", checked)}
													/>
												</div>
											</div>
										</div>

										{/* Action Buttons */}
										<div className="col-span-full flex justify-end gap-[12px]">
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
									</div>
								)}

								{activeSection === 'policies' && (
									<div className="bg-white rounded-[16px] border border-[#E5E7EB] p-[24px]">
										<h3 className="text-[16px] font-semibold text-[#111827] mb-[24px]">Password Policy</h3>
										<div className="grid grid-cols-1 md:grid-cols-2 gap-[24px]">
											<div>
												<h4 className="text-[14px] font-medium text-[#111827] mb-[16px]">Requirements</h4>
												<div className="space-y-[16px]">
													<InputField
														name="password_policy.min_length"
														label="Minimum length"
														type="number"
														value={values?.password_policy?.min_length}
														onChange={(e) => setFieldValue("password_policy.min_length", parseInt(e.target.value))}
													/>
													<div className="space-y-[12px]">
														{[
															{ field: "require_numbers", label: "Require numbers" },
															{ field: "require_lowercase", label: "Require lowercase letters" },
															{ field: "require_uppercase", label: "Require uppercase letters" },
															{ field: "require_special_chars", label: "Require special characters" }
														].map(({ field, label }) => (
															<div key={field} className="flex items-center justify-between">
																<span className="text-[13px] text-[#111827]">{label}</span>
																<ToggleSwitch
																	checked={values?.password_policy?.[field]}
																	onChange={(checked) => setFieldValue(`password_policy.${field}`, checked)}
																/>
															</div>
														))}
													</div>
												</div>
											</div>
											<div>
												<h4 className="text-[14px] font-medium text-[#111827] mb-[16px]">Management</h4>
												<div className="space-y-[16px]">
													<InputField
														name="password_policy.password_expiry_days"
														label="Password expiry (days)"
														type="number"
														value={values?.password_policy?.password_expiry_days}
														onChange={(e) => setFieldValue("password_policy.password_expiry_days", parseInt(e.target.value))}
													/>
													<InputField
														name="password_policy.password_history_count"
														label="Password history count"
														type="number"
														value={values?.password_policy?.password_history_count}
														onChange={(e) => setFieldValue("password_policy.password_history_count", parseInt(e.target.value))}
													/>
													<div className="flex items-center justify-between">
														<span className="text-[13px] text-[#111827]">Allow password change</span>
														<ToggleSwitch
															checked={values?.password_policy?.allow_change}
															onChange={(checked) => setFieldValue("password_policy.allow_change", checked)}
														/>
													</div>
												</div>
											</div>
										</div>

										{/* Action Buttons */}
										<div className="mt-[24px] flex justify-end gap-[12px]">
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
									</div>
								)}

								{activeSection === 'overview' && (
									<div className="bg-white rounded-[16px] border border-[#E5E7EB] p-[32px] text-center">
										<p className="text-[16px] text-[#6B7280]">Please select a specific section to edit configuration</p>
									</div>
								)}
							</form>
						);
					}}
				</Formik>
			) : roles.length > 0 && isAuthConfigured() ? (
				// View Mode (existing implementation)
				<>
					{activeSection === 'overview' && (
						<div className="space-y-[24px]">
							{/* Quick Stats */}
							<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-[16px]">
								<QuickStat
									label="Active Login Methods"
									value={activeLoginMethods.length}
									color="blue"
								/>
								<QuickStat
									label="Two-Factor Auth"
									value={authConfig.two_factor_auth?.required ? 'Required' : 'Optional'}
									color="green"
								/>
								<QuickStat
									label="Max Sessions"
									value={authConfig.session_policy?.max_concurrent_sessions || 'Unlimited'}
									color="purple"
								/>
								<QuickStat
									label="Password Expiry"
									value={`${authConfig.password_policy?.password_expiry_days || 90} days`}
									color="amber"
								/>
							</div>

							{/* Authentication Overview */}
							<div className="grid grid-cols-1 lg:grid-cols-2 gap-[24px]">
								{/* Login Methods Overview */}
								<div className="bg-white rounded-[16px] border border-[#E5E7EB] p-[24px]">
									<div className="flex items-center gap-[12px] mb-[20px]">
										<div className="w-[40px] h-[40px] bg-gradient-to-br from-[#5048ED] to-[#346BD4] rounded-[12px] flex items-center justify-center">
											<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
												<path d="M10 11.667C11.8409 11.667 13.3333 10.1743 13.3333 8.33333C13.3333 6.49238 11.8409 5 10 5C8.15905 5 6.66667 6.49238 6.66667 8.33333C6.66667 10.1743 8.15905 11.667 10 11.667Z" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
												<path d="M10 15C13.3333 15 16.6667 13.3333 16.6667 11.6667C16.6667 10 10 10 10 10C10 10 3.33333 10 3.33333 11.6667C3.33333 13.3333 6.66667 15 10 15Z" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
											</svg>
										</div>
										<div>
											<h3 className="text-[16px] font-semibold text-[#111827]">Login Methods</h3>
											<p className="text-[12px] text-[#6B7280]">{activeLoginMethods.length} method{activeLoginMethods.length !== 1 ? 's' : ''} enabled</p>
										</div>
									</div>
									<div className="space-y-[12px]">
										{authConfig.login_methods?.password?.enabled && (
											<div className="flex items-start gap-[12px] p-[12px] bg-[#F9FAFB] rounded-[8px]">
												<div className="flex-shrink-0 w-[32px] h-[32px] bg-[#EFF6FF] rounded-[8px] flex items-center justify-center">
													<span className="text-[18px]">🔑</span>
												</div>
												<div className="flex-1">
													<p className="text-[14px] font-medium text-[#111827]">Password Authentication</p>
													<p className="text-[12px] text-[#6B7280] mt-[2px]">
														{authConfig.login_methods?.password?.allowed_usernames?.map(type => type.charAt(0).toUpperCase() + type.slice(1)).join(', ')}
														{authConfig.login_methods?.password?.forgot_password_enabled && ' • Forgot password enabled'}
													</p>
												</div>
											</div>
										)}
										{authConfig.login_methods?.otp?.enabled && (
											<div className="flex items-start gap-[12px] p-[12px] bg-[#F9FAFB] rounded-[8px]">
												<div className="flex-shrink-0 w-[32px] h-[32px] bg-[#EFF6FF] rounded-[8px] flex items-center justify-center">
													<span className="text-[18px]">📱</span>
												</div>
												<div className="flex-1">
													<p className="text-[14px] font-medium text-[#111827]">One-Time Password (OTP)</p>
													<p className="text-[12px] text-[#6B7280] mt-[2px]">
														{authConfig.login_methods?.otp?.allowed_methods?.length > 0
															? authConfig.login_methods.otp.allowed_methods.map(m => m.charAt(0).toUpperCase() + m.slice(1)).join(', ')
															: 'SMS or email verification codes'}
													</p>
												</div>
											</div>
										)}
										{authConfig.login_methods?.sso?.enabled && (
											<div className="flex items-start gap-[12px] p-[12px] bg-[#F9FAFB] rounded-[8px]">
												<div className="flex-shrink-0 w-[32px] h-[32px] bg-[#EFF6FF] rounded-[8px] flex items-center justify-center">
													<span className="text-[18px]">🔗</span>
												</div>
												<div className="flex-1">
													<p className="text-[14px] font-medium text-[#111827]">Single Sign-On (SSO)</p>
													<p className="text-[12px] text-[#6B7280] mt-[2px]">Enterprise SSO integration</p>
												</div>
											</div>
										)}
										{authConfig.login_methods?.oidc?.enabled && (
											<div className="flex items-start gap-[12px] p-[12px] bg-[#F9FAFB] rounded-[8px]">
												<div className="flex-shrink-0 w-[32px] h-[32px] bg-[#EFF6FF] rounded-[8px] flex items-center justify-center">
													<span className="text-[18px]">🌐</span>
												</div>
												<div className="flex-1">
													<p className="text-[14px] font-medium text-[#111827]">OpenID Connect (OIDC)</p>
													<p className="text-[12px] text-[#6B7280] mt-[2px]">OAuth 2.0 based authentication</p>
												</div>
											</div>
										)}
									</div>
								</div>

								{/* Security Overview */}
								<div className="bg-white rounded-[16px] border border-[#E5E7EB] p-[24px]">
									<div className="flex items-center gap-[12px] mb-[20px]">
										<div className="w-[40px] h-[40px] bg-gradient-to-br from-[#10B981] to-[#059669] rounded-[12px] flex items-center justify-center">
											<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
												<path d="M10 1.667L3.33333 4.16699V9.16699C3.33333 13.5003 6.21667 17.5337 10 18.3337C13.7833 17.5337 16.6667 13.5003 16.6667 9.16699V4.16699L10 1.667Z" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
												<path d="M10 10.833V10.8413" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
											</svg>
										</div>
										<div>
											<h3 className="text-[16px] font-semibold text-[#111827]">Security Settings</h3>
											<p className="text-[12px] text-[#6B7280]">Protection & policies</p>
										</div>
									</div>
									<div className="space-y-[16px]">
										{/* Two-Factor Auth */}
										<div className="p-[12px] bg-[#F9FAFB] rounded-[8px]">
											<div className="flex items-center justify-between mb-[4px]">
												<p className="text-[13px] font-medium text-[#111827]">Two-Factor Authentication</p>
												<span className={`px-[8px] py-[2px] rounded-[6px] text-[11px] font-medium ${
													authConfig.two_factor_auth?.required
														? 'bg-[#D1FAE5] text-[#065F46]'
														: 'bg-[#FEF3C7] text-[#92400E]'
												}`}>
													{authConfig.two_factor_auth?.required ? 'Required' : 'Optional'}
												</span>
											</div>
											{authConfig.two_factor_auth?.allowed_methods?.length > 0 && (
												<p className="text-[12px] text-[#6B7280]">
													Methods: {authConfig.two_factor_auth.allowed_methods.map(m => m.charAt(0).toUpperCase() + m.slice(1)).join(', ')}
												</p>
											)}
										</div>

										{/* Session Policy */}
										<div className="p-[12px] bg-[#F9FAFB] rounded-[8px]">
											<div className="flex items-center justify-between mb-[4px]">
												<p className="text-[13px] font-medium text-[#111827]">Concurrent Sessions</p>
												<span className="px-[8px] py-[2px] bg-[#EDE9FE] text-[#6B21A8] rounded-[6px] text-[11px] font-medium">
													{authConfig.session_policy?.max_concurrent_sessions || 'Unlimited'}
												</span>
											</div>
											<p className="text-[12px] text-[#6B7280]">
												{authConfig.session_policy?.force_logout_on_password_change
													? 'Force logout on password change'
													: 'Sessions maintained on password change'}
											</p>
										</div>

										{/* Password Policy Summary */}
										<div className="p-[12px] bg-[#F9FAFB] rounded-[8px]">
											<p className="text-[13px] font-medium text-[#111827] mb-[4px]">Password Policy</p>
											<div className="flex flex-wrap gap-[6px]">
												<span className="px-[6px] py-[2px] bg-white border border-[#E5E7EB] rounded-[4px] text-[11px] text-[#6B7280]">
													Min {authConfig.password_policy?.min_length || 8} chars
												</span>
												{authConfig.password_policy?.require_uppercase && (
													<span className="px-[6px] py-[2px] bg-white border border-[#E5E7EB] rounded-[4px] text-[11px] text-[#6B7280]">
														Uppercase
													</span>
												)}
												{authConfig.password_policy?.require_lowercase && (
													<span className="px-[6px] py-[2px] bg-white border border-[#E5E7EB] rounded-[4px] text-[11px] text-[#6B7280]">
														Lowercase
													</span>
												)}
												{authConfig.password_policy?.require_numbers && (
													<span className="px-[6px] py-[2px] bg-white border border-[#E5E7EB] rounded-[4px] text-[11px] text-[#6B7280]">
														Numbers
													</span>
												)}
												{authConfig.password_policy?.require_special_chars && (
													<span className="px-[6px] py-[2px] bg-white border border-[#E5E7EB] rounded-[4px] text-[11px] text-[#6B7280]">
														Special chars
													</span>
												)}
											</div>
										</div>
									</div>
								</div>
							</div>

							{/* Role Overrides Summary */}
							{roles.some(role => role.auth_config?.override_applied === true) && (
								<div className="bg-gradient-to-br from-[#F8FAFC] to-[#EFF6FF] rounded-[16px] border border-[#E5E7EB] p-[24px]">
									<div className="flex items-center gap-[12px] mb-[16px]">
										<div className="w-[40px] h-[40px] bg-gradient-to-br from-[#F59E0B] to-[#D97706] rounded-[12px] flex items-center justify-center">
											<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
												<path d="M10 5V10L13.3333 11.6667M17.5 10C17.5 14.1421 14.1421 17.5 10 17.5C5.85786 17.5 2.5 14.1421 2.5 10C2.5 5.85786 5.85786 2.5 10 2.5C14.1421 2.5 17.5 5.85786 17.5 10Z" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
											</svg>
										</div>
										<div>
											<h3 className="text-[16px] font-semibold text-[#111827]">Role-Specific Policies</h3>
											<p className="text-[12px] text-[#6B7280]">Custom authentication rules for specific roles</p>
										</div>
									</div>
									<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-[12px]">
										{roles.filter(role => role.auth_config?.override_applied === true).map(role => (
											<div key={role.id} className="bg-white rounded-[10px] border border-[#E5E7EB] p-[12px]">
												<div className="flex items-center gap-[8px] mb-[8px]">
													<div className="w-[24px] h-[24px] bg-[#5048ED] rounded-[6px] flex items-center justify-center">
														<svg width="12" height="12" viewBox="0 0 12 12" fill="none">
															<path d="M6 6C7.24264 6 8.25 4.99264 8.25 3.75C8.25 2.50736 7.24264 1.5 6 1.5C4.75736 1.5 3.75 2.50736 3.75 3.75C3.75 4.99264 4.75736 6 6 6Z" stroke="white" strokeLinecap="round" strokeLinejoin="round"/>
															<path d="M1.5 10.5C1.5 8.84315 2.84315 7.5 4.5 7.5H7.5C9.15685 7.5 10.5 8.84315 10.5 10.5" stroke="white" strokeLinecap="round" strokeLinejoin="round"/>
														</svg>
													</div>
													<p className="text-[13px] font-semibold text-[#111827]">{role.name}</p>
												</div>
												<div className="flex flex-wrap gap-[4px]">
													{role.auth_config.password_policy && (
														<span className="px-[6px] py-[2px] bg-[#EFF6FF] text-[#5048ED] rounded-[4px] text-[10px] font-medium">
															Password
														</span>
													)}
													{role.auth_config.two_factor_auth?.required && (
														<span className="px-[6px] py-[2px] bg-[#D1FAE5] text-[#065F46] rounded-[4px] text-[10px] font-medium">
															2FA Required
														</span>
													)}
													{role.auth_config.session_policy && (
														<span className="px-[6px] py-[2px] bg-[#FEF3C7] text-[#92400E] rounded-[4px] text-[10px] font-medium">
															Session
														</span>
													)}
												</div>
											</div>
										))}
									</div>
								</div>
							)}
						</div>
					)}

					{activeSection === 'login' && (
						<div className="grid grid-cols-1 lg:grid-cols-2 gap-[24px]">
							{/* Login Methods */}
							<div className="bg-white rounded-[16px] border border-[#E5E7EB] p-[24px]">
								<h3 className="text-[16px] font-semibold text-[#111827] mb-[20px]">Login Methods</h3>
								<div className="space-y-[4px]">
									<ConfigToggle 
										label="Password Authentication" 
										enabled={authConfig.login_methods?.password?.enabled}
										description="Traditional username and password login"
									/>
									<ConfigToggle 
										label="One-Time Password (OTP)" 
										enabled={authConfig.login_methods?.otp?.enabled}
										description="SMS or email based verification codes"
									/>
									<div>
										<ConfigToggle
											label="Single Sign-On (SSO)"
											enabled={authConfig.login_methods?.sso?.enabled}
											description="Enterprise SSO integration"
										/>
										{authConfig.login_methods?.sso?.enabled && (
											<div className="mt-[12px] ml-[12px] p-[12px] bg-[#F0F9FF] border border-[#E0F2FE] rounded-[8px]">
												<p className="text-[12px] text-[#0369A1]">
													✓ SAML providers configured. Visit the <strong>SAML Providers</strong> section to manage them.
												</p>
											</div>
										)}
									</div>
									<ConfigToggle
										label="OpenID Connect (OIDC)"
										enabled={authConfig.login_methods?.oidc?.enabled}
										description="OAuth 2.0 based authentication"
									/>
								</div>
							</div>

							{/* Username Configuration */}
							<div className="bg-white rounded-[16px] border border-[#E5E7EB] p-[24px]">
								<h3 className="text-[16px] font-semibold text-[#111827] mb-[20px]">Username Configuration</h3>
								<div className="space-y-[12px]">
									<p className="text-[13px] text-[#6B7280]">Allowed username types:</p>
									<div className="flex flex-wrap gap-[8px]">
										{authConfig.login_methods?.password?.allowed_usernames?.map(type => (
											<span key={type} className="px-[12px] py-[6px] bg-[#EFF6FF] text-[#1E40AF] rounded-[8px] text-[13px] font-medium">
												{type.charAt(0).toUpperCase() + type.slice(1)}
											</span>
										))}
									</div>
									{authConfig.login_methods?.password?.enabled && (
										<div className="mt-[20px] pt-[20px] border-t border-[#F3F4F6]">
											<ConfigToggle 
												label="Forgot Password" 
												enabled={authConfig.login_methods?.password?.forgot_password_enabled}
												description={`Reset links expire after ${authConfig.login_methods?.password?.password_reset_link_expiry_hours || 24} hours`}
											/>
										</div>
									)}
								</div>
							</div>
						</div>
					)}

					{activeSection === 'security' && (
						<div className="grid grid-cols-1 lg:grid-cols-2 gap-[24px]">
							{/* Two-Factor Authentication */}
							<div className="bg-white rounded-[16px] border border-[#E5E7EB] p-[24px]">
								<h3 className="text-[16px] font-semibold text-[#111827] mb-[20px]">Two-Factor Authentication</h3>
								<ConfigToggle 
									label="Require 2FA for all users" 
									enabled={authConfig.two_factor_auth?.required}
									description="Additional security layer for user accounts"
								/>
								{authConfig.two_factor_auth?.allowed_methods?.length > 0 && (
									<div className="mt-[20px] pt-[20px] border-t border-[#F3F4F6]">
										<p className="text-[13px] text-[#6B7280] mb-[12px]">Available 2FA methods:</p>
										<div className="flex flex-wrap gap-[8px]">
											{authConfig.two_factor_auth.allowed_methods.map(method => (
												<span key={method} className="px-[12px] py-[6px] bg-[#D1FAE5] text-[#065F46] rounded-[8px] text-[13px] font-medium">
													{method}
												</span>
											))}
										</div>
									</div>
								)}
							</div>

							{/* Session Management */}
							<div className="bg-white rounded-[16px] border border-[#E5E7EB] p-[24px]">
								<h3 className="text-[16px] font-semibold text-[#111827] mb-[20px]">Session Management</h3>
								<div className="space-y-[16px]">
									<div>
										<p className="text-[13px] text-[#6B7280] mb-[4px]">Maximum concurrent sessions</p>
										<div className="flex items-center gap-[8px]">
											<span className="text-[24px] font-semibold text-[#111827]">
												{authConfig.session_policy?.max_concurrent_sessions || '∞'}
											</span>
											<span className="text-[13px] text-[#6B7280]">
												{authConfig.session_policy?.max_concurrent_sessions ? 'per user' : 'Unlimited'}
											</span>
										</div>
									</div>
									<ConfigToggle 
										label="Force logout on password change" 
										enabled={authConfig.session_policy?.force_logout_on_password_change}
										description="Terminate all sessions when password is changed"
									/>
								</div>
							</div>
						</div>
					)}

					{activeSection === 'policies' && (
						<div className="bg-white rounded-[16px] border border-[#E5E7EB] p-[24px]">
							<h3 className="text-[16px] font-semibold text-[#111827] mb-[24px]">Password Policy</h3>
							<div className="grid grid-cols-1 md:grid-cols-2 gap-[24px]">
								<div>
									<h4 className="text-[14px] font-medium text-[#111827] mb-[16px]">Requirements</h4>
									<div className="space-y-[0]">
										<PolicyItem 
											label="Minimum length" 
											value={`${authConfig.password_policy?.min_length || 8} characters`} 
										/>
										<PolicyItem 
											label="Numbers" 
											value={authConfig.password_policy?.require_numbers} 
											type="boolean"
										/>
										<PolicyItem 
											label="Lowercase letters" 
											value={authConfig.password_policy?.require_lowercase} 
											type="boolean"
										/>
										<PolicyItem 
											label="Uppercase letters" 
											value={authConfig.password_policy?.require_uppercase} 
											type="boolean"
										/>
										<PolicyItem 
											label="Special characters" 
											value={authConfig.password_policy?.require_special_chars} 
											type="boolean"
										/>
									</div>
								</div>
								<div>
									<h4 className="text-[14px] font-medium text-[#111827] mb-[16px]">Management</h4>
									<div className="space-y-[0]">
										<PolicyItem 
											label="Password expiry" 
											value={`${authConfig.password_policy?.password_expiry_days || 90} days`} 
										/>
										<PolicyItem 
											label="Password history" 
											value={`Last ${authConfig.password_policy?.password_history_count || 5} passwords`} 
										/>
										<PolicyItem 
											label="Allow password change" 
											value={authConfig.password_policy?.allow_change ? 'Yes' : 'No'} 
										/>
									</div>
								</div>
							</div>
						</div>
					)}

					{activeSection === 'role-overrides' && (
						<div className="space-y-[24px]">
							<div className="bg-white rounded-[16px] border border-[#E5E7EB] p-[24px]">
								<div className="mb-[24px]">
									<h3 className="text-[16px] font-semibold text-[#111827]">User Role Overrides</h3>
									<p className="text-[13px] text-[#6B7280] mt-[4px]">
										Define stricter authentication policies for specific user roles
									</p>
								</div>

								{/* Info Banner */}
								<div className="mb-[20px] p-[12px] bg-[#FEF3C7] rounded-[8px] flex gap-[8px]">
									<svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[#D97706] flex-shrink-0 mt-[2px]">
										<path d="M8 4V8M8 12H8.01M14 8C14 11.3137 11.3137 14 8 14C4.68629 14 2 11.3137 2 8C2 4.68629 4.68629 2 8 2C11.3137 2 14 4.68629 14 8Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
									</svg>
									<p className="text-[12px] text-[#92400E]">
										Role overrides can only enforce stricter policies than the global settings
									</p>
								</div>

								{roles && roles.length > 0 ? (
									<div className="space-y-[16px]">
										{roles.map((role) => {
											// Check for overrides in the role's own auth_config
											const roleAuthConfig = role.auth_config;
											// Use override_applied flag to determine if role has custom policies
											const hasOverride = roleAuthConfig?.override_applied === true;

											return (
												<div key={role.id} className={`border rounded-[12px] ${hasOverride ? 'border-[#5048ED]' : 'border-[#E5E7EB]'}`}>
													<div className={`p-[16px] ${hasOverride ? 'bg-[#F8FAFC]' : 'bg-white'}`}>
														<div className="flex items-center justify-between">
															<div className="flex items-center gap-[12px]">
																<div className={`w-[32px] h-[32px] rounded-[8px] flex items-center justify-center ${
																	hasOverride ? 'bg-[#5048ED] text-white' : 'bg-[#F3F4F6] text-[#6B7280]'
																}`}>
																	<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
																		<path d="M8 8C9.65685 8 11 6.65685 11 5C11 3.34315 9.65685 2 8 2C6.34315 2 5 3.34315 5 5C5 6.65685 6.34315 8 8 8Z" stroke="currentColor" strokeWidth="1.5"/>
																		<path d="M2 14C2 11.7909 3.79086 10 6 10H10C12.2091 10 14 11.7909 14 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
																	</svg>
																</div>
																<div>
																	<h4 className="text-[14px] font-medium text-[#111827]">{role.name}</h4>
																	<p className="text-[12px] text-[#6B7280]">
																		{hasOverride ? 'Custom policies applied' : 'Using default policies'}
																	</p>
																</div>
															</div>
															<div className="flex items-center gap-[8px]">
																{hasOverride && (
																	<div className="flex gap-[8px]">
																		{roleAuthConfig.password_policy && (
																			<span className="px-[8px] py-[2px] bg-[#EFF6FF] text-[#5048ED] rounded-[4px] text-[11px] font-medium">
																				Password Policy
																			</span>
																		)}
																		{roleAuthConfig.two_factor_auth?.required && (
																			<span className="px-[8px] py-[2px] bg-[#D1FAE5] text-[#065F46] rounded-[4px] text-[11px] font-medium">
																				2FA Required
																			</span>
																		)}
																	</div>
																)}
																<button
																	onClick={() => {
																		setSelectedRoleForOverride(role.id);
																		setShowRoleOverrideModal(true);
																	}}
																	className="flex items-center gap-[6px] px-[12px] py-[6px] bg-[#5048ED] text-white rounded-[8px] hover:bg-[#4338CA] transition-colors text-[13px] font-medium"
																>
																	<svg width="14" height="14" viewBox="0 0 14 14" fill="none">
																		<path d="M9.917 1.75004C10.0696 1.59743 10.2514 1.47608 10.4517 1.39308C10.652 1.31008 10.8672 1.26709 11.0845 1.26709C11.3017 1.26709 11.517 1.31008 11.7173 1.39308C11.9176 1.47608 12.0994 1.59743 12.252 1.75004C12.4046 1.90265 12.5259 2.08445 12.6089 2.28475C12.6919 2.48505 12.7349 2.70029 12.7349 2.91754C12.7349 3.13479 12.6919 3.35003 12.6089 3.55033C12.5259 3.75064 12.4046 3.93243 12.252 4.08504L4.37557 11.9617L1.16699 12.8334L2.03866 9.62504L9.917 1.75004Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
																	</svg>
																	Configure
																</button>
															</div>
														</div>
													</div>
													
													{hasOverride && (
														<div className="p-[16px] border-t border-[#E5E7EB] bg-[#FAFBFC]">
															<div className="grid grid-cols-1 md:grid-cols-2 gap-[16px]">
																{/* Password Policy Overrides */}
																{roleAuthConfig.password_policy && (
																	<div>
																		<h5 className="text-[12px] font-medium text-[#6B7280] mb-[8px]">Password Policy</h5>
																		<div className="space-y-[4px]">
																			{roleAuthConfig.password_policy.min_length > (authConfig.password_policy?.min_length || 8) && (
																				<div className="flex items-center gap-[6px] text-[11px]">
																					<span className="text-[#10B981]">↑</span>
																					<span className="text-[#111827]">Min length: {roleAuthConfig.password_policy.min_length} chars</span>
																				</div>
																			)}
																			{roleAuthConfig.password_policy.password_expiry_days < (authConfig.password_policy?.password_expiry_days || 90) && (
																				<div className="flex items-center gap-[6px] text-[11px]">
																					<span className="text-[#10B981]">↑</span>
																					<span className="text-[#111827]">Expires in: {roleAuthConfig.password_policy.password_expiry_days} days</span>
																				</div>
																			)}
																			{roleAuthConfig.password_policy.require_uppercase && !authConfig.password_policy?.require_uppercase && (
																				<div className="flex items-center gap-[6px] text-[11px]">
																					<span className="text-[#10B981]">✓</span>
																					<span className="text-[#111827]">Requires uppercase</span>
																				</div>
																			)}
																			{roleAuthConfig.password_policy.require_special_chars && !authConfig.password_policy?.require_special_chars && (
																				<div className="flex items-center gap-[6px] text-[11px]">
																					<span className="text-[#10B981]">✓</span>
																					<span className="text-[#111827]">Requires special chars</span>
																				</div>
																			)}
																		</div>
																	</div>
																)}

																{/* 2FA Override */}
																{roleAuthConfig.two_factor_auth?.required && !authConfig.two_factor_auth?.required && (
																	<div>
																		<h5 className="text-[12px] font-medium text-[#6B7280] mb-[8px]">Two-Factor Auth</h5>
																		<div className="flex items-center gap-[6px] text-[11px]">
																			<span className="text-[#10B981]">✓</span>
																			<span className="text-[#111827]">2FA required for this role</span>
																		</div>
																	</div>
																)}
															</div>
														</div>
													)}
												</div>
											);
										})}
									</div>
								) : (
									<div className="text-center py-[32px]">
										<p className="text-[14px] text-[#6B7280]">No user roles available</p>
									</div>
								)}
							</div>
						</div>
					)}

					{activeSection === 'saml' && (
						<div className="space-y-[24px]">
							<div className="bg-white rounded-[16px] border border-[#E5E7EB] p-[24px]">
								<div className="mb-[24px] flex items-center justify-between">
									<div>
										<h3 className="text-[16px] font-semibold text-[#111827]">SAML Providers</h3>
										<p className="text-[13px] text-[#6B7280] mt-[4px]">
											Configure SAML-based single sign-on providers
										</p>
									</div>
									<button
										onClick={() => setShowSAMLModal(true)}
										className="flex items-center gap-[8px] px-[16px] py-[8px] bg-[#5048ED] text-white rounded-[8px] hover:bg-[#4338CA] transition-colors"
									>
										<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
											<path d="M8 1V15M1 8H15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
										</svg>
										<span className="font-medium text-[14px]">Add Provider</span>
									</button>
								</div>

								{loadingSAML ? (
									<div className="flex items-center justify-center py-[32px]">
										<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#5048ED]"></div>
									</div>
								) : samlProviders && samlProviders.length > 0 ? (
									<div className="space-y-[12px]">
										{samlProviders.map((provider) => (
											<div key={provider.id} className="border border-[#E5E7EB] rounded-[12px] p-[16px] hover:bg-[#F9FAFB] transition-colors">
												<div className="flex items-center justify-between">
													<div className="flex items-center gap-[12px]">
														<div className="w-[40px] h-[40px] bg-gradient-to-br from-[#5048ED] to-[#346BD4] rounded-[10px] flex items-center justify-center">
															<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
																<path d="M10 2C5.58 2 2 4.69 2 8c0 2.25 1.38 4.21 3.5 5.27V17c0 .55.45 1 1 1h7c.55 0 1-.45 1-1v-3.73c2.12-1.06 3.5-3.02 3.5-5.27 0-3.31-3.58-6-8-6z" fill="currentColor"/>
															</svg>
														</div>
														<div>
															<h4 className="text-[14px] font-semibold text-[#111827]">{provider.label}</h4>
															<p className="text-[12px] text-[#6B7280]">Entity ID: {provider.sp_entityId}</p>
														</div>
													</div>
													<div className="flex items-center gap-[8px]">
														<button
															onClick={() => {
																setEditingSAMLProvider(provider);
																setShowSAMLModal(true);
															}}
															className="flex items-center gap-[6px] px-[12px] py-[6px] text-[#5048ED] hover:bg-[#EFF6FF] rounded-[8px] transition-colors text-[13px] font-medium"
														>
															<svg width="14" height="14" viewBox="0 0 14 14" fill="none">
																<path d="M9.917 1.75004C10.0696 1.59743 10.2514 1.47608 10.4517 1.39308C10.652 1.31008 10.8672 1.26709 11.0845 1.26709C11.3017 1.26709 11.517 1.31008 11.7173 1.39308C11.9176 1.47608 12.0994 1.59743 12.252 1.75004C12.4046 1.90265 12.5259 2.08445 12.6089 2.28475C12.6919 2.48505 12.7349 2.70029 12.7349 2.91754C12.7349 3.13479 12.6919 3.35003 12.6089 3.55033C12.5259 3.75064 12.4046 3.93243 12.252 4.08504L4.37557 11.9617L1.16699 12.8334L2.03866 9.62504L9.917 1.75004Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
															</svg>
															Edit
														</button>
														<button
															onClick={async () => {
																if (window.confirm(`Are you sure you want to delete "${provider.label}"?`)) {
																	try {
																		const { success } = await triggerApi({
																			url: `/api/v1/apps/${appId}/saml-providers/${provider.id}/`,
																			type: 'DELETE',
																			loader: true,
																		});
																		if (success) {
																			setSAMLProviders(samlProviders.filter(p => p.id !== provider.id));
																			dispatch(toggleRerenderPage());
																		}
																	} catch (error) {
																		console.error('Error deleting SAML provider:', error);
																	}
																}
															}}
															className="flex items-center gap-[6px] px-[12px] py-[6px] text-[#DC2626] hover:bg-[#FEE2E2] rounded-[8px] transition-colors text-[13px] font-medium"
														>
															<svg width="14" height="14" viewBox="0 0 14 14" fill="none">
																<path d="M1 3h12M5.5 5.5v5M8.5 5.5v5M2 3l0.5 9c0 0.55 0.45 1 1 1h7c0.55 0 1-0.45 1-1l0.5-9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
															</svg>
															Delete
														</button>
													</div>
												</div>
											</div>
										))}
									</div>
								) : (
									<div className="text-center py-[32px]">
										<div className="w-[80px] h-[80px] bg-[#F3F4F6] rounded-full flex items-center justify-center mx-auto mb-[16px]">
											<svg width="40" height="40" viewBox="0 0 40 40" fill="none">
												<path d="M20 4C11.1634 4 4 11.1634 4 20C4 28.8366 11.1634 36 20 36C28.8366 36 36 28.8366 36 20C36 11.1634 28.8366 4 20 4Z" stroke="#D1D5DB" strokeWidth="1.5"/>
												<path d="M20 12V28M12 20H28" stroke="#D1D5DB" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
											</svg>
										</div>
										<p className="text-[14px] text-[#6B7280] mb-[16px]">No SAML providers configured yet</p>
										<button
											onClick={() => setShowSAMLModal(true)}
											className="inline-flex items-center gap-[8px] px-[16px] py-[8px] bg-[#5048ED] text-white rounded-[8px] hover:bg-[#4338CA] transition-colors"
										>
											<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
												<path d="M8 1V15M1 8H15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
											</svg>
											<span className="font-medium text-[14px]">Add First Provider</span>
										</button>
									</div>
								)}
							</div>
						</div>
					)}
				</>
			) : null}

			{/* Auth Setup Modal - Also shown when editing existing config */}
			{isAuthConfigured() && (
				<AuthSetupModal
					show={showAuthSetupModal}
					onClose={() => setShowAuthSetupModal(false)}
					initialData={authConfig}
					roles={roles}
					onComplete={async (authData) => {
						// Transform to expected format matching the schema
						const updatedAuthConfig = {
							login_methods: {
								password: {
									enabled: authData.login_methods.password.enabled,
									forgot_password_enabled: authData.login_methods.password.forgot_password_enabled,
									password_reset_link_expiry_hours: authConfig?.login_methods?.password?.password_reset_link_expiry_hours || 24,
									allowed_usernames: authData.login_methods.allowed_usernames,
								},
								otp: {
									enabled: authData.login_methods.otp.enabled,
									allowed_methods: authData.login_methods.otp.allowed_methods || [],
									email_content: authData.login_methods.otp.email_content || '',
									email_subject: authData.login_methods.otp.email_subject || '',
									email_hook: authData.login_methods.otp.email_webhook || '',
									email_config_key: authData.login_methods.otp.email_config_key || '',
									sms_hook: authData.login_methods.otp.sms_webhook || '',
									sms_content: authData.login_methods.otp.sms_content || '',
									sms_config_key: authData.login_methods.otp.sms_config_key || '',
									sms_extra_data: authData.login_methods.otp.sms_extra_data || '',
									otp_expiry: authData.login_methods.otp.otp_expiry || 300,
								},
								sso: { enabled: authData.login_methods.sso.enabled },
								oidc: { enabled: authData.login_methods.oidc.enabled },
							},
							session_policy: {
								max_concurrent_sessions: authData.session_policy.max_concurrent_sessions,
							},
							password_policy: {
								min_length: authData.password_policy.min_length,
								allow_change: authData.password_policy.allow_change,
								require_numbers: authData.password_policy.require_numbers,
								require_lowercase: authData.password_policy.require_lowercase,
								require_uppercase: authData.password_policy.require_uppercase,
								password_expiry_days: authData.password_policy.password_expiry_days,
								password_repeat_days: authData.password_policy.password_repeat_days,
								require_special_chars: authData.password_policy.require_special_chars,
								password_history_count: authData.password_policy.password_history_count,
								reset: {
									enabled: authData.login_methods.password.forgot_password_enabled,
									expiry: authData.login_methods.password.reset_expiry_minutes * 60, // Convert minutes to seconds
									allowed_methods: (() => {
										const methods = [];
										if (authData.login_methods.password.reset_via_email) methods.push('email');
										if (authData.login_methods.password.reset_via_sms) methods.push('sms');
										return methods.length > 0 ? methods : ['email'];
									})(),
									by_code: authData.login_methods.password.reset_method === 'code',
									by_email: authData.login_methods.password.reset_via_email || false,
									login_after_reset: false,
									max_attempts: 3,
									email_hook: authData.login_methods.password.reset_email_webhook || '',
									email_content: authData.login_methods.password.reset_email_content || '',
									email_subject: authData.login_methods.password.reset_email_subject || '',
									email_config_key: authData.login_methods.password.reset_email_config_key || '',
									sms_hook: authData.login_methods.password.reset_sms_webhook || '',
									sms_content: authData.login_methods.password.reset_sms_content || '',
									sms_config_key: authData.login_methods.password.reset_sms_config_key || '',
									sms_extra_data: authData.login_methods.password.reset_sms_extra_data || '',
								},
							},
							two_factor_auth: {
								required: authData.two_factor_auth.required,
								allowed_methods: authData.two_factor_auth.allowedMethods || [],
								enforced_from: null,
								grace_period_days: null,
								skip_for_sso: false,
								email_hook: authData.two_factor_auth.email_hook || '',
								sms_hook: authData.two_factor_auth.sms_hook || '',
							},
						};

						// Save the configuration
						const tempValues = {
							auth_config: JSON.stringify(updatedAuthConfig)
						};
						const dynamicFormData = transformToFormData(tempValues);

						try {
							const { response, success } = await triggerApi({
								url: `/api/v1/apps/${appId}/`,
								type: 'PUT',
								loader: true,
								payload: dynamicFormData,
							});

							if (success && response) {
								dispatch(toggleRerenderPage());
								setShowAuthSetupModal(false);
							}
						} catch (error) {
							console.error('Error saving authentication configuration:', error);
						}
					}}
				/>
			)}

			{/* Role Override Modal */}
			{isAuthConfigured() && (
				<RoleOverrideModal
					show={showRoleOverrideModal}
					onClose={() => {
						setShowRoleOverrideModal(false);
						setSelectedRoleForOverride(null);
					}}
					roles={roles}
					globalAuthConfig={authConfig}
					currentOverrides={roles.reduce((acc, role) => {
						if (role.auth_config) {
							acc[role.id] = role.auth_config;
						}
						return acc;
					}, {})}
					initialSelectedRoleId={selectedRoleForOverride}
					onSave={async (roleId, overrideConfig) => {
						// Prepare auth_config JSON as form data
						const tempValues = {
							auth_config: JSON.stringify(overrideConfig || {})
						};
						const dynamicFormData = transformToFormData(tempValues);

						try {
							const { response, success } = await triggerApi({
								url: `/api/v1/apps/${appId}/roles/${roleId}/`,
								type: 'PUT',
								loader: true,
								payload: dynamicFormData,
							});

							if (success && response) {
								dispatch(toggleRerenderPage());
								setShowRoleOverrideModal(false);
								setSelectedRoleForOverride(null);
								// Reload page after saving role override
								setTimeout(() => {
									window.location.reload();
								}, 500);
							}
						} catch (error) {
							console.error('Error saving role override configuration:', error);
						}
					}}
				/>
			)}

			{/* SAML Provider Modal */}
			<SAMLProviderModal
				isOpen={showSAMLModal}
				initialData={editingSAMLProvider}
				onClose={() => {
					setShowSAMLModal(false);
					setEditingSAMLProvider(null);
				}}
				onSave={async (formData) => {
					try {
						// Convert form data to FormData object for API
						const dynamicFormData = transformToFormData(formData);

						const isUpdate = editingSAMLProvider !== null;
						const url = isUpdate
							? `/api/v1/apps/${appId}/saml-providers/${editingSAMLProvider.id}/`
							: `/api/v1/apps/${appId}/saml-providers/`;
						const method = isUpdate ? 'PUT' : 'POST';

						const { response, success } = await triggerApi({
							url,
							type: method,
							loader: true,
							payload: dynamicFormData,
						});

						if (success && response) {
							if (isUpdate) {
								// Update existing provider in list
								setSAMLProviders(samlProviders.map(p => p.id === editingSAMLProvider.id ? response : p));
							} else {
								// Add new provider to list
								setSAMLProviders([...samlProviders, response]);
							}
							setShowSAMLModal(false);
							setEditingSAMLProvider(null);
							dispatch(toggleRerenderPage());
						}
					} catch (error) {
						console.error('Error saving SAML provider:', error);
					}
				}}
			/>
		</div>
	);
};

export default ModernAuthConfig;