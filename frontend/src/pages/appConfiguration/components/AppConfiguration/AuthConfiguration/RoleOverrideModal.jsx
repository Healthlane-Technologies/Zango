import React, { useState, useEffect } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';

const RoleOverrideModal = ({ show, onClose, onSave, roles = [], globalAuthConfig = {}, currentOverrides = {}, initialSelectedRoleId = null }) => {
	const [selectedRoleId, setSelectedRoleId] = useState(null);
	const [roleOverrideStates, setRoleOverrideStates] = useState({});
	const [overrideConfig, setOverrideConfig] = useState({
		password_policy: null,
		two_factor_auth: null,
		session_policy: null,
		redirect_url: '/frame/router/',
	});

	// Initialize role override states from currentOverrides
	useEffect(() => {
		if (show && roles.length > 0) {
			const states = {};
			roles.forEach(role => {
				const override = currentOverrides[role.id];
				// Use override_applied flag to determine if role has custom policies
				// If not present, consider role as not overridden
				states[role.id] = override?.override_applied === true;
			});
			setRoleOverrideStates(states);
		}
	}, [show, roles, currentOverrides]);

	// Reset state when modal opens
	useEffect(() => {
		if (show) {
			// Set the selected role if initialSelectedRoleId is provided
			setSelectedRoleId(initialSelectedRoleId);
			setOverrideConfig({
				password_policy: null,
				two_factor_auth: null,
				session_policy: null,
				redirect_url: '/frame/router/',
			});
		}
	}, [show, initialSelectedRoleId]);

	// Load existing override when role is selected
	useEffect(() => {
		if (selectedRoleId && currentOverrides[selectedRoleId]) {
			const override = currentOverrides[selectedRoleId];
			setOverrideConfig({
				...override,
				redirect_url: override.redirect_url || '/frame/router/',
			});
		} else if (selectedRoleId) {
			// Initialize with null values for new override
			setOverrideConfig({
				password_policy: null,
				two_factor_auth: null,
				session_policy: null,
				redirect_url: '/frame/router/',
			});
		}
	}, [selectedRoleId, currentOverrides]);

	const handleSave = () => {
		if (!selectedRoleId) {
			alert('Please select a role first');
			return;
		}

		const roleOverrideEnabled = roleOverrideStates[selectedRoleId];
		let cleanedOverride = {};

		// Always ensure we have a redirect_url value
		const redirectUrl = overrideConfig.redirect_url || '/frame/router/';

		if (roleOverrideEnabled) {
			// If role override is enabled, send the entire auth_config with override_applied flag
			cleanedOverride.override_applied = true;

			if (overrideConfig.password_policy) {
				cleanedOverride.password_policy = overrideConfig.password_policy;
			}
			if (overrideConfig.two_factor_auth) {
				cleanedOverride.two_factor_auth = overrideConfig.two_factor_auth;
			}
			if (overrideConfig.session_policy) {
				cleanedOverride.session_policy = overrideConfig.session_policy;
			}
			// Include redirect_url
			cleanedOverride.redirect_url = redirectUrl;
		} else {
			// If role override is disabled, only send redirect_url with override_applied: false
			cleanedOverride.override_applied = false;
			cleanedOverride.redirect_url = redirectUrl;
		}

		onSave(selectedRoleId, cleanedOverride);
		onClose();
	};

	const handleRemoveOverride = () => {
		if (!selectedRoleId) return;

		if (window.confirm('Are you sure you want to remove this role override?')) {
			// When removing override, send empty auth_config with override_applied: false and redirect_url
			const emptyConfig = {
				override_applied: false,
				redirect_url: overrideConfig.redirect_url || '/frame/router/'
			};
			onSave(selectedRoleId, emptyConfig);
			onClose();
		}
	};

	const toggleRoleOverride = (roleId, enabled) => {
		setRoleOverrideStates(prev => ({
			...prev,
			[roleId]: enabled
		}));

		// When disabling override, clear all policy configs but keep redirect_url
		if (!enabled && roleId === selectedRoleId) {
			setOverrideConfig(prev => ({
				password_policy: null,
				two_factor_auth: null,
				session_policy: null,
				redirect_url: prev.redirect_url || '/frame/router/',
			}));
		}
	};

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

	const enablePasswordPolicyOverride = !!overrideConfig.password_policy;
	const enableTwoFactorOverride = !!overrideConfig.two_factor_auth;
	const enableSessionPolicyOverride = !!overrideConfig.session_policy;

	const togglePasswordPolicy = (enabled) => {
		if (enabled) {
			setOverrideConfig(prev => ({
				...prev,
				password_policy: {
					min_length: globalAuthConfig.password_policy?.min_length || 8,
					require_uppercase: globalAuthConfig.password_policy?.require_uppercase || false,
					require_lowercase: globalAuthConfig.password_policy?.require_lowercase || false,
					require_numbers: globalAuthConfig.password_policy?.require_numbers || false,
					require_special_chars: globalAuthConfig.password_policy?.require_special_chars || false,
					password_history_count: globalAuthConfig.password_policy?.password_history_count || 3,
					password_expiry_days: globalAuthConfig.password_policy?.password_expiry_days || 90,
					allow_change: globalAuthConfig.password_policy?.allow_change ?? true,
				}
			}));
		} else {
			setOverrideConfig(prev => ({ ...prev, password_policy: null }));
		}
	};

	const toggleTwoFactorAuth = (enabled) => {
		if (enabled) {
			setOverrideConfig(prev => ({
				...prev,
				two_factor_auth: {
					required: true,
					allowedMethods: globalAuthConfig.two_factor_auth?.allowedMethods || ['email'],
				}
			}));
		} else {
			setOverrideConfig(prev => ({ ...prev, two_factor_auth: null }));
		}
	};

	const toggleSessionPolicy = (enabled) => {
		if (enabled) {
			setOverrideConfig(prev => ({
				...prev,
				session_policy: {
					max_concurrent_sessions: globalAuthConfig.session_policy?.max_concurrent_sessions || 0,
					force_logout_on_password_change: globalAuthConfig.session_policy?.force_logout_on_password_change || false,
				}
			}));
		} else {
			setOverrideConfig(prev => ({ ...prev, session_policy: null }));
		}
	};

	const selectedRole = roles.find(r => r.id === selectedRoleId);
	const hasExistingOverride = selectedRoleId && currentOverrides[selectedRoleId];

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
							<Dialog.Panel className="w-full max-w-3xl transform overflow-hidden rounded-2xl bg-white text-left align-middle shadow-xl transition-all">
								{/* Header */}
								<div className="bg-gradient-to-r from-[#5048ED] to-[#346BD4] px-[32px] py-[24px]">
									<div className="flex items-center justify-between">
										<div className="flex items-center gap-[16px]">
											<div className="w-[48px] h-[48px] bg-white/20 rounded-full flex items-center justify-center">
												<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
													<path d="M12 12C14.21 12 16 10.21 16 8C16 5.79 14.21 4 12 4C9.79 4 8 5.79 8 8C8 10.21 9.79 12 12 12ZM12 14C9.33 14 4 15.34 4 18V20H20V18C20 15.34 14.67 14 12 14Z" fill="white"/>
												</svg>
											</div>
											<div>
												<Dialog.Title as="h3" className="text-[20px] font-semibold text-white">
													{selectedRole ? `Configure ${selectedRole.name}` : 'Role Authentication Override'}
												</Dialog.Title>
												<p className="text-[14px] text-white/80 mt-[2px]">
													{selectedRole ? 'Configure authentication policies for this role' : 'Configure stricter auth policies for a specific role'}
												</p>
											</div>
										</div>
										<button
											onClick={onClose}
											className="text-white/80 hover:text-white transition-colors"
										>
											<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
												<path d="M18 6L6 18M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
											</svg>
										</button>
									</div>
								</div>

								{/* Content */}
								<div className="px-[32px] py-[24px] max-h-[calc(100vh-300px)] overflow-y-auto">
									{/* Info Banner */}
									<div className="mb-[24px] p-[16px] bg-[#FEF3C7] border border-[#F59E0B] rounded-[12px] flex gap-[12px]">
										<svg width="20" height="20" viewBox="0 0 20 20" fill="none" className="text-[#F59E0B] flex-shrink-0 mt-[2px]">
											<path d="M10 5V11M10 15H10.01M18 10C18 14.4183 14.4183 18 10 18C5.58172 18 2 14.4183 2 10C2 5.58172 5.58172 2 10 2C14.4183 2 18 5.58172 18 10Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
										</svg>
										<div className="flex-1">
											<h4 className="text-[14px] font-semibold text-[#92400E] mb-[4px]">Important</h4>
											<p className="text-[13px] text-[#92400E]">
												Role overrides can only enforce stricter policies than global settings.
											</p>
										</div>
									</div>

									{/* Role Selection - Only show if no role is pre-selected */}
									{!initialSelectedRoleId && (
										<div className="mb-[32px]">
										<label className="block text-[14px] font-semibold text-[#111827] mb-[12px]">
											Select Role to Override
										</label>
										<div className="grid grid-cols-1 gap-[12px]">
											{roles.map((role) => {
												const hasOverride = currentOverrides[role.id];
												const isSelected = selectedRoleId === role.id;
												const isOverrideEnabled = roleOverrideStates[role.id] || false;

												return (
													<div
														key={role.id}
														className={`w-full rounded-[12px] border-2 transition-all ${
															isSelected
																? 'border-[#5048ED] bg-[#F8FAFC] shadow-md'
																: hasOverride
																? 'border-[#10B981] bg-[#F0FDF4]'
																: 'border-[#E5E7EB] bg-white'
														}`}
													>
														<button
															type="button"
															onClick={() => setSelectedRoleId(role.id)}
															className="w-full text-left px-[20px] py-[16px] hover:bg-opacity-80 transition-all"
														>
															<div className="flex items-center justify-between">
																<div className="flex items-center gap-[12px]">
																	<div className={`w-[36px] h-[36px] rounded-[8px] flex items-center justify-center ${
																		isSelected
																			? 'bg-[#5048ED] text-white'
																			: hasOverride
																			? 'bg-[#10B981] text-white'
																			: 'bg-[#F3F4F6] text-[#6B7280]'
																	}`}>
																		<svg width="18" height="18" viewBox="0 0 18 18" fill="none">
																			<path d="M9 9C10.6569 9 12 7.65685 12 6C12 4.34315 10.6569 3 9 3C7.34315 3 6 4.34315 6 6C6 7.65685 7.34315 9 9 9Z" stroke="currentColor" strokeWidth="1.5"/>
																			<path d="M3 15C3 12.7909 4.79086 11 7 11H11C13.2091 11 15 12.7909 15 15" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
																		</svg>
																	</div>
																	<div>
																		<h4 className="text-[15px] font-medium text-[#111827]">{role.name}</h4>
																		<p className="text-[12px] text-[#6B7280]">
																			{hasOverride ? 'Has custom override configured' : 'Using global policies'}
																		</p>
																	</div>
																</div>
																{isSelected && (
																	<svg width="20" height="20" viewBox="0 0 20 20" fill="none" className="text-[#5048ED]">
																		<circle cx="10" cy="10" r="10" fill="currentColor"/>
																		<path d="M8 10L9.5 11.5L12.5 8.5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
																	</svg>
																)}
															</div>
														</button>

														{/* Enable Override Toggle */}
														<div className="px-[20px] pb-[16px] border-t border-[#E5E7EB] pt-[12px] mt-[4px]">
															<div className="flex items-center justify-between">
																<div>
																	<p className="text-[13px] font-medium text-[#111827]">Enable Role Override</p>
																	<p className="text-[11px] text-[#6B7280]">Configure custom auth policies</p>
																</div>
																<ToggleSwitch
																	checked={isOverrideEnabled}
																	onChange={(checked) => toggleRoleOverride(role.id, checked)}
																/>
															</div>
														</div>
													</div>
												);
											})}
										</div>
									</div>
									)}

									{/* Configuration Form - Only show when role is selected */}
									{selectedRole && (
										<div className="space-y-[24px]">
											<div className={!initialSelectedRoleId ? "border-t border-[#E5E7EB] pt-[24px]" : ""}>
												<h4 className="text-[16px] font-semibold text-[#111827] mb-[16px]">
													Configure Overrides for {selectedRole.name}
												</h4>

												{/* Enable Override Toggle - Show when role is pre-selected */}
												{initialSelectedRoleId && (
													<div className="mb-[24px] bg-gradient-to-r from-[#EFF6FF] to-[#F3F4F6] rounded-[12px] p-[20px] border-2 border-[#5048ED]">
														<div className="flex items-center justify-between">
															<div>
																<h5 className="text-[15px] font-semibold text-[#111827] mb-[4px]">Enable Role Override</h5>
																<p className="text-[13px] text-[#6B7280]">
																	Enable to configure custom authentication policies for this role. When disabled, only redirect URL will be saved.
																</p>
															</div>
															<ToggleSwitch
																checked={roleOverrideStates[selectedRoleId] || false}
																onChange={(checked) => toggleRoleOverride(selectedRoleId, checked)}
															/>
														</div>
													</div>
												)}

												{/* Password Policy Override - Only show when override is enabled */}
												{roleOverrideStates[selectedRoleId] && (
													<div className="mb-[24px] bg-[#F8FAFC] rounded-[12px] p-[20px]">
														<div className="flex items-center justify-between mb-[16px]">
															<div>
																<h5 className="text-[14px] font-medium text-[#111827]">Password Policy Override</h5>
																<p className="text-[12px] text-[#6B7280] mt-[2px]">Define stricter password requirements</p>
															</div>
															<ToggleSwitch
																checked={enablePasswordPolicyOverride}
																onChange={togglePasswordPolicy}
															/>
														</div>

													{enablePasswordPolicyOverride && (
														<div className="mt-[20px] space-y-[16px] bg-white rounded-[8px] p-[16px]">
															<div className="grid grid-cols-2 gap-[16px]">
																<div>
																	<label className="block text-[13px] font-medium text-[#111827] mb-[8px]">
																		Minimum Password Length
																	</label>
																	<input
																		name="min_length"
																		type="number"
																		value={overrideConfig.password_policy?.min_length ?? 8}
																		onChange={(e) => setOverrideConfig(prev => ({
																			...prev,
																			password_policy: {
																				...prev.password_policy,
																				min_length: e.target.value === '' ? '' : parseInt(e.target.value)
																			}
																		}))}
																		className="w-full px-[12px] py-[8px] border border-[#E5E7EB] rounded-[8px] text-[14px] focus:outline-none focus:ring-2 focus:ring-[#5048ED] focus:border-transparent"
																	/>
																</div>
																<div>
																	<label className="block text-[13px] font-medium text-[#111827] mb-[8px]">
																		Password Expiry (Days)
																	</label>
																	<input
																		name="password_expiry_days"
																		type="number"
																		value={overrideConfig.password_policy?.password_expiry_days ?? 90}
																		onChange={(e) => setOverrideConfig(prev => ({
																			...prev,
																			password_policy: {
																				...prev.password_policy,
																				password_expiry_days: e.target.value === '' ? '' : parseInt(e.target.value)
																			}
																		}))}
																		className="w-full px-[12px] py-[8px] border border-[#E5E7EB] rounded-[8px] text-[14px] focus:outline-none focus:ring-2 focus:ring-[#5048ED] focus:border-transparent"
																	/>
																</div>
															</div>

															<div className="grid grid-cols-2 gap-[12px]">
																{[
																	{ field: 'require_uppercase', label: 'Require Uppercase' },
																	{ field: 'require_lowercase', label: 'Require Lowercase' },
																	{ field: 'require_numbers', label: 'Require Numbers' },
																	{ field: 'require_special_chars', label: 'Require Special Characters' }
																].map(({ field, label }) => (
																	<div key={field} className="flex items-center justify-between p-[12px] bg-[#F8FAFC] rounded-[8px]">
																		<span className="text-[13px] text-[#111827]">{label}</span>
																		<ToggleSwitch
																			checked={overrideConfig.password_policy?.[field] || false}
																			onChange={(checked) => setOverrideConfig(prev => ({
																				...prev,
																				password_policy: {
																					...prev.password_policy,
																					[field]: checked
																				}
																			}))}
																		/>
																	</div>
																))}
															</div>
														</div>
													)}
												</div>
												)}

												{/* Two-Factor Auth Override - Only show when override is enabled */}
												{roleOverrideStates[selectedRoleId] && (
													<div className="mb-[24px] bg-[#F8FAFC] rounded-[12px] p-[20px]">
														<div className="flex items-center justify-between mb-[16px]">
															<div>
																<h5 className="text-[14px] font-medium text-[#111827]">Two-Factor Authentication Override</h5>
																<p className="text-[12px] text-[#6B7280] mt-[2px]">Require 2FA for this role</p>
															</div>
															<ToggleSwitch
																checked={enableTwoFactorOverride}
																onChange={toggleTwoFactorAuth}
															/>
														</div>

													{enableTwoFactorOverride && (
														<div className="mt-[20px] bg-white rounded-[8px] p-[16px]">
															<p className="text-[13px] text-[#6B7280]">
																Two-factor authentication will be required for all users with this role.
															</p>
														</div>
													)}
												</div>
												)}

												{/* Session Policy Override - Only show when override is enabled */}
												{roleOverrideStates[selectedRoleId] && (
													<div className="mb-[24px] bg-[#F8FAFC] rounded-[12px] p-[20px]">
														<div className="flex items-center justify-between mb-[16px]">
															<div>
																<h5 className="text-[14px] font-medium text-[#111827]">Session Policy Override</h5>
																<p className="text-[12px] text-[#6B7280] mt-[2px]">Define stricter session limits</p>
															</div>
															<ToggleSwitch
																checked={enableSessionPolicyOverride}
																onChange={toggleSessionPolicy}
															/>
														</div>

													{enableSessionPolicyOverride && (
														<div className="mt-[20px] bg-white rounded-[8px] p-[16px]">
															<div>
																<label className="block text-[13px] font-medium text-[#111827] mb-[8px]">
																	Maximum Concurrent Sessions (0 = unlimited)
																</label>
																<input
																	name="max_concurrent_sessions"
																	type="number"
																	value={overrideConfig.session_policy?.max_concurrent_sessions ?? 0}
																	onChange={(e) => setOverrideConfig(prev => ({
																		...prev,
																		session_policy: {
																			...prev.session_policy,
																			max_concurrent_sessions: e.target.value === '' ? '' : parseInt(e.target.value)
																		}
																	}))}
																	className="w-full px-[12px] py-[8px] border border-[#E5E7EB] rounded-[8px] text-[14px] focus:outline-none focus:ring-2 focus:ring-[#5048ED] focus:border-transparent"
																/>
															</div>
														</div>
													)}
												</div>
												)}

												{/* Redirect URL */}
												<div className="bg-[#F8FAFC] rounded-[12px] p-[20px]">
													<div className="mb-[16px]">
														<h5 className="text-[14px] font-medium text-[#111827]">Redirect URL</h5>
														<p className="text-[12px] text-[#6B7280] mt-[2px]">URL to redirect users after successful login</p>
													</div>

													<div className="bg-white rounded-[8px] p-[16px]">
														<div>
															<label className="block text-[13px] font-medium text-[#111827] mb-[8px]">
																Redirect URL
															</label>
															<input
																name="redirect_url"
																type="text"
																value={overrideConfig.redirect_url || '/frame/router/'}
																onChange={(e) => setOverrideConfig(prev => ({
																	...prev,
																	redirect_url: e.target.value
																}))}
																placeholder="/frame/router/"
																className="w-full px-[12px] py-[8px] border border-[#E5E7EB] rounded-[8px] text-[14px] focus:outline-none focus:ring-2 focus:ring-[#5048ED] focus:border-transparent"
															/>
															<p className="text-[11px] text-[#6B7280] mt-[4px]">Default: /frame/router/</p>
														</div>
													</div>
												</div>
											</div>
										</div>
									)}
								</div>

								{/* Footer */}
								<div className="bg-[#F8FAFC] px-[32px] py-[20px] flex items-center justify-between border-t border-[#E5E7EB]">
									<div>
										{hasExistingOverride && (
											<button
												type="button"
												onClick={handleRemoveOverride}
												className="px-[16px] py-[8px] bg-[#EF4444] text-white rounded-[8px] hover:bg-[#DC2626] transition-colors text-[14px] font-medium"
											>
												Remove Override
											</button>
										)}
									</div>
									<div className="flex gap-[12px]">
										<button
											type="button"
											onClick={onClose}
											className="px-[16px] py-[8px] border-2 border-[#E5E7EB] text-[#6B7280] bg-white rounded-[8px] hover:border-[#D1D5DB] hover:bg-[#F9FAFB] transition-all text-[14px] font-medium"
										>
											Cancel
										</button>
										<button
											type="button"
											onClick={handleSave}
											disabled={!selectedRoleId}
											className="px-[16px] py-[8px] bg-[#5048ED] text-white rounded-[8px] hover:bg-[#4338CA] transition-colors text-[14px] font-medium disabled:opacity-50 disabled:cursor-not-allowed"
										>
											Save Override
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

export default RoleOverrideModal;
