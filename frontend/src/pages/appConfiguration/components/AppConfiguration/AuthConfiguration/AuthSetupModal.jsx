import React, { useState, useMemo } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';

const AuthSetupModal = ({ show, onClose, onComplete, initialData = null, roles = [] }) => {
	const [currentStep, setCurrentStep] = useState(1);
	const totalSteps = 4;

	// JSON Key-Value Pair Input Component
	const JsonKeyValueInput = ({ value, onChange, placeholder = "Add key-value pairs" }) => {
		const [pairs, setPairs] = useState(() => {
			try {
				const parsed = typeof value === 'string' ? JSON.parse(value || '{}') : (value || {});
				return Object.entries(parsed).map(([key, val]) => ({ key, value: val }));
			} catch {
				return [];
			}
		});

		const updateParent = (newPairs) => {
			const obj = {};
			newPairs.forEach(pair => {
				if (pair.key.trim()) {
					obj[pair.key.trim()] = pair.value;
				}
			});
			onChange(JSON.stringify(obj));
		};

		const addPair = () => {
			const newPairs = [...pairs, { key: '', value: '' }];
			setPairs(newPairs);
		};

		const removePair = (index) => {
			const newPairs = pairs.filter((_, i) => i !== index);
			setPairs(newPairs);
			updateParent(newPairs);
		};

		const updatePair = (index, field, val) => {
			const newPairs = pairs.map((pair, i) =>
				i === index ? { ...pair, [field]: val } : pair
			);
			setPairs(newPairs);
			updateParent(newPairs);
		};

		return (
			<div className="space-y-[8px]">
				{pairs.map((pair, index) => (
					<div key={index} className="flex gap-[8px] items-center">
						<input
							type="text"
							placeholder="Key"
							value={pair.key}
							onChange={(e) => {
								e.stopPropagation();
								updatePair(index, 'key', e.target.value);
							}}
							onClick={(e) => e.stopPropagation()}
							className="flex-1 px-[10px] py-[6px] border border-[#E5E7EB] rounded-[6px] text-[12px] focus:outline-none focus:ring-2 focus:ring-[#5048ED]"
						/>
						<input
							type="text"
							placeholder="Value"
							value={pair.value}
							onChange={(e) => {
								e.stopPropagation();
								updatePair(index, 'value', e.target.value);
							}}
							onClick={(e) => e.stopPropagation()}
							className="flex-1 px-[10px] py-[6px] border border-[#E5E7EB] rounded-[6px] text-[12px] focus:outline-none focus:ring-2 focus:ring-[#5048ED]"
						/>
						<button
							type="button"
							onClick={(e) => {
								e.stopPropagation();
								removePair(index);
							}}
							className="p-[6px] text-[#EF4444] hover:bg-[#FEF2F2] rounded-[6px] transition-colors"
						>
							<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
								<path d="M12 4L4 12M4 4L12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
							</svg>
						</button>
					</div>
				))}
				<button
					type="button"
					onClick={(e) => {
						e.stopPropagation();
						addPair();
					}}
					className="flex items-center gap-[6px] px-[12px] py-[6px] text-[12px] text-[#5048ED] hover:bg-[#F8FAFC] rounded-[6px] transition-colors"
				>
					<svg width="14" height="14" viewBox="0 0 14 14" fill="none">
						<path d="M7 1V13M1 7H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
					</svg>
					Add {pairs.length > 0 ? 'Another' : ''} Key-Value Pair
				</button>
			</div>
		);
	};

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
				reset_sms_config_key: '',
				reset_email_config_key: '',
				reset_sms_extra_data: '{}',
				allowed_usernames: ['email', 'phone'],
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
				sms_config_key: '',
				email_config_key: '',
				sms_extra_data: '{}',
				allowed_methods: ['email', 'sms'],
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
			reset: {
				expiry: 7200, // 2 hours in seconds
				enabled: true,
				allowed_methods: ['email'],
			},
		},
		two_factor_auth: {
			required: false,
			allowedMethods: ['email'],
			email_hook: '',
			sms_hook: '',
		},
		session_policy: {
			max_concurrent_sessions: 0,
			force_logout_on_password_change: false,
		},
	};

	// Use initial data if provided (editing mode), otherwise use defaults
	const getInitialData = () => {
		if (!initialData) return defaultSetupData;
		
		return {
			login_methods: {
				allowed_usernames: initialData.login_methods?.password?.allowed_usernames || initialData.login_methods?.allowed_usernames || ['email'],
				password: {
					enabled: initialData.login_methods?.password?.enabled || false,
					forgot_password_enabled: initialData.login_methods?.password?.forgot_password_enabled || false,
					reset_method: initialData.password_policy?.reset?.by_code ? 'code' : 'link',
					reset_expiry_minutes: initialData.password_policy?.reset?.expiry ? Math.floor(initialData.password_policy.reset.expiry / 60) : 15,
					reset_via_sms: initialData.password_policy?.reset?.allowed_methods?.includes('sms') || false,
					reset_via_email: initialData.password_policy?.reset?.allowed_methods?.includes('email') || true,
					reset_sms_webhook: initialData.password_policy?.reset?.sms_hook || '',
					reset_email_webhook: initialData.password_policy?.reset?.email_hook || '',
					reset_sms_content: initialData.password_policy?.reset?.sms_template_id || defaultSetupData.login_methods.password.reset_sms_content,
					reset_email_subject: initialData.password_policy?.reset?.email_subject || defaultSetupData.login_methods.password.reset_email_subject,
					reset_email_content: initialData.password_policy?.reset?.email_content || defaultSetupData.login_methods.password.reset_email_content,
					reset_sms_config_key: initialData.password_policy?.reset?.sms_config_key || '',
					reset_email_config_key: initialData.password_policy?.reset?.email_config_key || '',
					reset_sms_extra_data: initialData.password_policy?.reset?.sms_extra_data || '{}',
				},
				sso: { enabled: initialData.login_methods?.sso?.enabled || false },
				oidc: { enabled: initialData.login_methods?.oidc?.enabled || false },
				otp: {
					enabled: initialData.login_methods?.otp?.enabled || false,
					allowed_methods: initialData.login_methods?.otp?.allowed_methods || ['email', 'sms'],
					sms_webhook: initialData.login_methods?.otp?.sms_hook || initialData.login_methods?.otp?.sms_webhook || '',
					email_webhook: initialData.login_methods?.otp?.email_hook || initialData.login_methods?.otp?.email_webhook || '',
					sms_content: initialData.login_methods?.otp?.sms_template_id || initialData.login_methods?.otp?.sms_content || defaultSetupData.login_methods.otp.sms_content,
					email_subject: initialData.login_methods?.otp?.email_subject || defaultSetupData.login_methods.otp.email_subject,
					email_content: initialData.login_methods?.otp?.email_content || defaultSetupData.login_methods.otp.email_content,
					sms_config_key: initialData.login_methods?.otp?.sms_config_key || '',
					email_config_key: initialData.login_methods?.otp?.email_config_key || '',
					sms_extra_data: initialData.login_methods?.otp?.sms_extra_data || '{}',
				},
			},
			password_policy: initialData.password_policy || defaultSetupData.password_policy,
			two_factor_auth: {
				required: initialData.two_factor_auth?.required || false,
				allowedMethods: initialData.two_factor_auth?.allowedMethods || initialData.two_factor_auth?.allowed_methods || ['email'],
				email_hook: initialData.two_factor_auth?.email_hook || '',
				sms_hook: initialData.two_factor_auth?.sms_hook || '',
			},
			session_policy: initialData.session_policy || defaultSetupData.session_policy,
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
			{[1, 2, 3, 4].map((step) => (
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
					{step < 4 && (
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
															Email Config Key (Optional)
														</label>
														<input
															type="text"
															placeholder="e.g., sendgrid_config"
															value={setupData.login_methods.password.reset_email_config_key}
															onChange={(e) => {
																e.stopPropagation();
																updateSetupData('login_methods', {
																	password: { ...setupData.login_methods.password, reset_email_config_key: e.target.value }
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
															SMS Config Key (Optional)
														</label>
														<input
															type="text"
															placeholder="e.g., twilio_config"
															value={setupData.login_methods.password.reset_sms_config_key}
															onChange={(e) => {
																e.stopPropagation();
																updateSetupData('login_methods', {
																	password: { ...setupData.login_methods.password, reset_sms_config_key: e.target.value }
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
														<label className="block text-[12px] font-medium text-[#111827] mt-[8px]">
															SMS Extra Data (JSON)
														</label>
														<JsonKeyValueInput
															value={setupData.login_methods.password.reset_sms_extra_data}
															onChange={(value) => {
																updateSetupData('login_methods', {
																	password: { ...setupData.login_methods.password, reset_sms_extra_data: value }
																});
															}}
														/>
														<p className="text-[10px] text-[#6B7280]">Additional data to send with SMS webhook</p>
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
										{/* Allowed OTP Methods Selection */}
										<div>
											<label className="block text-[13px] font-medium text-[#111827] mb-[8px]">
												Allowed OTP Delivery Methods
											</label>
											<p className="text-[11px] text-[#6B7280] mb-[12px]">Select how OTP codes should be delivered to users</p>
											<div className="space-y-[8px]">
												{setupData.login_methods.allowed_usernames.includes('email') && (
													<label className="flex items-center gap-[8px]">
														<input
															type="checkbox"
															checked={setupData.login_methods.otp.allowed_methods.includes('email')}
															onChange={(e) => {
																const currentMethods = [...setupData.login_methods.otp.allowed_methods];
																if (e.target.checked) {
																	if (!currentMethods.includes('email')) {
																		currentMethods.push('email');
																	}
																} else {
																	const index = currentMethods.indexOf('email');
																	if (index > -1) {
																		currentMethods.splice(index, 1);
																	}
																}
																updateSetupData('login_methods', {
																	otp: { ...setupData.login_methods.otp, allowed_methods: currentMethods }
																});
															}}
															className="w-[16px] h-[16px] rounded border-[#D1D5DB] text-[#5048ED]"
														/>
														<span className="text-[13px] text-[#111827]">Email</span>
													</label>
												)}
												{setupData.login_methods.allowed_usernames.includes('phone') && (
													<label className="flex items-center gap-[8px]">
														<input
															type="checkbox"
															checked={setupData.login_methods.otp.allowed_methods.includes('sms')}
															onChange={(e) => {
																const currentMethods = [...setupData.login_methods.otp.allowed_methods];
																if (e.target.checked) {
																	if (!currentMethods.includes('sms')) {
																		currentMethods.push('sms');
																	}
																} else {
																	const index = currentMethods.indexOf('sms');
																	if (index > -1) {
																		currentMethods.splice(index, 1);
																	}
																}
																updateSetupData('login_methods', {
																	otp: { ...setupData.login_methods.otp, allowed_methods: currentMethods }
																});
															}}
															className="w-[16px] h-[16px] rounded border-[#D1D5DB] text-[#5048ED]"
														/>
														<span className="text-[13px] text-[#111827]">SMS</span>
													</label>
												)}
											</div>
											{setupData.login_methods.otp.allowed_methods.length === 0 && (
												<p className="text-[11px] text-[#EF4444] mt-[8px]">At least one OTP delivery method must be selected</p>
											)}
										</div>

										{/* SMS Webhook - only show if phone is selected and SMS is in allowed methods */}
										{setupData.login_methods.allowed_usernames.includes('phone') && setupData.login_methods.otp.allowed_methods.includes('sms') && (
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
													SMS Config Key (Optional)
												</label>
												<input
													type="text"
													placeholder="e.g., twilio_config"
													value={setupData.login_methods.otp.sms_config_key}
													onChange={(e) => {
														e.stopPropagation();
														updateSetupData('login_methods', {
															otp: { ...setupData.login_methods.otp, sms_config_key: e.target.value }
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
												<label className="block text-[13px] font-medium text-[#111827] mt-[12px]">
													SMS Extra Data (JSON)
												</label>
												<JsonKeyValueInput
													value={setupData.login_methods.otp.sms_extra_data}
													onChange={(value) => {
														updateSetupData('login_methods', {
															otp: { ...setupData.login_methods.otp, sms_extra_data: value }
														});
													}}
												/>
												<p className="text-[11px] text-[#6B7280]">Additional data to send with SMS webhook</p>
											</div>
										)}

										{/* Email Webhook - only show if email is selected and email is in allowed methods */}
										{setupData.login_methods.allowed_usernames.includes('email') && setupData.login_methods.otp.allowed_methods.includes('email') && (
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
													Email Config Key (Optional)
												</label>
												<input
													type="text"
													placeholder="e.g., sendgrid_config"
													value={setupData.login_methods.otp.email_config_key}
													onChange={(e) => {
														e.stopPropagation();
														updateSetupData('login_methods', {
															otp: { ...setupData.login_methods.otp, email_config_key: e.target.value }
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
	const Step2PasswordPolicy = useMemo(() => (
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
						onChange={(e) => {
							const value = e.target.value === '' ? '' : Number(e.target.value);
							updateSetupData('password_policy', {
								min_length: value
							});
						}}
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
						onChange={(e) => {
							const value = e.target.value === '' ? '' : Number(e.target.value);
							updateSetupData('password_policy', {
								password_expiry_days: value
							});
						}}
						className="w-[120px] px-[12px] py-[8px] border border-[#E5E7EB] rounded-[8px] text-[14px] focus:outline-none focus:ring-2 focus:ring-[#5048ED] focus:border-transparent"
					/>
				</div>
			</div>
		</div>
	), [setupData.password_policy]);

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

	// Step 4: Review
	const Step4Review = () => (
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

				{/* Password Policy - Always show, even if password auth is disabled */}
				<div className="bg-[#F8FAFC] rounded-[12px] p-[20px]">
					<h4 className="text-[16px] font-medium text-[#111827] mb-[12px]">Password Policy</h4>
					{setupData.login_methods.password.enabled ? (
						<div className="space-y-[8px] text-[14px] text-[#111827]">
							<div>Minimum length: {setupData.password_policy.min_length} characters</div>
							<div>Expires every: {setupData.password_policy.password_expiry_days} days</div>
							<div>Password history: {setupData.password_policy.password_history_count} previous passwords</div>
							<div>Allow password change: {setupData.password_policy.allow_change ? 'Yes' : 'No'}</div>
							<div className="flex flex-wrap items-center gap-[8px]">
								<span>Requirements:</span>
								{setupData.password_policy.require_uppercase && <span className="px-[8px] py-[2px] bg-[#D1FAE5] text-[#065F46] rounded-[4px] text-[11px] font-medium">Uppercase</span>}
								{setupData.password_policy.require_lowercase && <span className="px-[8px] py-[2px] bg-[#D1FAE5] text-[#065F46] rounded-[4px] text-[11px] font-medium">Lowercase</span>}
								{setupData.password_policy.require_numbers && <span className="px-[8px] py-[2px] bg-[#D1FAE5] text-[#065F46] rounded-[4px] text-[11px] font-medium">Numbers</span>}
								{setupData.password_policy.require_special_chars && <span className="px-[8px] py-[2px] bg-[#D1FAE5] text-[#065F46] rounded-[4px] text-[11px] font-medium">Special chars</span>}
							</div>
						</div>
					) : (
						<div className="text-[14px] text-[#6B7280]">Password authentication is disabled</div>
					)}
				</div>

				{/* Session Policy */}
				<div className="bg-[#F8FAFC] rounded-[12px] p-[20px]">
					<h4 className="text-[16px] font-medium text-[#111827] mb-[12px]">Session Policy</h4>
					<div className="space-y-[8px] text-[14px] text-[#111827]">
						<div>Maximum concurrent sessions: {setupData.session_policy.max_concurrent_sessions === 0 ? 'Unlimited' : setupData.session_policy.max_concurrent_sessions}</div>
						<div>Force logout on password change: {setupData.session_policy.force_logout_on_password_change ? 'Yes' : 'No'}</div>
					</div>
				</div>

				{/* Two-Factor Authentication */}
				<div className="bg-[#F8FAFC] rounded-[12px] p-[20px]">
					<h4 className="text-[16px] font-medium text-[#111827] mb-[12px]">Two-Factor Authentication</h4>
					<div className="space-y-[8px] text-[14px] text-[#111827]">
						<div>Required: {setupData.two_factor_auth.required ? (
							<span className="text-[#10B981] font-medium">Yes, for all users</span>
						) : (
							<span className="text-[#6B7280]">No</span>
						)}</div>
						{setupData.two_factor_auth.required && (
							<div className="flex flex-wrap items-center gap-[8px]">
								<span>Available methods:</span>
								{setupData.two_factor_auth.allowedMethods.map((method) => (
									<span key={method} className="px-[8px] py-[2px] bg-[#EFF6FF] text-[#5048ED] rounded-[4px] text-[11px] font-medium">
										{method.charAt(0).toUpperCase() + method.slice(1)}
									</span>
								))}
							</div>
						)}
					</div>
				</div>

				{/* OTP Configuration Details */}
				{setupData.login_methods.otp.enabled && (
					<div className="bg-[#F8FAFC] rounded-[12px] p-[20px]">
						<h4 className="text-[16px] font-medium text-[#111827] mb-[12px]">OTP Configuration</h4>
						<div className="space-y-[8px] text-[14px] text-[#111827]">
							<div className="flex flex-wrap items-center gap-[8px]">
								<span>Allowed methods:</span>
								{setupData.login_methods.otp.allowed_methods.map((method) => (
									<span key={method} className="px-[8px] py-[2px] bg-[#EFF6FF] text-[#5048ED] rounded-[4px] text-[11px] font-medium">
										{method.charAt(0).toUpperCase() + method.slice(1)}
									</span>
								))}
							</div>
							{setupData.login_methods.otp.sms_webhook && (
								<div>SMS Webhook: <span className="font-mono text-[12px] bg-[#F3F4F6] px-[8px] py-[2px] rounded">{setupData.login_methods.otp.sms_webhook}</span></div>
							)}
							{setupData.login_methods.otp.email_webhook && (
								<div>Email Webhook: <span className="font-mono text-[12px] bg-[#F3F4F6] px-[8px] py-[2px] rounded">{setupData.login_methods.otp.email_webhook}</span></div>
							)}
							{setupData.login_methods.otp.sms_content && (
								<div>SMS Template: <span className="font-mono text-[12px] bg-[#F3F4F6] px-[8px] py-[2px] rounded">{setupData.login_methods.otp.sms_content}</span></div>
							)}
							{setupData.login_methods.otp.email_subject && (
								<div>Email Subject: <span className="font-mono text-[12px] bg-[#F3F4F6] px-[8px] py-[2px] rounded">{setupData.login_methods.otp.email_subject}</span></div>
							)}
						</div>
					</div>
				)}

				{/* Password Reset Configuration */}
				{setupData.login_methods.password.enabled && setupData.login_methods.password.forgot_password_enabled && (
					<div className="bg-[#F8FAFC] rounded-[12px] p-[20px]">
						<h4 className="text-[16px] font-medium text-[#111827] mb-[12px]">Password Reset Configuration</h4>
						<div className="space-y-[8px] text-[14px] text-[#111827]">
							<div>Reset method: {setupData.login_methods.password.reset_method === 'link' ? 'Email link' : 'Verification code'}</div>
							<div>Reset link expiry: {setupData.login_methods.password.reset_expiry_minutes} minutes</div>
							<div>Reset via SMS: {setupData.login_methods.password.reset_via_sms ? 'Enabled' : 'Disabled'}</div>
							<div>Reset via Email: {setupData.login_methods.password.reset_via_email ? 'Enabled' : 'Disabled'}</div>
							{setupData.login_methods.password.reset_sms_webhook && (
								<div>SMS Webhook: <span className="font-mono text-[12px] bg-[#F3F4F6] px-[8px] py-[2px] rounded">{setupData.login_methods.password.reset_sms_webhook}</span></div>
							)}
							{setupData.login_methods.password.reset_email_webhook && (
								<div>Email Webhook: <span className="font-mono text-[12px] bg-[#F3F4F6] px-[8px] py-[2px] rounded">{setupData.login_methods.password.reset_email_webhook}</span></div>
							)}
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
				return Step2PasswordPolicy;
			case 3:
				return <Step3TwoFactor />;
			case 4:
				return <Step4Review />;
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

									<div className="flex items-center gap-[12px]">
										{/* Skip to Review button - show on steps 1-4 when can proceed */}
										{currentStep < totalSteps && canProceed() && (
											<button
												onClick={() => setCurrentStep(totalSteps)}
												className="px-[16px] py-[10px] rounded-[8px] font-medium text-[14px] text-[#6B7280] border border-[#E5E7EB] hover:bg-[#F9FAFB] transition-all"
											>
												{currentStep === 1 ? 'Review Current Config' : 'Skip to Review'}
											</button>
										)}

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