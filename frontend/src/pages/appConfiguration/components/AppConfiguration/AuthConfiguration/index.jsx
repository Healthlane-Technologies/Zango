import React from "react";
import DetailsTable from "./DetailsTable";
import UpdateAuthConfigButton from "./UpdateAuthConfigButton";

const AuthConfiguration = () => {
	// Mock data for demonstration - will be replaced with API calls later
	const mockAuthConfigData = {
		auth_config: {
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
				allowed_usernames: ["email", "phone"],
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
				allowedMethods: ["email", "sms"],
			},
		},
	};

	const ConfigCard = ({ title, description, icon, status, children }) => (
		<div className="bg-white rounded-[16px] border border-[#E5E7EB] shadow-sm hover:shadow-md transition-shadow duration-200">
			<div className="p-[24px]">
				<div className="flex items-center justify-between mb-[16px]">
					<div className="flex items-center gap-[12px]">
						<div className="flex h-[40px] w-[40px] items-center justify-center rounded-[10px] bg-[#5048ED]">
							{icon}
						</div>
						<div>
							<h3 className="font-source-sans-pro text-[16px] font-semibold leading-[24px] text-[#111827]">
								{title}
							</h3>
							<p className="font-lato text-[12px] leading-[16px] text-[#6B7280]">
								{description}
							</p>
						</div>
					</div>
					{status && (
						<span className={`px-[12px] py-[4px] rounded-full text-[11px] font-semibold ${
							status === 'active' 
								? 'bg-[#D1FAE5] text-[#065F46]' 
								: 'bg-[#FEE2E2] text-[#991B1B]'
						}`}>
							{status.toUpperCase()}
						</span>
					)}
				</div>
				{children}
			</div>
		</div>
	);

	const StatusBadge = ({ enabled, label }) => (
		<span className={`inline-flex items-center gap-[6px] px-[12px] py-[6px] rounded-[20px] text-[12px] font-medium ${
			enabled 
				? 'bg-[#D1FAE5] text-[#065F46]' 
				: 'bg-[#F3F4F6] text-[#6B7280]'
		}`}>
			<div className={`w-[8px] h-[8px] rounded-full ${enabled ? 'bg-[#10B981]' : 'bg-[#9CA3AF]'}`}></div>
			{label}
		</span>
	);

	const InfoRow = ({ label, value, isArray = false }) => (
		<div className="flex items-center justify-between py-[8px] border-b border-[#F3F4F6] last:border-b-0">
			<span className="font-lato text-[13px] font-medium text-[#6B7280]">{label}</span>
			<div className="flex items-center gap-[8px]">
				{isArray ? (
					<div className="flex gap-[6px]">
						{value.map((item, index) => (
							<span key={index} className="px-[8px] py-[4px] bg-[#EFF6FF] text-[#5048ED] rounded-[6px] text-[11px] font-medium">
								{item.charAt(0).toUpperCase() + item.slice(1)}
							</span>
						))}
					</div>
				) : (
					<span className="font-lato text-[13px] font-semibold text-[#111827]">{value}</span>
				)}
			</div>
		</div>
	);

	return (
		<div className="space-y-[24px]">
			{/* Header */}
			<div className="bg-white rounded-[16px] border border-[#E5E7EB] shadow-sm p-[24px]">
				<div className="flex items-center justify-between">
					<div className="flex items-center gap-[16px]">
						<div className="flex h-[56px] w-[56px] items-center justify-center rounded-[12px] bg-[#5048ED] shadow-lg">
							<svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
								<path d="M21 14V11.667C21 7.78 17.866 4.667 14 4.667C10.134 4.667 7 7.78 7 11.667V14M5.833 14H22.167C22.812 14 23.333 14.522 23.333 15.167V23.333C23.333 23.978 22.812 24.5 22.167 24.5H5.833C5.188 24.5 4.667 23.978 4.667 23.333V15.167C4.667 14.522 5.188 14 5.833 14Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
							</svg>
						</div>
						<div>
							<h1 className="font-source-sans-pro text-[24px] font-bold leading-[32px] text-[#111827]">
								Authentication Configuration
							</h1>
							<p className="font-lato text-[14px] leading-[20px] text-[#6B7280] mt-[2px]">
								Manage security settings and authentication methods for your application
							</p>
						</div>
					</div>
					<UpdateAuthConfigButton />
				</div>
			</div>

			{/* Configuration Cards */}
			<div className="grid grid-cols-1 lg:grid-cols-2 gap-[24px]">
				{/* Login Methods */}
				<ConfigCard
					title="Login Methods"
					description="Available authentication methods"
					icon={
						<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
							<path d="M15 10V8C15 5.23858 12.7614 3 10 3C7.23858 3 5 5.23858 5 8V10M4 10H16C16.5523 10 17 10.4477 17 11V17C17 17.5523 16.5523 18 16 18H4C3.44772 18 3 17.5523 3 17V11C3 10.4477 3.44772 10 4 10Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
						</svg>
					}
				>
					<div className="space-y-[12px]">
						<div className="flex flex-wrap gap-[8px]">
							<StatusBadge enabled={mockAuthConfigData.auth_config.login_methods.password.enabled} label="Password" />
							<StatusBadge enabled={mockAuthConfigData.auth_config.login_methods.otp.enabled} label="OTP" />
							<StatusBadge enabled={mockAuthConfigData.auth_config.login_methods.sso.enabled} label="SSO" />
							<StatusBadge enabled={mockAuthConfigData.auth_config.login_methods.oidc.enabled} label="OIDC" />
						</div>
						<InfoRow 
							label="Allowed Username Types" 
							value={mockAuthConfigData.auth_config.login_methods.allowed_usernames} 
							isArray={true}
						/>
						<InfoRow 
							label="Password Reset Expiry" 
							value={`${mockAuthConfigData.auth_config.login_methods.password.password_reset_link_expiry_hours} hours`} 
						/>
					</div>
				</ConfigCard>

				{/* Two-Factor Authentication */}
				<ConfigCard
					title="Two-Factor Authentication"
					description="Additional security layer settings"
					status={mockAuthConfigData.auth_config.two_factor_auth.required ? 'active' : 'inactive'}
					icon={
						<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
							<path d="M10 2L12.5 4.5H17.5V9.5L15 12L17.5 14.5V19.5H12.5L10 17L7.5 19.5H2.5V14.5L5 12L2.5 9.5V4.5H7.5L10 2Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
							<circle cx="10" cy="10" r="2.5" stroke="white" strokeWidth="2"/>
						</svg>
					}
				>
					<div className="space-y-[12px]">
						<InfoRow 
							label="Required for all users" 
							value={mockAuthConfigData.auth_config.two_factor_auth.required ? 'Yes' : 'No'} 
						/>
						<InfoRow 
							label="Available Methods" 
							value={mockAuthConfigData.auth_config.two_factor_auth.allowedMethods} 
							isArray={true}
						/>
					</div>
				</ConfigCard>

				{/* Session Policy */}
				<ConfigCard
					title="Session Management"
					description="Session security and management policies"
					icon={
						<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
							<path d="M10 2V10L15 15" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
							<circle cx="10" cy="10" r="8" stroke="white" strokeWidth="2"/>
						</svg>
					}
				>
					<div className="space-y-[12px]">
						<InfoRow 
							label="Max Concurrent Sessions" 
							value={mockAuthConfigData.auth_config.session_policy.max_concurrent_sessions || 'Unlimited'} 
						/>
						<InfoRow 
							label="Force Logout on Password Change" 
							value={mockAuthConfigData.auth_config.session_policy.force_logout_on_password_change ? 'Yes' : 'No'} 
						/>
					</div>
				</ConfigCard>

				{/* Password Policy */}
				<ConfigCard
					title="Password Policy"
					description="Password requirements and security rules"
					icon={
						<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
							<path d="M14 8V6C14 3.79086 12.2091 2 10 2C7.79086 2 6 3.79086 6 6V8M5 8H15C15.5523 8 16 8.44772 16 9V16C16 16.5523 15.5523 17 15 17H5C4.44772 17 4 16.5523 4 16V9C4 8.44772 4.44772 8 5 8Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
							<circle cx="10" cy="12.5" r="1.5" fill="white"/>
						</svg>
					}
				>
					<div className="space-y-[12px]">
						<InfoRow 
							label="Minimum Length" 
							value={`${mockAuthConfigData.auth_config.password_policy.min_length} characters`} 
						/>
						<InfoRow 
							label="Password Expiry" 
							value={`${mockAuthConfigData.auth_config.password_policy.password_expiry_days} days`} 
						/>
						<InfoRow 
							label="History Count" 
							value={mockAuthConfigData.auth_config.password_policy.password_history_count} 
						/>
						<div className="flex flex-wrap gap-[6px] mt-[12px]">
							<span className="px-[8px] py-[4px] bg-[#EFF6FF] text-[#5048ED] rounded-[6px] text-[11px] font-medium">
								Numbers Required
							</span>
							<span className="px-[8px] py-[4px] bg-[#EFF6FF] text-[#5048ED] rounded-[6px] text-[11px] font-medium">
								Uppercase Required
							</span>
							<span className="px-[8px] py-[4px] bg-[#EFF6FF] text-[#5048ED] rounded-[6px] text-[11px] font-medium">
								Lowercase Required
							</span>
							<span className="px-[8px] py-[4px] bg-[#EFF6FF] text-[#5048ED] rounded-[6px] text-[11px] font-medium">
								Special Characters Required
							</span>
						</div>
					</div>
				</ConfigCard>
			</div>
		</div>
	);
};

export default AuthConfiguration;