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

    // Get two-factor method options from the dropdown data or use defaults
    const twoFactorMethodOptions = appUserRolesData?.dropdown_options?.two_factor_methods ?? [
        { id: "email", label: "Email" },
        { id: "sms", label: "SMS" },
    ];

    const MultiSelectChips = ({ label, name, options, value, onChange, description }) => (
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
        name: Yup.string().required('Required'),
        auth_config: Yup.object({
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
                        <div className="flex grow flex-col gap-[16px]">
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

                            <MultiSelectField
                                key="policies"
                                label="Policy"
                                name="policies"
                                id="policies"
                                placeholder="Select policies"
                                value={get(formik.values, 'policies', [])}
                                optionsDataName="policies"
                                optionsData={appUserRolesData?.dropdown_options?.policies ?? []}
                                formik={formik}
                            />

                            {/* Two-Factor Authentication Section */}
                            <div className="space-y-[12px]">
                                <h3 className="font-lato text-[14px] font-semibold text-[#111827] border-b border-[#E5E7EB] pb-[8px]">
                                    Two-Factor Authentication
                                </h3>
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
                                <h3 className="font-lato text-[14px] font-semibold text-[#111827] border-b border-[#E5E7EB] pb-[8px]">
                                    Password Policy
                                </h3>
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
