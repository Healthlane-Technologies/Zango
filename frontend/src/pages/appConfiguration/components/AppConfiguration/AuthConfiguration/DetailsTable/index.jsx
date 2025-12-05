import React from "react";

const DetailsTable = ({ data }) => {
	if (!data) {
		return (
			<div className="flex h-[200px] items-center justify-center">
				<div className="text-[#A3ABB1]">No authentication configuration found</div>
			</div>
		);
	}

	const authConfig = data.auth_config || {};

	const StatusBadge = ({ enabled, enabledText = "Enabled", disabledText = "Disabled" }) => (
		<span className={`inline-flex items-center rounded-full px-[8px] py-[4px] text-[12px] font-medium ${
			enabled 
				? 'bg-green-100 text-green-800' 
				: 'bg-red-100 text-red-800'
		}`}>
			<div className={`mr-[4px] h-[6px] w-[6px] rounded-full ${
				enabled ? 'bg-green-600' : 'bg-red-600'
			}`} />
			{enabled ? enabledText : disabledText}
		</span>
	);

	const InfoCard = ({ title, icon, children }) => (
		<div className="rounded-[10px] border border-[#E5E7EB] bg-white p-[24px] shadow-sm hover:shadow-md transition-shadow">
			<div className="mb-[20px] flex items-center gap-[12px]">
				<div className="flex h-[36px] w-[36px] items-center justify-center rounded-[8px] bg-gradient-to-br from-[#EFF6FF] to-[#DBEAFE]">
					{icon}
				</div>
				<h3 className="font-source-sans-pro text-[16px] font-semibold leading-[24px] text-[#111827]">
					{title}
				</h3>
			</div>
			<div className="space-y-[16px]">
				{children}
			</div>
		</div>
	);

	const InfoRow = ({ label, value, type = "text" }) => (
		<div className="flex items-center justify-between py-[12px] border-b border-[#F3F4F6] last:border-b-0">
			<span className="font-lato text-[14px] leading-[20px] text-[#6B7280]">
				{label}
			</span>
			<div className="font-lato text-[14px] font-medium leading-[20px] text-[#111827]">
				{type === "badge" ? value : (
					<span className="text-right">{value}</span>
				)}
			</div>
		</div>
	);

	return (
		<div className="grid gap-[24px] lg:grid-cols-2">
			{/* Login Methods Card */}
			<InfoCard 
				title="Login Methods" 
				icon={
					<svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
						<path d="M13.5 9V7.5C13.5 5.01472 11.4853 3 9 3C6.51472 3 4.5 5.01472 4.5 7.5V9M3.75 9H14.25C14.6642 9 15 9.33579 15 9.75V15.75C15 16.1642 14.6642 16.5 14.25 16.5H3.75C3.33579 16.5 3 16.1642 3 15.75V9.75C3 9.33579 3.33579 9 3.75 9Z" stroke="#346BD4" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
					</svg>
				}
			>
				<InfoRow 
					label="Password Login" 
					value={<StatusBadge enabled={authConfig.login_methods?.password?.enabled} />}
					type="badge"
				/>
				{authConfig.login_methods?.password?.enabled && (
					<>
						<InfoRow 
							label="Forgot Password" 
							value={<StatusBadge enabled={authConfig.login_methods?.password?.forgot_password_enabled} />}
							type="badge"
						/>
						<InfoRow 
							label="Reset Link Expiry" 
							value={`${authConfig.login_methods?.password?.password_reset_link_expiry_hours || 24} hours`}
						/>
					</>
				)}
				<InfoRow 
					label="OTP Login" 
					value={<StatusBadge enabled={authConfig.login_methods?.otp?.enabled} />}
					type="badge"
				/>
				<InfoRow 
					label="SSO Login" 
					value={<StatusBadge enabled={authConfig.login_methods?.sso?.enabled} />}
					type="badge"
				/>
				<InfoRow 
					label="OIDC Login" 
					value={<StatusBadge enabled={authConfig.login_methods?.oidc?.enabled} />}
					type="badge"
				/>
				<InfoRow 
					label="Allowed Usernames" 
					value={
						Array.isArray(authConfig.login_methods?.allowed_usernames) 
							? authConfig.login_methods?.allowed_usernames?.join(", ") 
							: authConfig.login_methods?.allowed_usernames || "Not configured"
					}
				/>
			</InfoCard>

			{/* Session Policy Card */}
			<InfoCard 
				title="Session Policy" 
				icon={
					<svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
						<path d="M9 1.5V9L13.5 13.5" stroke="#346BD4" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
						<circle cx="9" cy="9" r="7.5" stroke="#346BD4" strokeWidth="1.5"/>
					</svg>
				}
			>
				<InfoRow 
					label="Max Concurrent Sessions" 
					value={authConfig.session_policy?.max_concurrent_sessions === 0 ? "Unlimited" : authConfig.session_policy?.max_concurrent_sessions?.toString() || "Not configured"}
				/>
				<InfoRow 
					label="Force Logout on Password Change" 
					value={<StatusBadge enabled={authConfig.session_policy?.force_logout_on_password_change} enabledText="Yes" disabledText="No" />}
					type="badge"
				/>
			</InfoCard>

			{/* Password Policy Card */}
			<InfoCard 
				title="Password Policy" 
				icon={
					<svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
						<path d="M12.75 7.5V6C12.75 3.51472 10.7353 1.5 8.25 1.5C5.76472 1.5 3.75 3.51472 3.75 6V7.5M3 7.5H13.5C13.9142 7.5 14.25 7.83579 14.25 8.25V15.75C14.25 16.1642 13.9142 16.5 13.5 16.5H3C2.58579 16.5 2.25 16.1642 2.25 15.75V8.25C2.25 7.83579 2.58579 7.5 3 7.5Z" stroke="#346BD4" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
						<circle cx="8.25" cy="12" r="1.5" fill="#346BD4"/>
					</svg>
				}
			>
				<InfoRow 
					label="Minimum Length" 
					value={`${authConfig.password_policy?.min_length || 8} characters`}
				/>
				<InfoRow 
					label="Allow Password Change" 
					value={<StatusBadge enabled={authConfig.password_policy?.allow_change} enabledText="Yes" disabledText="No" />}
					type="badge"
				/>
				<InfoRow 
					label="Require Numbers" 
					value={<StatusBadge enabled={authConfig.password_policy?.require_numbers} enabledText="Yes" disabledText="No" />}
					type="badge"
				/>
				<InfoRow 
					label="Require Lowercase" 
					value={<StatusBadge enabled={authConfig.password_policy?.require_lowercase} enabledText="Yes" disabledText="No" />}
					type="badge"
				/>
				<InfoRow 
					label="Require Uppercase" 
					value={<StatusBadge enabled={authConfig.password_policy?.require_uppercase} enabledText="Yes" disabledText="No" />}
					type="badge"
				/>
				<InfoRow 
					label="Require Special Characters" 
					value={<StatusBadge enabled={authConfig.password_policy?.require_special_chars} enabledText="Yes" disabledText="No" />}
					type="badge"
				/>
				<InfoRow 
					label="Password Expiry" 
					value={`${authConfig.password_policy?.password_expiry_days || 90} days`}
				/>
				<InfoRow 
					label="Password History Count" 
					value={authConfig.password_policy?.password_history_count?.toString() || "Not configured"}
				/>
			</InfoCard>

			{/* Two-Factor Authentication Card */}
			<InfoCard 
				title="Two-Factor Authentication" 
				icon={
					<svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
						<path d="M9 1.5L11.25 3.75H16.5V8.25L13.5 11.25L16.5 14.25V18.75H11.25L9 16.5L6.75 18.75H1.5V14.25L4.5 11.25L1.5 8.25V3.75H6.75L9 1.5Z" stroke="#346BD4" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
						<circle cx="9" cy="9" r="2.25" stroke="#346BD4" strokeWidth="1.5"/>
					</svg>
				}
			>
				<InfoRow 
					label="Required" 
					value={<StatusBadge enabled={authConfig.two_factor_auth?.required} enabledText="Yes" disabledText="No" />}
					type="badge"
				/>
				<InfoRow 
					label="Allowed Methods" 
					value={
						Array.isArray(authConfig.two_factor_auth?.allowedMethods) 
							? authConfig.two_factor_auth?.allowedMethods?.join(", ") 
							: authConfig.two_factor_auth?.allowedMethods || "Not configured"
					}
				/>
			</InfoCard>
		</div>
	);
};

export default DetailsTable;