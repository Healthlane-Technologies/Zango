import React, { useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { Formik } from 'formik';
import * as Yup from 'yup';

const AuthSetupModal = ({ show, onClose, onComplete, initialData = null, roles = [] }) => {
	const [currentStep, setCurrentStep] = useState(1);
	const totalSteps = 5; // Added role overrides step

	// Default setup data
	const defaultSetupData = {
		login_methods: {
			allowed_usernames: ['email'], // Default to email
			password: { 
				enabled: false, 
				forgot_password_enabled: false,
				reset_method: 'link', // 'link' or 'code'
				reset_expiry_minutes: 15,
				reset_via_sms: false,
				reset_via_email: true,
				reset_sms_webhook: '',
				reset_email_webhook: '',
				reset_sms_content: 'Your password reset code is: {{code}}. Valid for {{expiry}} minutes.',
				reset_email_subject: 'Password Reset Request',
				reset_email_content: 'Click the following link to reset your password: {{link}}. This link is valid for {{expiry}} minutes.',
			},
			sso: { enabled: false },
			oidc: { enabled: false },
			otp: { 
				enabled: false,
				sms_webhook: '',
				email_webhook: '',
				sms_content: 'Your OTP code is: {{otp}}. Valid for 10 minutes.',
				email_subject: 'Your OTP Verification Code',
				email_content: 'Your OTP code is: {{otp}}. This code is valid for 10 minutes.',
			},
		},
		password_policy: {
			min_length: 8,
			require_uppercase: true,
			require_lowercase: true,
			require_numbers: true,
			require_special_chars: false,
			password_history_count: 3,
			password_expiry_days: 90,
			allow_change: true,
		},
		two_factor_auth: {
			required: false,
			allowedMethods: ['email'],
		},
		session_policy: {
			max_concurrent_sessions: 0,
			force_logout_on_password_change: false,
		},
		role_overrides: {}, // { roleId: { password_policy: {...}, two_factor_auth: {...} } }
	};

	// Use initial data if provided (editing mode), otherwise use defaults
	const getInitialData = () => {
		if (!initialData) return defaultSetupData;
		
		return {
			login_methods: {
				allowed_usernames: initialData.login_methods?.allowed_usernames || ['email'],
				password: {
					enabled: initialData.login_methods?.password?.enabled || false,
					forgot_password_enabled: initialData.login_methods?.password?.forgot_password_enabled || false,
					reset_method: initialData.login_methods?.password?.reset_method || 'link',
					reset_expiry_minutes: initialData.login_methods?.password?.reset_expiry_minutes || 15,
					reset_via_sms: initialData.login_methods?.password?.reset_via_sms || false,
					reset_via_email: initialData.login_methods?.password?.reset_via_email || true,
					reset_sms_webhook: initialData.login_methods?.password?.reset_sms_webhook || '',
					reset_email_webhook: initialData.login_methods?.password?.reset_email_webhook || '',
					reset_sms_content: initialData.login_methods?.password?.reset_sms_content || defaultSetupData.login_methods.password.reset_sms_content,
					reset_email_subject: initialData.login_methods?.password?.reset_email_subject || defaultSetupData.login_methods.password.reset_email_subject,
					reset_email_content: initialData.login_methods?.password?.reset_email_content || defaultSetupData.login_methods.password.reset_email_content,
				},
				sso: { enabled: initialData.login_methods?.sso?.enabled || false },
				oidc: { enabled: initialData.login_methods?.oidc?.enabled || false },
				otp: { 
					enabled: initialData.login_methods?.otp?.enabled || false,
					sms_webhook: initialData.login_methods?.otp?.sms_webhook || '',
					email_webhook: initialData.login_methods?.otp?.email_webhook || '',
					sms_content: initialData.login_methods?.otp?.sms_content || defaultSetupData.login_methods.otp.sms_content,
					email_subject: initialData.login_methods?.otp?.email_subject || defaultSetupData.login_methods.otp.email_subject,
					email_content: initialData.login_methods?.otp?.email_content || defaultSetupData.login_methods.otp.email_content,
				},
			},
			password_policy: initialData.password_policy || defaultSetupData.password_policy,
			two_factor_auth: {
				required: initialData.two_factor_auth?.required || false,
				allowedMethods: initialData.two_factor_auth?.allowedMethods || ['email'],
			},
			session_policy: initialData.session_policy || defaultSetupData.session_policy,
			role_overrides: initialData.role_overrides || {},
		};
	};

	const [setupData, setSetupData] = useState(getInitialData());

	// Reset data when modal opens
	React.useEffect(() => {
		if (show) {
			setSetupData(getInitialData());
			setCurrentStep(1);
		}
	}, [show, initialData]);

	const handleNext = () => {
		if (currentStep < totalSteps) {
			setCurrentStep(currentStep + 1);
		} else {
			// Complete setup
			onComplete(setupData);
		}
	};

	const handleBack = () => {
		if (currentStep > 1) {
			setCurrentStep(currentStep - 1);
		}
	};

	const updateSetupData = (section, data) => {
		setSetupData(prev => ({
			...prev,
			[section]: { ...prev[section], ...data }
		}));
	};

	// Step components
	const StepIndicator = () => (
		<div className="flex items-center justify-center mb-[32px]">
			{[1, 2, 3, 4, 5].map((step) => (
				<div key={step} className="flex items-center">
					<div
						className={`w-[40px] h-[40px] rounded-full flex items-center justify-center font-medium text-[14px] transition-all ${
							step === currentStep
								? 'bg-[#5048ED] text-white shadow-lg'
								: step < currentStep
								? 'bg-[#10B981] text-white'
								: 'bg-[#E5E7EB] text-[#6B7280]'
						}`}
					>
						{step < currentStep ? (
							<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
								<path d="M13.5 4.5L6 12L2.5 8.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
							</svg>
						) : (
							step
						)}
					</div>
					{step < 5 && (
						<div className={`w-[60px] h-[2px] mx-[8px] transition-all ${
							step < currentStep ? 'bg-[#10B981]' : 'bg-[#E5E7EB]'
						}`} />
					)}
				</div>
			))}
		</div>
	);

	// Step 1: Login Methods
	const Step1LoginMethods = () => (
		<div className="space-y-[24px]">
			<div>
				<h3 className="text-[20px] font-semibold text-[#111827] mb-[4px]">Choose Login Methods</h3>
				<p className="text-[14px] text-[#6B7280]">Select how users will sign in to your application</p>
			</div>

			{/* Username Types Selection */}
			<div className="space-y-[16px]">
				<div>
					<h4 className="text-[16px] font-medium text-[#111827] mb-[8px]">Allowed Username Types</h4>
					<p className="text-[13px] text-[#6B7280] mb-[16px]">Choose how users can identify themselves when logging in</p>
					
					<div className="grid grid-cols-2 gap-[16px]">
						{/* Email Option */}
						<label className="block">
							<div className={`relative border-2 rounded-[12px] p-[20px] cursor-pointer transition-all ${
								setupData.login_methods.allowed_usernames.includes('email')
									? 'border-[#5048ED] bg-[#F8FAFC]'
									: 'border-[#E5E7EB] hover:border-[#D1D5DB]'
							}`}>
								<div className="flex flex-col items-center text-center gap-[12px]">
									<div className={`w-[48px] h-[48px] rounded-[12px] flex items-center justify-center ${
										setupData.login_methods.allowed_usernames.includes('email')
											? 'bg-[#5048ED] text-white'
											: 'bg-[#F3F4F6] text-[#6B7280]'
									}`}>
										<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
											<path d="M20 4H4C2.9 4 2 4.9 2 6V18C2 19.1 2.9 20 4 20H20C21.1 20 22 19.1 22 18V6C22 4.9 21.1 4 20 4ZM20 8L12 13L4 8V6L12 11L20 6V8Z" fill="currentColor"/>
										</svg>
									</div>
									<div>
										<h5 className="text-[14px] font-medium text-[#111827] mb-[4px]">Email Address</h5>
										<p className="text-[12px] text-[#6B7280]">Users can log in with their email</p>
									</div>
									<input
										type="checkbox"
										checked={setupData.login_methods.allowed_usernames.includes('email')}
										onChange={(e) => {
											const currentTypes = [...setupData.login_methods.allowed_usernames];
											if (e.target.checked) {
												if (!currentTypes.includes('email')) {
													currentTypes.push('email');
												}
											} else {
												const index = currentTypes.indexOf('email');
												if (index > -1 && currentTypes.length > 1) {
													currentTypes.splice(index, 1);
												}
											}
											updateSetupData('login_methods', {
												allowed_usernames: currentTypes
											});
										}}
										className="sr-only"
									/>
									{setupData.login_methods.allowed_usernames.includes('email') && (
										<div className="absolute top-[12px] right-[12px]">
											<svg width="20" height="20" viewBox="0 0 20 20" fill="none" className="text-[#5048ED]">
												<circle cx="10" cy="10" r="10" fill="currentColor"/>
												<path d="M8 10L9.5 11.5L12.5 8.5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
											</svg>
										</div>
									)}
								</div>
							</div>
						</label>

						{/* Phone Option */}
						<label className="block">
							<div className={`relative border-2 rounded-[12px] p-[20px] cursor-pointer transition-all ${
								setupData.login_methods.allowed_usernames.includes('phone')
									? 'border-[#5048ED] bg-[#F8FAFC]'
									: 'border-[#E5E7EB] hover:border-[#D1D5DB]'
							}`}>
								<div className="flex flex-col items-center text-center gap-[12px]">
									<div className={`w-[48px] h-[48px] rounded-[12px] flex items-center justify-center ${
										setupData.login_methods.allowed_usernames.includes('phone')
											? 'bg-[#5048ED] text-white'
											: 'bg-[#F3F4F6] text-[#6B7280]'
									}`}>
										<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
											<path d="M17 2H7C5.9 2 5 2.9 5 4V20C5 21.1 5.9 22 7 22H17C18.1 22 19 21.1 19 20V4C19 2.9 18.1 2 17 2ZM17 18H7V6H17V18Z" fill="currentColor"/>
										</svg>
									</div>
									<div>
										<h5 className="text-[14px] font-medium text-[#111827] mb-[4px]">Phone Number</h5>
										<p className="text-[12px] text-[#6B7280]">Users can log in with their phone</p>
									</div>
									<input
										type="checkbox"
										checked={setupData.login_methods.allowed_usernames.includes('phone')}
										onChange={(e) => {
											const currentTypes = [...setupData.login_methods.allowed_usernames];
											if (e.target.checked) {
												if (!currentTypes.includes('phone')) {
													currentTypes.push('phone');
												}
											} else {
												const index = currentTypes.indexOf('phone');
												if (index > -1 && currentTypes.length > 1) {
													currentTypes.splice(index, 1);
												}
											}
											updateSetupData('login_methods', {
												allowed_usernames: currentTypes
											});
										}}
										className="sr-only"
									/>
									{setupData.login_methods.allowed_usernames.includes('phone') && (
										<div className="absolute top-[12px] right-[12px]">
											<svg width="20" height="20" viewBox="0 0 20 20" fill="none" className="text-[#5048ED]">
												<circle cx="10" cy="10" r="10" fill="currentColor"/>
												<path d="M8 10L9.5 11.5L12.5 8.5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
											</svg>
										</div>
									)}
								</div>
							</div>
						</label>
					</div>
					
					{setupData.login_methods.allowed_usernames.length === 0 && (
						<p className="text-[12px] text-[#EF4444] mt-[8px]">At least one username type must be selected</p>
					)}
				</div>
			</div>

			{/* Login Methods */}
			<div className="space-y-[16px]">
				<h4 className="text-[16px] font-medium text-[#111827] mb-[8px]">Authentication Methods</h4>
				{/* Password Login */}
				<label className="block">
					<div className={`relative border-2 rounded-[12px] p-[20px] cursor-pointer transition-all ${
						setupData.login_methods.password.enabled
							? 'border-[#5048ED] bg-[#F8FAFC]'
							: 'border-[#E5E7EB] hover:border-[#D1D5DB]'
					}`}>
						<div className="flex items-start gap-[16px]">
							<input
								type="checkbox"
								checked={setupData.login_methods.password.enabled}
								onChange={(e) => updateSetupData('login_methods', {
									password: { ...setupData.login_methods.password, enabled: e.target.checked }
								})}
								className="mt-[2px] w-[20px] h-[20px] rounded border-[#D1D5DB] text-[#5048ED] focus:ring-[#5048ED]"
							/>
							<div className="flex-1">
								<h4 className="text-[16px] font-medium text-[#111827] mb-[4px]">Password Authentication</h4>
								<p className="text-[13px] text-[#6B7280] mb-[12px]">Traditional username and password login</p>
								
								{setupData.login_methods.password.enabled && (
									<div className="ml-[4px] space-y-[12px] pt-[12px] border-t border-[#E5E7EB]">
										<label className="flex items-center gap-[8px]">
											<input
												type="checkbox"
												checked={setupData.login_methods.password.forgot_password_enabled}
												onChange={(e) => updateSetupData('login_methods', {
													password: { ...setupData.login_methods.password, forgot_password_enabled: e.target.checked }
												})}
												className="w-[16px] h-[16px] rounded border-[#D1D5DB] text-[#5048ED]"
											/>
											<span className="text-[13px] text-[#111827]">Enable "Forgot Password" feature</span>
										</label>
										
										{setupData.login_methods.password.forgot_password_enabled && (
											<div className="space-y-[12px] pl-[24px]">
												{/* Reset Method */}
												<div>
													<label className="block text-[12px] font-medium text-[#111827] mb-[8px]">
														Reset Method
													</label>
													<div className="flex gap-[12px]">
														<label className="flex items-center gap-[6px]">
															<input
																type="radio"
																name="reset_method"
																value="link"
																checked={setupData.login_methods.password.reset_method === 'link'}
																onChange={(e) => updateSetupData('login_methods', {
																	password: { 
																		...setupData.login_methods.password, 
																		reset_method: e.target.value,
																		// Auto-enable email and disable SMS for link method
																		reset_via_email: true,
																		reset_via_sms: false
																	}
																})}
																className="w-[14px] h-[14px] text-[#5048ED]"
															/>
															<span className="text-[12px] text-[#111827]">Reset Link</span>
														</label>
														<label className="flex items-center gap-[6px]">
															<input
																type="radio"
																name="reset_method"
																value="code"
																checked={setupData.login_methods.password.reset_method === 'code'}
																onChange={(e) => updateSetupData('login_methods', {
																	password: { ...setupData.login_methods.password, reset_method: e.target.value }
																})}
																className="w-[14px] h-[14px] text-[#5048ED]"
															/>
															<span className="text-[12px] text-[#111827]">Reset Code</span>
														</label>
													</div>
												</div>
												
												{/* Expiry Time */}
												<div>
													<label className="block text-[12px] font-medium text-[#111827] mb-[6px]">
														Expiry Time (minutes)
													</label>
													<input
														type="number"
														min="5"
														max="1440"
														value={setupData.login_methods.password.reset_expiry_minutes}
														onChange={(e) => updateSetupData('login_methods', {
															password: { ...setupData.login_methods.password, reset_expiry_minutes: parseInt(e.target.value) || 15 }
														})}
														onClick={(e) => e.stopPropagation()}
														className="w-[100px] px-[10px] py-[6px] border border-[#E5E7EB] rounded-[6px] text-[12px] focus:outline-none focus:ring-2 focus:ring-[#5048ED]"
													/>
												</div>
												
												{/* Reset Delivery Methods */}
												<div>
													<label className="block text-[12px] font-medium text-[#111827] mb-[6px]">
														Send Reset {setupData.login_methods.password.reset_method === 'link' ? 'Link' : 'Code'} Via
													</label>
													<div className="space-y-[8px]">
														{setupData.login_methods.allowed_usernames.includes('email') && (
															<label className="flex items-center gap-[6px]">
																<input
																	type="checkbox"
																	checked={setupData.login_methods.password.reset_via_email}
																	onChange={(e) => updateSetupData('login_methods', {
																		password: { ...setupData.login_methods.password, reset_via_email: e.target.checked }
																	})}
																	disabled={setupData.login_methods.password.reset_method === 'link'} // Disable for link method
																	className="w-[14px] h-[14px] rounded border-[#D1D5DB] text-[#5048ED] disabled:opacity-50"
																/>
																<span className="text-[12px] text-[#111827]">Email</span>
																{setupData.login_methods.password.reset_method === 'link' && (
																	<span className="text-[10px] text-[#6B7280]">(required for links)</span>
																)}
															</label>
														)}
														{/* Only show SMS option for reset code method */}
														{setupData.login_methods.allowed_usernames.includes('phone') && setupData.login_methods.password.reset_method === 'code' && (
															<label className="flex items-center gap-[6px]">
																<input
																	type="checkbox"
																	checked={setupData.login_methods.password.reset_via_sms}
																	onChange={(e) => updateSetupData('login_methods', {
																		password: { ...setupData.login_methods.password, reset_via_sms: e.target.checked }
																	})}
																	className="w-[14px] h-[14px] rounded border-[#D1D5DB] text-[#5048ED]"
																/>
																<span className="text-[12px] text-[#111827]">SMS</span>
															</label>
														)}
													</div>
												</div>
												
												{/* Email Webhook Configuration */}
												{setupData.login_methods.password.reset_via_email && setupData.login_methods.allowed_usernames.includes('email') && (
													<div className="space-y-[6px]">
														<label className="block text-[12px] font-medium text-[#111827]">
															Email Webhook URL
														</label>
														<input
															type="url"
															placeholder="https://api.example.com/send-reset-email"
															value={setupData.login_methods.password.reset_email_webhook}
															onChange={(e) => {
																e.stopPropagation();
																updateSetupData('login_methods', {
																	password: { ...setupData.login_methods.password, reset_email_webhook: e.target.value }
																});
															}}
															onClick={(e) => e.stopPropagation()}
															className="w-full px-[10px] py-[6px] border border-[#E5E7EB] rounded-[6px] text-[12px] focus:outline-none focus:ring-2 focus:ring-[#5048ED]"
														/>
														<label className="block text-[12px] font-medium text-[#111827] mt-[8px]">
															Email Subject
														</label>
														<input
															type="text"
															placeholder="Password Reset Request"
															value={setupData.login_methods.password.reset_email_subject}
															onChange={(e) => {
																e.stopPropagation();
																updateSetupData('login_methods', {
																	password: { ...setupData.login_methods.password, reset_email_subject: e.target.value }
																});
															}}
															onClick={(e) => e.stopPropagation()}
															className="w-full px-[10px] py-[6px] border border-[#E5E7EB] rounded-[6px] text-[12px] focus:outline-none focus:ring-2 focus:ring-[#5048ED]"
														/>
														<label className="block text-[12px] font-medium text-[#111827] mt-[8px]">
															Email Content
														</label>
														<textarea
															placeholder={setupData.login_methods.password.reset_method === 'link' 
																? "Click here to reset your password: {{link}}" 
																: "Your password reset code is: {{code}}"}
															value={setupData.login_methods.password.reset_email_content}
															onChange={(e) => {
																e.stopPropagation();
																updateSetupData('login_methods', {
																	password: { ...setupData.login_methods.password, reset_email_content: e.target.value }
																});
															}}
															onClick={(e) => e.stopPropagation()}
															rows="2"
															className="w-full px-[10px] py-[6px] border border-[#E5E7EB] rounded-[6px] text-[12px] focus:outline-none focus:ring-2 focus:ring-[#5048ED] resize-none"
														/>
														<p className="text-[10px] text-[#6B7280]">
															Use {setupData.login_methods.password.reset_method === 'link' ? '{{link}}' : '{{code}}'} and {'{{expiry}}'} as placeholders
														</p>
													</div>
												)}
												
												{/* SMS Webhook Configuration */}
												{setupData.login_methods.password.reset_via_sms && setupData.login_methods.allowed_usernames.includes('phone') && (
													<div className="space-y-[6px]">
														<label className="block text-[12px] font-medium text-[#111827]">
															SMS Webhook URL
														</label>
														<input
															type="url"
															placeholder="https://api.example.com/send-reset-sms"
															value={setupData.login_methods.password.reset_sms_webhook}
															onChange={(e) => {
																e.stopPropagation();
																updateSetupData('login_methods', {
																	password: { ...setupData.login_methods.password, reset_sms_webhook: e.target.value }
																});
															}}
															onClick={(e) => e.stopPropagation()}
															className="w-full px-[10px] py-[6px] border border-[#E5E7EB] rounded-[6px] text-[12px] focus:outline-none focus:ring-2 focus:ring-[#5048ED]"
														/>
														<label className="block text-[12px] font-medium text-[#111827] mt-[8px]">
															SMS Content
														</label>
														<textarea
															placeholder={setupData.login_methods.password.reset_method === 'link' 
																? "Reset your password: {{link}}" 
																: "Your password reset code is: {{code}}"}
															value={setupData.login_methods.password.reset_sms_content}
															onChange={(e) => {
																e.stopPropagation();
																updateSetupData('login_methods', {
																	password: { ...setupData.login_methods.password, reset_sms_content: e.target.value }
																});
															}}
															onClick={(e) => e.stopPropagation()}
															rows="2"
															className="w-full px-[10px] py-[6px] border border-[#E5E7EB] rounded-[6px] text-[12px] focus:outline-none focus:ring-2 focus:ring-[#5048ED] resize-none"
														/>
														<p className="text-[10px] text-[#6B7280]">
															Use {setupData.login_methods.password.reset_method === 'link' ? '{{link}}' : '{{code}}'} and {'{{expiry}}'} as placeholders
														</p>
													</div>
												)}
											</div>
										)}
									</div>
								)}
							</div>
						</div>
					</div>
				</label>

				{/* OTP */}
				<label className="block">
					<div className={`relative border-2 rounded-[12px] p-[20px] cursor-pointer transition-all ${
						setupData.login_methods.otp.enabled
							? 'border-[#5048ED] bg-[#F8FAFC]'
							: 'border-[#E5E7EB] hover:border-[#D1D5DB]'
					}`}>
						<div className="flex items-start gap-[16px]">
							<input
								type="checkbox"
								checked={setupData.login_methods.otp.enabled}
								onChange={(e) => updateSetupData('login_methods', {
									otp: { ...setupData.login_methods.otp, enabled: e.target.checked }
								})}
								className="mt-[2px] w-[20px] h-[20px] rounded border-[#D1D5DB] text-[#5048ED] focus:ring-[#5048ED]"
							/>
							<div className="flex-1">
								<h4 className="text-[16px] font-medium text-[#111827] mb-[4px]">One-Time Password (OTP)</h4>
								<p className="text-[13px] text-[#6B7280]">SMS or email based verification codes</p>
								
								{setupData.login_methods.otp.enabled && (
									<div className="mt-[16px] space-y-[16px] pt-[16px] border-t border-[#E5E7EB]">
										{/* SMS Webhook - only show if phone is selected */}
										{setupData.login_methods.allowed_usernames.includes('phone') && (
											<div className="space-y-[8px]">
												<label className="block text-[13px] font-medium text-[#111827]">
													SMS Webhook URL
												</label>
												<input
													type="url"
													placeholder="https://api.example.com/send-sms"
													value={setupData.login_methods.otp.sms_webhook}
													onChange={(e) => {
														e.stopPropagation();
														updateSetupData('login_methods', {
															otp: { ...setupData.login_methods.otp, sms_webhook: e.target.value }
														});
													}}
													onClick={(e) => e.stopPropagation()}
													className="w-full px-[12px] py-[8px] border border-[#E5E7EB] rounded-[8px] text-[13px] focus:outline-none focus:ring-2 focus:ring-[#5048ED] focus:border-transparent"
												/>
												<label className="block text-[13px] font-medium text-[#111827] mt-[12px]">
													SMS Content Template
												</label>
												<textarea
													placeholder="Your OTP code is: {{otp}}"
													value={setupData.login_methods.otp.sms_content}
													onChange={(e) => {
														e.stopPropagation();
														updateSetupData('login_methods', {
															otp: { ...setupData.login_methods.otp, sms_content: e.target.value }
														});
													}}
													onClick={(e) => e.stopPropagation()}
													rows="2"
													className="w-full px-[12px] py-[8px] border border-[#E5E7EB] rounded-[8px] text-[13px] focus:outline-none focus:ring-2 focus:ring-[#5048ED] focus:border-transparent resize-none"
												/>
												<p className="text-[11px] text-[#6B7280]">Use {'{{otp}}'} as placeholder for the OTP code</p>
											</div>
										)}
										
										{/* Email Webhook - only show if email is selected */}
										{setupData.login_methods.allowed_usernames.includes('email') && (
											<div className="space-y-[8px]">
												<label className="block text-[13px] font-medium text-[#111827]">
													Email Webhook URL
												</label>
												<input
													type="url"
													placeholder="https://api.example.com/send-email"
													value={setupData.login_methods.otp.email_webhook}
													onChange={(e) => {
														e.stopPropagation();
														updateSetupData('login_methods', {
															otp: { ...setupData.login_methods.otp, email_webhook: e.target.value }
														});
													}}
													onClick={(e) => e.stopPropagation()}
													className="w-full px-[12px] py-[8px] border border-[#E5E7EB] rounded-[8px] text-[13px] focus:outline-none focus:ring-2 focus:ring-[#5048ED] focus:border-transparent"
												/>
												<label className="block text-[13px] font-medium text-[#111827] mt-[12px]">
													Email Subject
												</label>
												<input
													type="text"
													placeholder="Your OTP Verification Code"
													value={setupData.login_methods.otp.email_subject}
													onChange={(e) => {
														e.stopPropagation();
														updateSetupData('login_methods', {
															otp: { ...setupData.login_methods.otp, email_subject: e.target.value }
														});
													}}
													onClick={(e) => e.stopPropagation()}
													className="w-full px-[12px] py-[8px] border border-[#E5E7EB] rounded-[8px] text-[13px] focus:outline-none focus:ring-2 focus:ring-[#5048ED] focus:border-transparent"
												/>
												<label className="block text-[13px] font-medium text-[#111827] mt-[12px]">
													Email Content Template
												</label>
												<textarea
													placeholder="Your OTP code is: {{otp}}"
													value={setupData.login_methods.otp.email_content}
													onChange={(e) => {
														e.stopPropagation();
														updateSetupData('login_methods', {
															otp: { ...setupData.login_methods.otp, email_content: e.target.value }
														});
													}}
													onClick={(e) => e.stopPropagation()}
													rows="3"
													className="w-full px-[12px] py-[8px] border border-[#E5E7EB] rounded-[8px] text-[13px] focus:outline-none focus:ring-2 focus:ring-[#5048ED] focus:border-transparent resize-none"
												/>
												<p className="text-[11px] text-[#6B7280]">Use {'{{otp}}'} as placeholder for the OTP code</p>
											</div>
										)}
									</div>
								)}
							</div>
						</div>
					</div>
				</label>

				{/* SSO
				<label className="block">
					<div className={`relative border-2 rounded-[12px] p-[20px] cursor-pointer transition-all ${
						setupData.login_methods.sso.enabled
							? 'border-[#5048ED] bg-[#F8FAFC]'
							: 'border-[#E5E7EB] hover:border-[#D1D5DB]'
					}`}>
						<div className="flex items-start gap-[16px]">
							<input
								type="checkbox"
								checked={setupData.login_methods.sso.enabled}
								onChange={(e) => updateSetupData('login_methods', {
									sso: { enabled: e.target.checked }
								})}
								className="mt-[2px] w-[20px] h-[20px] rounded border-[#D1D5DB] text-[#5048ED] focus:ring-[#5048ED]"
							/>
							<div className="flex-1">
								<h4 className="text-[16px] font-medium text-[#111827] mb-[4px]">Single Sign-On (SSO)</h4>
								<p className="text-[13px] text-[#6B7280]">Enterprise SSO integration for seamless access</p>
							</div>
						</div>
					</div>
				</label> */}

				{/* OIDC */}
				<label className="block">
					<div className={`relative border-2 rounded-[12px] p-[20px] cursor-pointer transition-all ${
						setupData.login_methods.oidc.enabled
							? 'border-[#5048ED] bg-[#F8FAFC]'
							: 'border-[#E5E7EB] hover:border-[#D1D5DB]'
					}`}>
						<div className="flex items-start gap-[16px]">
							<input
								type="checkbox"
								checked={setupData.login_methods.oidc.enabled}
								onChange={(e) => updateSetupData('login_methods', {
									oidc: { enabled: e.target.checked }
								})}
								className="mt-[2px] w-[20px] h-[20px] rounded border-[#D1D5DB] text-[#5048ED] focus:ring-[#5048ED]"
							/>
							<div className="flex-1">
								<h4 className="text-[16px] font-medium text-[#111827] mb-[4px]">OpenID Connect (OIDC)</h4>
								<p className="text-[13px] text-[#6B7280]">OAuth 2.0 based authentication</p>
							</div>
						</div>
					</div>
				</label>

				
			</div>
		</div>
	);

	// Step 2: Password Policy (only if password is enabled)
	const Step2PasswordPolicy = () => (
		<div className="space-y-[24px]">
			<div>
				<h3 className="text-[20px] font-semibold text-[#111827] mb-[4px]">Password Policy</h3>
				<p className="text-[14px] text-[#6B7280]">Configure password requirements for your users</p>
			</div>

			<div className="space-y-[20px]">
				{/* Minimum Length */}
				<div>
					<label className="block text-[14px] font-medium text-[#111827] mb-[8px]">
						Minimum Password Length
					</label>
					<input
						type="number"
						min="4"
						max="128"
						value={setupData.password_policy.min_length}
						onChange={(e) => updateSetupData('password_policy', {
							min_length: parseInt(e.target.value) || 8
						})}
						className="w-[120px] px-[12px] py-[8px] border border-[#E5E7EB] rounded-[8px] text-[14px] focus:outline-none focus:ring-2 focus:ring-[#5048ED] focus:border-transparent"
					/>
				</div>

				{/* Requirements */}
				<div>
					<label className="block text-[14px] font-medium text-[#111827] mb-[12px]">
						Password Requirements
					</label>
					<div className="space-y-[12px]">
						<label className="flex items-center gap-[12px]">
							<input
								type="checkbox"
								checked={setupData.password_policy.require_uppercase}
								onChange={(e) => updateSetupData('password_policy', {
									require_uppercase: e.target.checked
								})}
								className="w-[18px] h-[18px] rounded border-[#D1D5DB] text-[#5048ED]"
							/>
							<span className="text-[14px] text-[#111827]">Require uppercase letters (A-Z)</span>
						</label>
						<label className="flex items-center gap-[12px]">
							<input
								type="checkbox"
								checked={setupData.password_policy.require_lowercase}
								onChange={(e) => updateSetupData('password_policy', {
									require_lowercase: e.target.checked
								})}
								className="w-[18px] h-[18px] rounded border-[#D1D5DB] text-[#5048ED]"
							/>
							<span className="text-[14px] text-[#111827]">Require lowercase letters (a-z)</span>
						</label>
						<label className="flex items-center gap-[12px]">
							<input
								type="checkbox"
								checked={setupData.password_policy.require_numbers}
								onChange={(e) => updateSetupData('password_policy', {
									require_numbers: e.target.checked
								})}
								className="w-[18px] h-[18px] rounded border-[#D1D5DB] text-[#5048ED]"
							/>
							<span className="text-[14px] text-[#111827]">Require numbers (0-9)</span>
						</label>
						<label className="flex items-center gap-[12px]">
							<input
								type="checkbox"
								checked={setupData.password_policy.require_special_chars}
								onChange={(e) => updateSetupData('password_policy', {
									require_special_chars: e.target.checked
								})}
								className="w-[18px] h-[18px] rounded border-[#D1D5DB] text-[#5048ED]"
							/>
							<span className="text-[14px] text-[#111827]">Require special characters (!@#$%^&*)</span>
						</label>
					</div>
				</div>

				{/* Expiry */}
				<div>
					<label className="block text-[14px] font-medium text-[#111827] mb-[8px]">
						Password Expiry (days)
					</label>
					<input
						type="number"
						min="1"
						max="365"
						value={setupData.password_policy.password_expiry_days}
						onChange={(e) => updateSetupData('password_policy', {
							password_expiry_days: parseInt(e.target.value) || 90
						})}
						className="w-[120px] px-[12px] py-[8px] border border-[#E5E7EB] rounded-[8px] text-[14px] focus:outline-none focus:ring-2 focus:ring-[#5048ED] focus:border-transparent"
					/>
				</div>
			</div>
		</div>
	);

	// Step 3: Two-Factor Authentication
	const Step3TwoFactor = () => (
		<div className="space-y-[24px]">
			<div>
				<h3 className="text-[20px] font-semibold text-[#111827] mb-[4px]">Two-Factor Authentication</h3>
				<p className="text-[14px] text-[#6B7280]">Add an extra layer of security for user accounts</p>
			</div>

			<div className="space-y-[20px]">
				<label className="flex items-center gap-[12px]">
					<input
						type="checkbox"
						checked={setupData.two_factor_auth.required}
						onChange={(e) => updateSetupData('two_factor_auth', {
							required: e.target.checked
						})}
						className="w-[20px] h-[20px] rounded border-[#D1D5DB] text-[#5048ED]"
					/>
					<div>
						<span className="text-[16px] font-medium text-[#111827]">Require 2FA for all users</span>
						<p className="text-[13px] text-[#6B7280] mt-[2px]">Users must set up two-factor authentication to access the application</p>
					</div>
				</label>

				{setupData.two_factor_auth.required && (
					<div className="ml-[32px] space-y-[16px] pt-[16px] border-t border-[#E5E7EB]">
						<p className="text-[14px] font-medium text-[#111827]">Available 2FA Methods</p>
						<div className="space-y-[12px]">
							<label className="flex items-center gap-[12px]">
								<input
									type="checkbox"
									checked={setupData.two_factor_auth.allowedMethods.includes('email')}
									onChange={(e) => {
										const methods = e.target.checked
											? [...setupData.two_factor_auth.allowedMethods, 'email']
											: setupData.two_factor_auth.allowedMethods.filter(m => m !== 'email');
										updateSetupData('two_factor_auth', { allowedMethods: methods });
									}}
									className="w-[18px] h-[18px] rounded border-[#D1D5DB] text-[#5048ED]"
								/>
								<span className="text-[14px] text-[#111827]">Email verification</span>
							</label>
							<label className="flex items-center gap-[12px]">
								<input
									type="checkbox"
									checked={setupData.two_factor_auth.allowedMethods.includes('sms')}
									onChange={(e) => {
										const methods = e.target.checked
											? [...setupData.two_factor_auth.allowedMethods, 'sms']
											: setupData.two_factor_auth.allowedMethods.filter(m => m !== 'sms');
										updateSetupData('two_factor_auth', { allowedMethods: methods });
									}}
									className="w-[18px] h-[18px] rounded border-[#D1D5DB] text-[#5048ED]"
								/>
								<span className="text-[14px] text-[#111827]">SMS verification</span>
							</label>
						</div>
					</div>
				)}
			</div>
		</div>
	);

	// Step 4: Role Overrides
	const Step4RoleOverrides = () => (
		<div className="space-y-[24px]">
			<div>
				<h3 className="text-[20px] font-semibold text-[#111827] mb-[4px]">User Role Overrides</h3>
				<p className="text-[14px] text-[#6B7280]">Define stricter password and 2FA policies for specific user roles</p>
				<div className="mt-[8px] p-[12px] bg-[#FEF3C7] rounded-[8px] flex gap-[8px]">
					<svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[#D97706] flex-shrink-0 mt-[2px]">
						<path d="M8 4V8M8 12H8.01M14 8C14 11.3137 11.3137 14 8 14C4.68629 14 2 11.3137 2 8C2 4.68629 4.68629 2 8 2C11.3137 2 14 4.68629 14 8Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
					</svg>
					<p className="text-[12px] text-[#92400E]">
						Role overrides can only enforce stricter policies than the global settings. You cannot relax security requirements for specific roles.
					</p>
				</div>
			</div>

			{roles && roles.length > 0 ? (
				<div className="space-y-[16px]">
					{roles.map((role) => {
						const roleOverride = setupData.role_overrides[role.id] || {};
						const hasOverride = !!setupData.role_overrides[role.id];
						
						return (
							<div key={role.id} className="border-2 border-[#E5E7EB] rounded-[12px] overflow-hidden">
								<div className="p-[20px] bg-[#F9FAFB]">
									<div className="flex items-center justify-between">
										<div className="flex items-center gap-[12px]">
											<div className={`w-[40px] h-[40px] rounded-[8px] flex items-center justify-center ${
												hasOverride ? 'bg-[#5048ED] text-white' : 'bg-[#E5E7EB] text-[#6B7280]'
											}`}>
												<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
													<path d="M10 10C12.2091 10 14 8.20914 14 6C14 3.79086 12.2091 2 10 2C7.79086 2 6 3.79086 6 6C6 8.20914 7.79086 10 10 10Z" stroke="currentColor" strokeWidth="2"/>
													<path d="M2 18C2 14.6863 4.68629 12 8 12H12C15.3137 12 18 14.6863 18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
												</svg>
											</div>
											<div>
												<h4 className="text-[16px] font-medium text-[#111827]">{role.name}</h4>
												<p className="text-[12px] text-[#6B7280]">
													{hasOverride ? 'Custom policies applied' : 'Using default policies'}
												</p>
											</div>
										</div>
										<label className="flex items-center gap-[8px]">
											<input
												type="checkbox"
												checked={hasOverride}
												onChange={(e) => {
													if (e.target.checked) {
														// Initialize with current global settings
														updateSetupData('role_overrides', {
															[role.id]: {
																password_policy: { ...setupData.password_policy },
																two_factor_auth: { ...setupData.two_factor_auth }
															}
														});
													} else {
														// Remove override
														const newOverrides = { ...setupData.role_overrides };
														delete newOverrides[role.id];
														setSetupData(prev => ({
															...prev,
															role_overrides: newOverrides
														}));
													}
												}}
												className="w-[20px] h-[20px] rounded border-[#D1D5DB] text-[#5048ED]"
											/>
											<span className="text-[14px] font-medium text-[#111827]">Enable Overrides</span>
										</label>
									</div>
								</div>
								
								{hasOverride && (
									<div className="p-[20px] space-y-[20px] border-t border-[#E5E7EB]">
										{/* Password Policy Override */}
										<div>
											<h5 className="text-[14px] font-medium text-[#111827] mb-[12px] flex items-center gap-[6px]">
												<svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[#5048ED]">
													<path d="M12 7V5C12 2.79086 10.2091 1 8 1C5.79086 1 4 2.79086 4 5V7M3 7H13C13.5523 7 14 7.44772 14 8V14C14 14.5523 13.5523 15 13 15H3C2.44772 15 2 14.5523 2 14V8C2 7.44772 2.44772 7 3 7Z" stroke="currentColor" strokeWidth="1.5"/>
												</svg>
												Password Policy
											</h5>
											<div className="grid grid-cols-2 gap-[12px]">
												<div>
													<label className="block text-[12px] text-[#6B7280] mb-[4px]">Min Length</label>
													<input
														type="number"
														min={setupData.password_policy.min_length}
														max="128"
														value={roleOverride.password_policy?.min_length || setupData.password_policy.min_length}
														onChange={(e) => {
															const newValue = parseInt(e.target.value) || setupData.password_policy.min_length;
															// Ensure it's not less than global setting
															if (newValue >= setupData.password_policy.min_length) {
																updateSetupData('role_overrides', {
																	[role.id]: {
																		...roleOverride,
																		password_policy: {
																			...roleOverride.password_policy,
																			min_length: newValue
																		}
																	}
																});
															}
														}}
														className="w-full px-[10px] py-[6px] border border-[#E5E7EB] rounded-[6px] text-[12px]"
													/>
												</div>
												<div>
													<label className="block text-[12px] text-[#6B7280] mb-[4px]">Expiry (days)</label>
													<input
														type="number"
														min="0"
														max={setupData.password_policy.password_expiry_days || 365}
														value={roleOverride.password_policy?.password_expiry_days || setupData.password_policy.password_expiry_days}
														onChange={(e) => {
															const newValue = parseInt(e.target.value) || 0;
															// Ensure it's not greater than global setting (shorter expiry is stricter)
															if (newValue <= setupData.password_policy.password_expiry_days) {
																updateSetupData('role_overrides', {
																	[role.id]: {
																		...roleOverride,
																		password_policy: {
																			...roleOverride.password_policy,
																			password_expiry_days: newValue
																		}
																	}
																});
															}
														}}
														className="w-full px-[10px] py-[6px] border border-[#E5E7EB] rounded-[6px] text-[12px]"
													/>
												</div>
											</div>
											<div className="mt-[8px] space-y-[6px]">
												<label className="flex items-center gap-[6px]">
													<input
														type="checkbox"
														checked={roleOverride.password_policy?.require_uppercase ?? setupData.password_policy.require_uppercase}
														disabled={setupData.password_policy.require_uppercase} // Can't disable if globally required
														onChange={(e) => {
															// Only allow enabling, not disabling if globally enabled
															if (!setupData.password_policy.require_uppercase || e.target.checked) {
																updateSetupData('role_overrides', {
																	[role.id]: {
																		...roleOverride,
																		password_policy: {
																			...roleOverride.password_policy,
																			require_uppercase: e.target.checked
																		}
																	}
																});
															}
														}}
														className="w-[14px] h-[14px] rounded border-[#D1D5DB] text-[#5048ED] disabled:opacity-50"
													/>
													<span className="text-[12px] text-[#111827]">Require uppercase</span>
													{setupData.password_policy.require_uppercase && (
														<span className="text-[10px] text-[#6B7280]">(globally required)</span>
													)}
												</label>
												<label className="flex items-center gap-[6px]">
													<input
														type="checkbox"
														checked={roleOverride.password_policy?.require_lowercase ?? setupData.password_policy.require_lowercase}
														disabled={setupData.password_policy.require_lowercase}
														onChange={(e) => {
															if (!setupData.password_policy.require_lowercase || e.target.checked) {
																updateSetupData('role_overrides', {
																	[role.id]: {
																		...roleOverride,
																		password_policy: {
																			...roleOverride.password_policy,
																			require_lowercase: e.target.checked
																		}
																	}
																});
															}
														}}
														className="w-[14px] h-[14px] rounded border-[#D1D5DB] text-[#5048ED] disabled:opacity-50"
													/>
													<span className="text-[12px] text-[#111827]">Require lowercase</span>
													{setupData.password_policy.require_lowercase && (
														<span className="text-[10px] text-[#6B7280]">(globally required)</span>
													)}
												</label>
												<label className="flex items-center gap-[6px]">
													<input
														type="checkbox"
														checked={roleOverride.password_policy?.require_numbers ?? setupData.password_policy.require_numbers}
														disabled={setupData.password_policy.require_numbers}
														onChange={(e) => {
															if (!setupData.password_policy.require_numbers || e.target.checked) {
																updateSetupData('role_overrides', {
																	[role.id]: {
																		...roleOverride,
																		password_policy: {
																			...roleOverride.password_policy,
																			require_numbers: e.target.checked
																		}
																	}
																});
															}
														}}
														className="w-[14px] h-[14px] rounded border-[#D1D5DB] text-[#5048ED] disabled:opacity-50"
													/>
													<span className="text-[12px] text-[#111827]">Require numbers</span>
													{setupData.password_policy.require_numbers && (
														<span className="text-[10px] text-[#6B7280]">(globally required)</span>
													)}
												</label>
												<label className="flex items-center gap-[6px]">
													<input
														type="checkbox"
														checked={roleOverride.password_policy?.require_special_chars ?? setupData.password_policy.require_special_chars}
														disabled={setupData.password_policy.require_special_chars}
														onChange={(e) => {
															if (!setupData.password_policy.require_special_chars || e.target.checked) {
																updateSetupData('role_overrides', {
																	[role.id]: {
																		...roleOverride,
																		password_policy: {
																			...roleOverride.password_policy,
																			require_special_chars: e.target.checked
																		}
																	}
																});
															}
														}}
														className="w-[14px] h-[14px] rounded border-[#D1D5DB] text-[#5048ED] disabled:opacity-50"
													/>
													<span className="text-[12px] text-[#111827]">Require special characters</span>
													{setupData.password_policy.require_special_chars && (
														<span className="text-[10px] text-[#6B7280]">(globally required)</span>
													)}
												</label>
											</div>
										</div>
										
										{/* 2FA Override */}
										<div>
											<h5 className="text-[14px] font-medium text-[#111827] mb-[12px] flex items-center gap-[6px]">
												<svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[#5048ED]">
													<path d="M8 1L10 3H14V7L12 9L14 11V15H10L8 13L6 15H2V11L4 9L2 7V3H6L8 1Z" stroke="currentColor" strokeWidth="1.5"/>
													<circle cx="8" cy="8" r="2" stroke="currentColor" strokeWidth="1.5"/>
												</svg>
												Two-Factor Authentication
											</h5>
											<label className="flex items-center gap-[8px]">
												<input
													type="checkbox"
													checked={roleOverride.two_factor_auth?.required ?? setupData.two_factor_auth.required}
													disabled={setupData.two_factor_auth.required} // Can't disable if globally required
													onChange={(e) => {
														// Only allow enabling 2FA, not disabling if globally enabled
														if (!setupData.two_factor_auth.required || e.target.checked) {
															updateSetupData('role_overrides', {
																[role.id]: {
																	...roleOverride,
																	two_factor_auth: {
																		...roleOverride.two_factor_auth,
																		required: e.target.checked
																	}
																}
															});
														}
													}}
													className="w-[16px] h-[16px] rounded border-[#D1D5DB] text-[#5048ED] disabled:opacity-50"
												/>
												<span className="text-[13px] text-[#111827]">Require 2FA for this role</span>
												{setupData.two_factor_auth.required && (
													<span className="text-[10px] text-[#6B7280] ml-[4px]">(globally required)</span>
												)}
											</label>
										</div>
									</div>
								)}
							</div>
						);
					})}
				</div>
			) : (
				<div className="bg-[#F9FAFB] rounded-[12px] p-[32px] text-center">
					<p className="text-[14px] text-[#6B7280]">No user roles available for overrides</p>
				</div>
			)}
		</div>
	);

	// Step 5: Review
	const Step5Review = () => (
		<div className="space-y-[24px]">
			<div>
				<h3 className="text-[20px] font-semibold text-[#111827] mb-[4px]">Review Configuration</h3>
				<p className="text-[14px] text-[#6B7280]">Review your authentication settings before saving</p>
			</div>

			<div className="space-y-[20px]">
				{/* Username Types */}
				<div className="bg-[#F8FAFC] rounded-[12px] p-[20px]">
					<h4 className="text-[16px] font-medium text-[#111827] mb-[12px]">Allowed Username Types</h4>
					<div className="flex gap-[12px]">
						{setupData.login_methods.allowed_usernames.map((type) => (
							<span key={type} className="px-[12px] py-[6px] bg-[#5048ED] text-white rounded-[8px] text-[14px] font-medium">
								{type.charAt(0).toUpperCase() + type.slice(1)}
							</span>
						))}
					</div>
				</div>

				{/* Login Methods */}
				<div className="bg-[#F8FAFC] rounded-[12px] p-[20px]">
					<h4 className="text-[16px] font-medium text-[#111827] mb-[12px]">Authentication Methods</h4>
					<div className="space-y-[8px]">
						{setupData.login_methods.password.enabled && (
							<div className="flex items-center gap-[8px] text-[14px] text-[#111827]">
								<svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[#10B981]">
									<path d="M13.5 4.5L6 12L2.5 8.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
								</svg>
								Password Authentication
								{setupData.login_methods.password.forgot_password_enabled && " (with forgot password)"}
							</div>
						)}
						{setupData.login_methods.sso.enabled && (
							<div className="flex items-center gap-[8px] text-[14px] text-[#111827]">
								<svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[#10B981]">
									<path d="M13.5 4.5L6 12L2.5 8.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
								</svg>
								Single Sign-On (SSO)
							</div>
						)}
						{setupData.login_methods.oidc.enabled && (
							<div className="flex items-center gap-[8px] text-[14px] text-[#111827]">
								<svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[#10B981]">
									<path d="M13.5 4.5L6 12L2.5 8.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
								</svg>
								OpenID Connect (OIDC)
							</div>
						)}
						{setupData.login_methods.otp.enabled && (
							<div className="flex items-center gap-[8px] text-[14px] text-[#111827]">
								<svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[#10B981]">
									<path d="M13.5 4.5L6 12L2.5 8.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
								</svg>
								One-Time Password (OTP)
							</div>
						)}
					</div>
				</div>

				{/* Password Policy (if enabled) */}
				{setupData.login_methods.password.enabled && (
					<div className="bg-[#F8FAFC] rounded-[12px] p-[20px]">
						<h4 className="text-[16px] font-medium text-[#111827] mb-[12px]">Password Policy</h4>
						<div className="space-y-[8px] text-[14px] text-[#111827]">
							<div>Minimum length: {setupData.password_policy.min_length} characters</div>
							<div>Expires every: {setupData.password_policy.password_expiry_days} days</div>
							<div className="flex items-center gap-[8px]">
								Requirements:
								{setupData.password_policy.require_uppercase && <span className="text-[#10B981]">Uppercase</span>}
								{setupData.password_policy.require_lowercase && <span className="text-[#10B981]">Lowercase</span>}
								{setupData.password_policy.require_numbers && <span className="text-[#10B981]">Numbers</span>}
								{setupData.password_policy.require_special_chars && <span className="text-[#10B981]">Special chars</span>}
							</div>
						</div>
					</div>
				)}

				{/* 2FA */}
				<div className="bg-[#F8FAFC] rounded-[12px] p-[20px]">
					<h4 className="text-[16px] font-medium text-[#111827] mb-[12px]">Two-Factor Authentication</h4>
					<div className="text-[14px] text-[#111827]">
						{setupData.two_factor_auth.required ? (
							<span className="text-[#10B981] font-medium">Required for all users</span>
						) : (
							<span className="text-[#6B7280]">Not required</span>
						)}
					</div>
				</div>

				{/* Role Overrides */}
				{Object.keys(setupData.role_overrides).length > 0 && (
					<div className="bg-[#F8FAFC] rounded-[12px] p-[20px]">
						<h4 className="text-[16px] font-medium text-[#111827] mb-[12px]">Role Overrides</h4>
						<div className="space-y-[8px]">
							{Object.entries(setupData.role_overrides).map(([roleId, override]) => {
								const role = roles?.find(r => r.id === parseInt(roleId));
								if (!role) return null;
								
								return (
									<div key={roleId} className="flex items-center justify-between text-[14px]">
										<span className="font-medium text-[#111827]">{role.name}</span>
										<div className="flex gap-[8px]">
											{override.password_policy && (
												<span className="px-[8px] py-[2px] bg-[#EFF6FF] text-[#5048ED] rounded-[4px] text-[11px] font-medium">
													Custom Password Policy
												</span>
											)}
											{override.two_factor_auth?.required && (
												<span className="px-[8px] py-[2px] bg-[#D1FAE5] text-[#065F46] rounded-[4px] text-[11px] font-medium">
													2FA Required
												</span>
											)}
										</div>
									</div>
								);
							})}
						</div>
					</div>
				)}
			</div>
		</div>
	);

	// Render current step
	const renderStep = () => {
		switch (currentStep) {
			case 1:
				return <Step1LoginMethods />;
			case 2:
				// Skip to step 3 if password is not enabled
				if (!setupData.login_methods.password.enabled && currentStep === 2) {
					setCurrentStep(3);
					return null;
				}
				return <Step2PasswordPolicy />;
			case 3:
				return <Step3TwoFactor />;
			case 4:
				return <Step4RoleOverrides />;
			case 5:
				return <Step5Review />;
			default:
				return null;
		}
	};

	// Check if current step can proceed
	const canProceed = () => {
		if (currentStep === 1) {
			// At least one username type must be selected
			if (setupData.login_methods.allowed_usernames.length === 0) {
				return false;
			}
			// At least one login method must be selected
			return setupData.login_methods.password.enabled ||
				setupData.login_methods.sso.enabled ||
				setupData.login_methods.oidc.enabled ||
				setupData.login_methods.otp.enabled;
		}
		return true;
	};

	return (
		<Transition appear show={show} as={Fragment}>
			<Dialog as="div" className="relative z-50" onClose={onClose}>
				<Transition.Child
					as={Fragment}
					enter="ease-out duration-300"
					enterFrom="opacity-0"
					enterTo="opacity-100"
					leave="ease-in duration-200"
					leaveFrom="opacity-100"
					leaveTo="opacity-0"
				>
					<div className="fixed inset-0 bg-black bg-opacity-25" />
				</Transition.Child>

				<div className="fixed inset-0 overflow-y-auto">
					<div className="flex min-h-full items-center justify-center p-4 text-center">
						<Transition.Child
							as={Fragment}
							enter="ease-out duration-300"
							enterFrom="opacity-0 scale-95"
							enterTo="opacity-100 scale-100"
							leave="ease-in duration-200"
							leaveFrom="opacity-100 scale-100"
							leaveTo="opacity-0 scale-95"
						>
							<Dialog.Panel className="w-full max-w-[720px] transform overflow-hidden rounded-[20px] bg-white p-[32px] text-left align-middle shadow-xl transition-all">
								{/* Close Button */}
								<button
									onClick={onClose}
									className="absolute top-[24px] right-[24px] text-[#6B7280] hover:text-[#111827] transition-colors"
								>
									<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
										<path d="M18 6L6 18M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
									</svg>
								</button>

								{/* Step Indicator */}
								<StepIndicator />

								{/* Content */}
								<div className="min-h-[400px]">
									{renderStep()}
								</div>

								{/* Footer */}
								<div className="flex items-center justify-between mt-[40px] pt-[24px] border-t border-[#E5E7EB]">
									<button
										onClick={handleBack}
										disabled={currentStep === 1}
										className={`px-[20px] py-[10px] rounded-[8px] font-medium text-[14px] transition-all ${
											currentStep === 1
												? 'text-[#9CA3AF] cursor-not-allowed'
												: 'text-[#6B7280] hover:bg-[#F3F4F6]'
										}`}
									>
										Back
									</button>

									<button
										onClick={handleNext}
										disabled={!canProceed()}
										className={`px-[24px] py-[10px] rounded-[8px] font-medium text-[14px] transition-all ${
											canProceed()
												? 'bg-[#5048ED] text-white hover:bg-[#4338CA]'
												: 'bg-[#E5E7EB] text-[#9CA3AF] cursor-not-allowed'
										}`}
									>
										{currentStep === totalSteps ? 'Complete Setup' : 'Next'}
									</button>
								</div>
							</Dialog.Panel>
						</Transition.Child>
					</div>
				</div>
			</Dialog>
		</Transition>
	);
};

export default AuthSetupModal;