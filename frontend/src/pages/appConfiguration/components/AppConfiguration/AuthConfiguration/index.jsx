import { useState } from "react";
import UpdateAuthConfigButton from "./UpdateAuthConfigButton";
import SAMLProviderModal from "./SAMLProviderModal";
import { useSelector } from "react-redux";
import { selectAppConfigurationData } from '../../../slice';

const AuthConfiguration = () => {
    const [isSAMLModalOpen, setIsSAMLModalOpen] = useState(false);
    const appConfigurationData = useSelector(
        selectAppConfigurationData
    );

    // Show loading only when appConfigurationData is null/undefined
    // Once we have appConfigurationData (even if auth_config is missing), show the page
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

	console.log("App Configuration Data:", appConfigurationData);
	const auth_config = appConfigurationData?.app?.auth_config;

    // If appConfigurationData exists but auth_config is missing, show empty state
    if (!auth_config) {
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

                {/* Empty State */}
                <div className="bg-white rounded-[16px] border border-[#E5E7EB] shadow-sm p-[48px] text-center">
                    <div className="flex h-[64px] w-[64px] items-center justify-center rounded-[12px] bg-[#F3F4F6] mx-auto mb-[24px]">
                        <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M16 2V16L24 24" stroke="#6B7280" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                            <circle cx="16" cy="16" r="14" stroke="#6B7280" strokeWidth="2"/>
                        </svg>
                    </div>
                    <h3 className="font-source-sans-pro text-[18px] font-semibold leading-[24px] text-[#111827] mb-[8px]">
                        No Authentication Configuration Found
                    </h3>
                    <p className="font-lato text-[14px] leading-[20px] text-[#6B7280]">
                        Authentication configuration is not available. Please check your application settings.
                    </p>
                </div>
            </div>
        );
    }

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
                        {value?.map((item, index) => (
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
                            <StatusBadge enabled={auth_config.login_methods?.password?.enabled} label="Password" />
                            <StatusBadge enabled={auth_config.login_methods?.otp?.enabled} label="OTP" />
                            <StatusBadge enabled={auth_config.login_methods?.sso?.enabled} label="SSO" />
                            <StatusBadge enabled={auth_config.login_methods?.oidc?.enabled} label="OIDC" />
                        </div>
                        <InfoRow
                            label="Allowed Username Types"
                            value={auth_config.login_methods?.allowed_usernames || []}
                            isArray={true}
                        />
                        <InfoRow
                            label="Password Reset Expiry"
                            value={`${auth_config.login_methods?.password?.password_reset_link_expiry_hours || 0} hours`}
                        />
                    </div>
                </ConfigCard>

                {/* Two-Factor Authentication */}
                <ConfigCard
                    title="Two-Factor Authentication"
                    description="Additional security layer settings"
                    status={auth_config.two_factor_auth?.required ? 'active' : 'inactive'}
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
                            value={auth_config.two_factor_auth?.required ? 'Yes' : 'No'}
                        />
                        <InfoRow
                            label="Available Methods"
                            value={auth_config.two_factor_auth?.allowedMethods || []}
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
                            value={auth_config.session_policy?.max_concurrent_sessions || 'Unlimited'}
                        />
                        <InfoRow
                            label="Force Logout on Password Change"
                            value={auth_config.session_policy?.force_logout_on_password_change ? 'Yes' : 'No'}
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
							value={`${auth_config.password_policy?.min_length || 0} characters`}
						/>
						<InfoRow
							label="Password Expiry"
							value={`${auth_config.password_policy?.password_expiry_days || 0} days`}
						/>
						<InfoRow
							label="History Count"
							value={auth_config.password_policy?.password_history_count || 0}
						/>
						<InfoRow
							label="Numbers Required"
							value={auth_config.password_policy?.require_numbers ? "Yes" : "No"}
						/>
						<InfoRow
							label="Uppercase Required"
							value={auth_config.password_policy?.require_uppercase ? "Yes" : "No"}
						/>
						<InfoRow
							label="Lowercase Required"
							value={auth_config.password_policy?.require_lowercase ? "Yes" : "No"}
						/>
						<InfoRow
							label="Special Characters Required"
							value={auth_config.password_policy?.require_special_chars ? "Yes" : "No"}
						/>
					</div>
				</ConfigCard>

            </div>

            {/* SAML Configuration Section */}
            <div className="space-y-[24px]">
                {/* SAML Section Header */}
                <div className="bg-white rounded-[16px] border border-[#E5E7EB] shadow-sm p-[24px]">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-[16px]">
                            <div className="flex h-[56px] w-[56px] items-center justify-center rounded-[12px] bg-[#5048ED] shadow-lg">
                                <svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M14 2C7.373 2 2 7.373 2 14C2 20.627 7.373 26 14 26C20.627 26 26 20.627 26 14C26 7.373 20.627 2 14 2ZM14 5C18.967 5 23 9.033 23 14C23 18.967 18.967 23 14 23C9.033 23 5 18.967 5 14C5 9.033 9.033 5 14 5Z" fill="white"/>
                                    <path d="M14 7C10.134 7 7 10.134 7 14C7 17.866 10.134 21 14 21C17.866 21 21 17.866 21 14C21 10.134 17.866 7 14 7ZM14 9C16.761 9 19 11.239 19 14C19 16.761 16.761 19 14 19C11.239 19 9 16.761 9 14C9 11.239 11.239 9 14 9Z" fill="white"/>
                                </svg>
                            </div>
                            <div>
                                <h2 className="font-source-sans-pro text-[20px] font-bold leading-[28px] text-[#111827]">
                                    SAML Configuration
                                </h2>
                                <p className="font-lato text-[14px] leading-[20px] text-[#6B7280] mt-[2px]">
                                    Manage SAML authentication providers and security settings
                                </p>
                            </div>
                        </div>
                        <button
                            onClick={() => setIsSAMLModalOpen(true)}
                            className="flex items-center gap-[8px] px-[16px] py-[10px] bg-[#5048ED] text-white rounded-[8px] hover:bg-[#3D2BA1] transition-colors duration-200 font-medium text-[14px]">
                            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M10 3V17M3 10H17" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                            </svg>
                            Add Provider
                        </button>
                    </div>
                </div>

                {/* SAML Providers Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-[24px]">
                    {/* SAML Providers Overview */}
                    <ConfigCard
                        title="Configured Providers"
                        description="Currently active SAML providers"
                        icon={
                            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M10 2C5.58172 2 2 5.58172 2 10C2 14.4183 5.58172 18 10 18C14.4183 18 18 14.4183 18 10C18 5.58172 14.4183 2 10 2ZM10 4C13.3137 4 16 6.68629 16 10C16 13.3137 13.3137 16 10 16C6.68629 16 4 13.3137 4 10C4 6.68629 6.68629 4 10 4Z" fill="white"/>
                                <path d="M10 5C7.23858 5 5 7.23858 5 10C5 12.7614 7.23858 15 10 15C12.7614 15 15 12.7614 15 10C15 7.23858 12.7614 5 10 5ZM10 7C11.6569 7 13 8.34315 13 10C13 11.6569 11.6569 13 10 13C8.34315 13 7 11.6569 7 10C7 8.34315 8.34315 7 10 7Z" fill="white"/>
                            </svg>
                        }
                    >
                        <div className="space-y-[12px]">
                            <div className="flex items-center justify-between p-[12px] bg-[#F9FAFB] rounded-[8px] border border-[#E5E7EB]">
                                <div className="flex items-center gap-[12px]">
                                    <div className="flex h-[32px] w-[32px] items-center justify-center rounded-[8px] bg-[#5048ED]">
                                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M8 1C4.13401 1 1 4.13401 1 8C1 11.866 4.13401 15 8 15C11.866 15 15 11.866 15 8C15 4.13401 11.866 1 8 1Z" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                                            <path d="M8 4V8L11 10" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                                        </svg>
                                    </div>
                                    <div>
                                        <p className="font-lato text-[13px] font-semibold text-[#111827]">No providers configured</p>
                                        <p className="font-lato text-[12px] text-[#6B7280]">Add your first SAML provider</p>
                                    </div>
                                </div>
                            </div>
                            <button
                                onClick={() => setIsSAMLModalOpen(true)}
                                className="w-full px-[16px] py-[10px] border-2 border-[#5048ED] text-[#5048ED] rounded-[8px] hover:bg-[#5048ED] hover:text-white transition-colors duration-200 font-medium text-[14px]">
                                Configure SAML Provider
                            </button>
                        </div>
                    </ConfigCard>

                    {/* SAML Security Settings */}
                    <ConfigCard
                        title="Default Security Settings"
                        description="SAML security configuration"
                        icon={
                            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M15 9V6C15 3.23858 12.7614 1 10 1C7.23858 1 5 3.23858 5 6V9M4 9H16C16.5523 9 17 9.44772 17 10V17C17 17.5523 16.5523 18 16 18H4C3.44772 18 3 17.5523 3 17V10C3 9.44772 3.44772 9 4 9Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                            </svg>
                        }
                    >
                        <div className="space-y-[12px]">
                            <InfoRow
                                label="Strict Mode"
                                value="Enabled"
                            />
                            <InfoRow
                                label="Message Signing"
                                value="Optional"
                            />
                            <InfoRow
                                label="Assertion Encryption"
                                value="Optional"
                            />
                            <div className="pt-[8px]">
                                <button className="text-[#5048ED] hover:text-[#3D2BA1] font-medium text-[13px] transition-colors duration-200">
                                    Edit Security Settings →
                                </button>
                            </div>
                        </div>
                    </ConfigCard>
                </div>

                {/* SAML Provider Details Section */}
                <div className="bg-white rounded-[16px] border border-[#E5E7EB] shadow-sm p-[24px]">
                    <h3 className="font-source-sans-pro text-[16px] font-semibold leading-[24px] text-[#111827] mb-[16px]">
                        Quick Setup Guide
                    </h3>
                    <div className="space-y-[16px]">
                        <div className="flex gap-[12px] p-[12px] bg-[#F0F9FF] rounded-[8px] border border-[#E0F2FE]">
                            <div className="flex h-[24px] w-[24px] items-center justify-center rounded-full bg-[#5048ED] flex-shrink-0 mt-[2px]">
                                <span className="text-white text-[12px] font-bold">1</span>
                            </div>
                            <div>
                                <p className="font-lato text-[13px] font-semibold text-[#1E40AF]">Gather IdP Information</p>
                                <p className="font-lato text-[12px] text-[#1E40AF] mt-[2px]">Collect Entity ID, SSO URL, and x509 certificate from your identity provider</p>
                            </div>
                        </div>
                        <div className="flex gap-[12px] p-[12px] bg-[#F0F9FF] rounded-[8px] border border-[#E0F2FE]">
                            <div className="flex h-[24px] w-[24px] items-center justify-center rounded-full bg-[#5048ED] flex-shrink-0 mt-[2px]">
                                <span className="text-white text-[12px] font-bold">2</span>
                            </div>
                            <div>
                                <p className="font-lato text-[13px] font-semibold text-[#1E40AF]">Create SAML Provider</p>
                                <p className="font-lato text-[12px] text-[#1E40AF] mt-[2px]">Click "Add Provider" to create a new SAML configuration</p>
                            </div>
                        </div>
                        <div className="flex gap-[12px] p-[12px] bg-[#F0F9FF] rounded-[8px] border border-[#E0F2FE]">
                            <div className="flex h-[24px] w-[24px] items-center justify-center rounded-full bg-[#5048ED] flex-shrink-0 mt-[2px]">
                                <span className="text-white text-[12px] font-bold">3</span>
                            </div>
                            <div>
                                <p className="font-lato text-[13px] font-semibold text-[#1E40AF]">Configure IdP Settings</p>
                                <p className="font-lato text-[12px] text-[#1E40AF] mt-[2px]">Enter your identity provider credentials and URLs</p>
                            </div>
                        </div>
                        <div className="flex gap-[12px] p-[12px] bg-[#F0F9FF] rounded-[8px] border border-[#E0F2FE]">
                            <div className="flex h-[24px] w-[24px] items-center justify-center rounded-full bg-[#5048ED] flex-shrink-0 mt-[2px]">
                                <span className="text-white text-[12px] font-bold">4</span>
                            </div>
                            <div>
                                <p className="font-lato text-[13px] font-semibold text-[#1E40AF]">Test and Activate</p>
                                <p className="font-lato text-[12px] text-[#1E40AF] mt-[2px]">Validate the configuration and activate the provider</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* SAML Provider Modal */}
            <SAMLProviderModal
                isOpen={isSAMLModalOpen}
                onClose={() => setIsSAMLModalOpen(false)}
                onSave={(formData) => {
                    // Handle saving SAML provider
                    console.log("Saving SAML Provider:", formData);
                    // TODO: Integrate with API to save the SAML provider
                }}
            />
        </div>
    );
};

export default AuthConfiguration;
