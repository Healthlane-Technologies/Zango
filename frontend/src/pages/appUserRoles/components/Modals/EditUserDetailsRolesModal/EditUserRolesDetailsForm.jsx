import { Formik } from 'formik';
import { get } from 'lodash';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import * as Yup from 'yup';
import InputField from '../../../../../components/Form/InputField';
import MultiSelectField from '../../../../../components/Form/MultiSelectField';
import CheckboxField from '../../../../../components/Form/CheckboxField';
import SubmitButton from '../../../../../components/Form/SubmitButton';
import useApi from '../../../../../hooks/useApi';
import { transformToFormData } from '../../../../../utils/form';
import {
    selectAppUserRolesData,
    selectAppUserRolesFormData,
    toggleRerenderPage,
} from '../../../slice';

const EditUserRolesDetailsForm = ({ closeModal }) => {
    let { appId } = useParams();
    const dispatch = useDispatch();

    const appUserRolesData = useSelector(selectAppUserRolesData);
    const appUserRolesFormData = useSelector(selectAppUserRolesFormData);

    const triggerApi = useApi();

    // Check if this is a reserved role
    const isReservedRole = appUserRolesFormData?.name === 'AnonymousUsers' || appUserRolesFormData?.name === 'SystemUsers';

    // Get two-factor method options from the dropdown data or use defaults
    const twoFactorMethodOptions = appUserRolesData?.dropdown_options?.two_factor_methods ?? [
        { id: "email", label: "Email" },
        { id: "sms", label: "SMS" },
    ];

    const MultiSelectChips = ({ label, options, value, onChange, description }) => (
        <div className="space-y-[12px]">
            <div>
                <label className="font-lato text-[12px] font-semibold text-[#A3ABB1] uppercase tracking-[0.5px]">
                    {label}
                </label>
                {description && (
                    <p className="font-lato text-[10px] leading-[14px] text-[#6B7280] mt-[2px]">
                        {description}
                    </p>
                )}
            </div>
            <div className="flex flex-wrap gap-[8px]">
                {options.map((option) => {
                    const isSelected = Array.isArray(value) ? value.includes(option.id) : value === option.id;
                    return (
                        <button
                            key={option.id}
                            type="button"
                            onClick={() => {
                                const currentValue = Array.isArray(value) ? value : [value];
                                const newValue = isSelected
                                    ? currentValue.filter(v => v !== option.id)
                                    : [...currentValue, option.id];
                                onChange(newValue);
                            }}
                            className={`px-[12px] py-[6px] rounded-[6px] border font-lato text-[12px] font-medium transition-all duration-200 flex items-center gap-[6px] ${
                                isSelected
                                    ? 'border-[#5048ED] bg-[#5048ED] text-white'
                                    : 'border-[#E5E7EB] bg-white text-[#6B7280] hover:border-[#5048ED] hover:bg-[#F8FAFC]'
                            }`}
                        >
                            {isSelected && (
                                <svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M10 3L4.5 8.5L2 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                                </svg>
                            )}
                            {option.label}
                        </button>
                    );
                })}
            </div>
        </div>
    );

    const ToggleCard = ({ title, description, name, value, onChange, children }) => (
        <div className={`rounded-[8px] border transition-all duration-200 ${
            value ? 'border-[#5048ED] bg-[#F8FAFC]' : 'border-[#E5E7EB] bg-white'
        }`}>
            <div className="p-[12px]">
                <div className="flex items-start gap-[8px]">
                    <CheckboxField
                        name={name}
                        value={value}
                        onChange={onChange}
                    />
                    <div className="flex-1">
                        <h4 className="font-lato text-[12px] font-semibold leading-[16px] text-[#111827]">
                            {title}
                        </h4>
                        {description && (
                            <p className="font-lato text-[10px] leading-[14px] text-[#6B7280] mt-[2px]">
                                {description}
                            </p>
                        )}
                    </div>
                </div>
                {value && children && (
                    <div className="mt-[12px] pl-[24px] space-y-[8px]">
                        {children}
                    </div>
                )}
            </div>
        </div>
    );

    // Get default values - only include auth_config if it exists in the form data
    const getDefaultValues = () => {
        const existingAuthConfig = appUserRolesFormData?.auth_config || {};
        
        return {
            name: appUserRolesFormData?.name ?? '',
            policies: appUserRolesFormData?.attached_policies?.map((eachApp) => eachApp.id) ?? [],
            // Only include auth_config properties if they exist in the existing data
            auth_config: {
                redirect_url: existingAuthConfig?.redirect_url ?? '/frame/router',
                two_factor_auth: {
                    required: existingAuthConfig?.two_factor_auth?.required ?? false,
                    allowedMethods: existingAuthConfig?.two_factor_auth?.allowedMethods ?? [],
                },
                password_policy: {
                    min_length: existingAuthConfig?.password_policy?.min_length ?? '',
                    require_numbers: existingAuthConfig?.password_policy?.require_numbers ?? false,
                    require_lowercase: existingAuthConfig?.password_policy?.require_lowercase ?? false,
                    require_uppercase: existingAuthConfig?.password_policy?.require_uppercase ?? false,
                    require_special_chars: existingAuthConfig?.password_policy?.require_special_chars ?? false,
                    password_expiry_days: existingAuthConfig?.password_policy?.password_expiry_days ?? '',
                    password_history_count: existingAuthConfig?.password_policy?.password_history_count ?? '',
                },
            },
        };
    };

    let initialValues = getDefaultValues();

    // Get validation constraints from appUserRolesData or use defaults
    const getValidationConstraints = () => {
        const constraints = appUserRolesData?.validation_constraints || {};
        
        return {
            password_policy: {
                min_length: {
                    min: constraints.password_policy?.min_length?.min ?? 4,
                    max: constraints.password_policy?.min_length?.max ?? 128,
                },
                password_expiry_days: {
                    min: constraints.password_policy?.password_expiry_days?.min ?? 0,
                    max: constraints.password_policy?.password_expiry_days?.max ?? 365,
                },
                password_history_count: {
                    min: constraints.password_policy?.password_history_count?.min ?? 0,
                    max: constraints.password_policy?.password_history_count?.max ?? 24,
                },
            },
        };
    };

    const validationConstraints = getValidationConstraints();

    let validationSchema = Yup.object({
        name: isReservedRole ? Yup.string() : Yup.string().required('Required'),
        auth_config: Yup.object({
            redirect_url: isReservedRole ? Yup.string() : Yup.string().required('Required'),
            two_factor_auth: Yup.object({
                required: Yup.boolean(),
                allowedMethods: Yup.array().when('required', {
                    is: true,
                    then: () => Yup.array().min(1, 'At least one method is required'),
                    otherwise: () => Yup.array(),
                }),
            }),
            password_policy: Yup.object({
                min_length: Yup.number()
                    .nullable()
                    .transform((value, originalValue) => (originalValue === '' ? null : value))
                    .when('$isSet', {
                        is: true,
                        then: () => Yup.number()
                            .min(validationConstraints.password_policy.min_length.min, `Minimum length must be at least ${validationConstraints.password_policy.min_length.min}`)
                            .max(validationConstraints.password_policy.min_length.max, `Maximum length is ${validationConstraints.password_policy.min_length.max}`),
                    }),
                require_numbers: Yup.boolean(),
                require_lowercase: Yup.boolean(),
                require_uppercase: Yup.boolean(),
                require_special_chars: Yup.boolean(),
                password_expiry_days: Yup.number()
                    .nullable()
                    .transform((value, originalValue) => (originalValue === '' ? null : value))
                    .when('$isSet', {
                        is: true,
                        then: () => Yup.number()
                            .min(validationConstraints.password_policy.password_expiry_days.min, `Must be at least ${validationConstraints.password_policy.password_expiry_days.min} days`)
                            .max(validationConstraints.password_policy.password_expiry_days.max, `Must be less than ${validationConstraints.password_policy.password_expiry_days.max} days`),
                    }),
                password_history_count: Yup.number()
                    .nullable()
                    .transform((value, originalValue) => (originalValue === '' ? null : value))
                    .when('$isSet', {
                        is: true,
                        then: () => Yup.number()
                            .min(validationConstraints.password_policy.password_history_count.min, 'Cannot be negative')
                            .max(validationConstraints.password_policy.password_history_count.max, `Maximum is ${validationConstraints.password_policy.password_history_count.max}`),
                    }),
            }),
        }),
    });

    // Helper function to remove empty/default values from auth_config
    const cleanAuthConfig = (authConfig) => {
        const cleanedConfig = {};
        
        // Always include redirect_url
        cleanedConfig.redirect_url = authConfig.redirect_url;
        
        // Handle two_factor_auth
        if (authConfig.two_factor_auth.required || authConfig.two_factor_auth.allowedMethods.length > 0) {
            cleanedConfig.two_factor_auth = {};
            if (authConfig.two_factor_auth.required) {
                cleanedConfig.two_factor_auth.required = true;
            }
            if (authConfig.two_factor_auth.allowedMethods.length > 0) {
                cleanedConfig.two_factor_auth.allowedMethods = authConfig.two_factor_auth.allowedMethods;
            }
        }
        
        // Handle password_policy
        const passwordPolicyConfig = {};
        let hasPasswordPolicy = false;
        
        if (authConfig.password_policy.min_length !== '' && authConfig.password_policy.min_length !== null) {
            passwordPolicyConfig.min_length = authConfig.password_policy.min_length;
            hasPasswordPolicy = true;
        }
        
        if (authConfig.password_policy.require_numbers) {
            passwordPolicyConfig.require_numbers = true;
            hasPasswordPolicy = true;
        }
        
        if (authConfig.password_policy.require_lowercase) {
            passwordPolicyConfig.require_lowercase = true;
            hasPasswordPolicy = true;
        }
        
        if (authConfig.password_policy.require_uppercase) {
            passwordPolicyConfig.require_uppercase = true;
            hasPasswordPolicy = true;
        }
        
        if (authConfig.password_policy.require_special_chars) {
            passwordPolicyConfig.require_special_chars = true;
            hasPasswordPolicy = true;
        }
        
        if (authConfig.password_policy.password_expiry_days !== '' && authConfig.password_policy.password_expiry_days !== null) {
            passwordPolicyConfig.password_expiry_days = authConfig.password_policy.password_expiry_days;
            hasPasswordPolicy = true;
        }
        
        if (authConfig.password_policy.password_history_count !== '' && authConfig.password_policy.password_history_count !== null) {
            passwordPolicyConfig.password_history_count = authConfig.password_policy.password_history_count;
            hasPasswordPolicy = true;
        }
        
        if (hasPasswordPolicy) {
            cleanedConfig.password_policy = passwordPolicyConfig;
        }
        
        return cleanedConfig;
    };

    let onSubmit = (values) => {
        // Clean auth_config to only include explicitly set values
        const cleanedAuthConfig = cleanAuthConfig(values.auth_config);
        
        // Transform the values to include auth_config as JSON only if it has content
        let tempValues = {
            ...values,
        };
        
        // Only include auth_config if it has actual content
        if (Object.keys(cleanedAuthConfig).length > 0) {
            tempValues.auth_config = JSON.stringify(cleanedAuthConfig);
        }

        let dynamicFormData = transformToFormData(tempValues);

        const makeApiCall = async () => {
            const { response, success } = await triggerApi({
                url: `/api/v1/apps/${appId}/roles/${appUserRolesFormData?.id}/`,
                type: 'PUT',
                loader: true,
                payload: dynamicFormData,
            });

            if (success && response) {
                closeModal();
                dispatch(toggleRerenderPage());
            }
        };

        makeApiCall();
    };

    return (
        <Formik
            initialValues={initialValues}
            validationSchema={validationSchema}
            onSubmit={onSubmit}
        >
            {(formik) => {
                return (
                    <form
                        className="complete-hidden-scroll-style flex grow flex-col gap-4 overflow-y-auto"
                        onSubmit={formik.handleSubmit}
                    >
                        <div className="flex grow flex-col gap-[24px]">
                            {/* Role Information Section */}
                            <div className="space-y-[16px]">
                                <h3 className="font-lato text-[16px] font-semibold text-[#111827] border-b border-[#E5E7EB] pb-[8px] flex items-center gap-[8px]">
                                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[#6366F1]">
                                        <path d="M8 8a3 3 0 100-6 3 3 0 000 6zM8 10c-4 0-7 2-7 4v1h14v-1c0-2-3-4-7-4z" fill="currentColor"/>
                                    </svg>
                                    Role Information
                                </h3>

                                {isReservedRole ? (
                                    <div className="bg-[#FEF3C7] border border-[#F59E0B] rounded-[8px] p-[16px]">
                                        <div className="flex items-start gap-[8px]">
                                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[#F59E0B] mt-[2px]">
                                                <path d="M8 1a7 7 0 100 14A7 7 0 008 1zM8 4a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 018 4zm0 8a1 1 0 100-2 1 1 0 000 2z" fill="currentColor"/>
                                            </svg>
                                            <div>
                                                <p className="font-lato text-[12px] font-semibold text-[#92400E] uppercase tracking-[0.5px]">Reserved Role</p>
                                                <h3 className="font-lato text-[16px] font-semibold text-[#92400E] mb-[4px]">{appUserRolesFormData?.name}</h3>
                                                <p className="font-lato text-[12px] text-[#92400E]">This is a system role required for application functionality. You can only modify its policies and authentication settings.</p>
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <InputField
                                        key="name"
                                        label="Role Name"
                                        name="name"
                                        id="name"
                                        placeholder="Enter role name"
                                        value={get(formik.values, 'name', '')}
                                        onChange={formik.handleChange}
                                        formik={formik}
                                    />
                                )}
                            </div>

                            {/* Policies Section */}
                            <div className="space-y-[16px]">
                                <h3 className="font-lato text-[16px] font-semibold text-[#111827] border-b border-[#E5E7EB] pb-[8px] flex items-center gap-[8px]">
                                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[#10B981]">
                                        <path d="M4 3a2 2 0 00-2 2v1a2 2 0 002 2h1a2 2 0 002-2V5a2 2 0 00-2-2H4zM9 3a2 2 0 00-2 2v1a2 2 0 002 2h1a2 2 0 002-2V5a2 2 0 00-2-2H9zM4 9a2 2 0 00-2 2v1a2 2 0 002 2h1a2 2 0 002-2v-1a2 2 0 00-2-2H4zM9 9a2 2 0 00-2 2v1a2 2 0 002 2h1a2 2 0 002-2v-1a2 2 0 00-2-2H9z" fill="currentColor"/>
                                    </svg>
                                    Access Policies
                                    <span className="ml-auto text-[12px] font-normal text-[#6B7280] bg-[#F3F4F6] px-[8px] py-[2px] rounded-[12px]">
                                        {get(formik.values, 'policies', []).length} selected
                                    </span>
                                </h3>

                                <div className="bg-[#F9FAFB] border border-[#E5E7EB] rounded-[8px] p-[12px]">
                                    <p className="font-lato text-[12px] text-[#6B7280] mb-[2px]">
                                        <strong>Tip:</strong> Policies control what users in this role can access and do in the application.
                                    </p>
                                    <p className="font-lato text-[11px] text-[#6B7280]">
                                        Select the appropriate policies based on the responsibilities of users in this role.
                                    </p>
                                </div>

                                <MultiSelectField
                                    key="policies"
                                    label="Available Policies"
                                    name="policies"
                                    id="policies"
                                    placeholder="Select policies to attach"
                                    value={get(formik.values, 'policies', [])}
                                    optionsDataName="policies"
                                    optionsData={appUserRolesData?.dropdown_options?.policies ?? []}
                                    formik={formik}
                                />
                            </div>

                            {/* Authentication Settings Section */}
                            <div className="space-y-[16px]">
                                <h3 className="font-lato text-[16px] font-semibold text-[#111827] border-b border-[#E5E7EB] pb-[8px] flex items-center gap-[8px]">
                                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[#F59E0B]">
                                        <path d="M3 5a2 2 0 012-2h6a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2V5zM8 6a2 2 0 100 4 2 2 0 000-4z" fill="currentColor"/>
                                    </svg>
                                    Authentication Settings
                                </h3>

                                {!isReservedRole && (
                                    <InputField
                                        key="auth_config.redirect_url"
                                        label="Redirect URL"
                                        name="auth_config.redirect_url"
                                        id="auth_config.redirect_url"
                                        placeholder="Enter redirect URL"
                                        value={get(formik.values, 'auth_config.redirect_url', '')}
                                        onChange={formik.handleChange}
                                        formik={formik}
                                    />
                                )}

                                {/* Two-Factor Authentication Section */}
                                <div className="space-y-[12px]">
                                    <h4 className="font-lato text-[14px] font-semibold text-[#111827] flex items-center gap-[6px]">
                                        <svg width="14" height="14" viewBox="0 0 16 16" fill="none" className="text-[#6366F1]">
                                            <path d="M8 2a2 2 0 00-2 2v2H4a1 1 0 00-1 1v6a1 1 0 001 1h8a1 1 0 001-1V7a1 1 0 00-1-1h-2V4a2 2 0 00-2-2z" fill="currentColor"/>
                                        </svg>
                                        Two-Factor Authentication
                                    </h4>
                                <ToggleCard
                                    title="Require Two-Factor Authentication"
                                    description="Make 2FA mandatory for users with this role"
                                    name="auth_config.two_factor_auth.required"
                                    value={get(formik.values, 'auth_config.two_factor_auth.required', false)}
                                    onChange={(e) => formik.setFieldValue('auth_config.two_factor_auth.required', e.target.checked)}
                                >
                                    <MultiSelectChips
                                        name="auth_config.two_factor_auth.allowedMethods"
                                        label="Allowed Methods"
                                        description="Select available methods for two-factor authentication"
                                        options={twoFactorMethodOptions}
                                        value={get(formik.values, 'auth_config.two_factor_auth.allowedMethods', [])}
                                        onChange={(value) => formik.setFieldValue('auth_config.two_factor_auth.allowedMethods', value)}
                                    />
                                </ToggleCard>
                            </div>

                                {/* Password Policy Section */}
                                <div className="space-y-[12px]">
                                    <h4 className="font-lato text-[14px] font-semibold text-[#111827] flex items-center gap-[6px]">
                                        <svg width="14" height="14" viewBox="0 0 16 16" fill="none" className="text-[#EF4444]">
                                            <path d="M3 7a1 1 0 011-1h8a1 1 0 011 1v5a1 1 0 01-1 1H4a1 1 0 01-1-1V7zM5 5a3 3 0 116 0v1H5V5z" fill="currentColor"/>
                                        </svg>
                                        Password Policy
                                    </h4>
                                <div className="grid grid-cols-2 gap-[12px]">
                                    <InputField
                                        key="auth_config.password_policy.min_length"
                                        label="Minimum Length"
                                        name="auth_config.password_policy.min_length"
                                        id="auth_config.password_policy.min_length"
                                        type="number"
                                        placeholder="Enter minimum length"
                                        value={get(formik.values, 'auth_config.password_policy.min_length', '')}
                                        onChange={formik.handleChange}
                                        formik={formik}
                                    />
                                    <InputField
                                        key="auth_config.password_policy.password_expiry_days"
                                        label="Password Expiry (Days)"
                                        name="auth_config.password_policy.password_expiry_days"
                                        id="auth_config.password_policy.password_expiry_days"
                                        type="number"
                                        placeholder="Enter expiry days"
                                        value={get(formik.values, 'auth_config.password_policy.password_expiry_days', '')}
                                        onChange={formik.handleChange}
                                        formik={formik}
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-[12px]">
                                    <ToggleCard
                                        title="Require Numbers"
                                        description="Passwords must contain numbers"
                                        name="auth_config.password_policy.require_numbers"
                                        value={get(formik.values, 'auth_config.password_policy.require_numbers', false)}
                                        onChange={(e) => formik.setFieldValue('auth_config.password_policy.require_numbers', e.target.checked)}
                                    />
                                    <ToggleCard
                                        title="Require Uppercase"
                                        description="Passwords must contain uppercase letters"
                                        name="auth_config.password_policy.require_uppercase"
                                        value={get(formik.values, 'auth_config.password_policy.require_uppercase', false)}
                                        onChange={(e) => formik.setFieldValue('auth_config.password_policy.require_uppercase', e.target.checked)}
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-[12px]">
                                    <ToggleCard
                                        title="Require Lowercase"
                                        description="Passwords must contain lowercase letters"
                                        name="auth_config.password_policy.require_lowercase"
                                        value={get(formik.values, 'auth_config.password_policy.require_lowercase', false)}
                                        onChange={(e) => formik.setFieldValue('auth_config.password_policy.require_lowercase', e.target.checked)}
                                    />
                                    <ToggleCard
                                        title="Require Special Characters"
                                        description="Passwords must contain special characters"
                                        name="auth_config.password_policy.require_special_chars"
                                        value={get(formik.values, 'auth_config.password_policy.require_special_chars', false)}
                                        onChange={(e) => formik.setFieldValue('auth_config.password_policy.require_special_chars', e.target.checked)}
                                    />
                                </div>
                                    <InputField
                                        key="auth_config.password_policy.password_history_count"
                                        label="Password History Count"
                                        name="auth_config.password_policy.password_history_count"
                                        id="auth_config.password_policy.password_history_count"
                                        type="number"
                                        placeholder="Enter history count"
                                        value={get(formik.values, 'auth_config.password_policy.password_history_count', '')}
                                        onChange={formik.handleChange}
                                        formik={formik}
                                    />
                                </div>
                            </div>
                        </div>
                        <div className="sticky bottom-0 flex flex-col gap-[8px] bg-[#ffffff] pt-[24px] font-lato text-[#696969]">
                            <SubmitButton
                                label={'Save'}
                                formik={formik}
                                allowDisabled={false}
                            />
                        </div>
                    </form>
                );
            }}
        </Formik>
    );
};

export default EditUserRolesDetailsForm;
