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
import { selectAppUserRolesData, toggleRerenderPage } from '../../../slice';

const AddNewUserRolesForm = ({ closeModal }) => {
	let { appId } = useParams();
	const dispatch = useDispatch();
	const appUserRolesData = useSelector(selectAppUserRolesData);
	const triggerApi = useApi();

	const twoFactorMethodOptions = [
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
	let initialValues = {
		name: '',
		policies: [],
		two_factor_auth: {
			required: false,
			allowedMethods: ['email'],
		},
		password_policy: {
			min_length: 8,
			require_numbers: true,
			require_lowercase: true,
			require_uppercase: true,
			require_special_chars: true,
			password_expiry_days: 90,
			password_history_count: 3,
		},
	};

	let validationSchema = Yup.object({
		name: Yup.string().required('Required'),
		two_factor_auth: Yup.object({
			required: Yup.boolean(),
			allowedMethods: Yup.array().min(1, 'At least one method is required'),
		}),
		password_policy: Yup.object({
			min_length: Yup.number().min(4, 'Minimum length must be at least 4').max(128, 'Maximum length is 128'),
			require_numbers: Yup.boolean(),
			require_lowercase: Yup.boolean(),
			require_uppercase: Yup.boolean(),
			require_special_chars: Yup.boolean(),
			password_expiry_days: Yup.number().min(1, 'Must be at least 1 day').max(365, 'Must be less than 365 days'),
			password_history_count: Yup.number().min(0, 'Cannot be negative').max(24, 'Maximum is 24'),
		}),
	});

	let onSubmit = (values) => {
		let tempValues = values;

		let dynamicFormData = transformToFormData(tempValues);

		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/roles/`,
				type: 'POST',
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
									name="two_factor_auth.required"
									value={get(formik.values, 'two_factor_auth.required', false)}
									onChange={(e) => formik.setFieldValue('two_factor_auth.required', e.target.checked)}
								>
									<MultiSelectChips
										name="two_factor_auth.allowedMethods"
										label="Allowed Methods"
										description="Select available methods for two-factor authentication"
										options={twoFactorMethodOptions}
										value={get(formik.values, 'two_factor_auth.allowedMethods', [])}
										onChange={(value) => formik.setFieldValue('two_factor_auth.allowedMethods', value)}
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
										key="password_policy.min_length"
										label="Minimum Length"
										name="password_policy.min_length"
										id="password_policy.min_length"
										type="number"
										placeholder="8"
										value={get(formik.values, 'password_policy.min_length', 8)}
										onChange={formik.handleChange}
										formik={formik}
									/>
									<InputField
										key="password_policy.password_expiry_days"
										label="Password Expiry (Days)"
										name="password_policy.password_expiry_days"
										id="password_policy.password_expiry_days"
										type="number"
										placeholder="90"
										value={get(formik.values, 'password_policy.password_expiry_days', 90)}
										onChange={formik.handleChange}
										formik={formik}
									/>
								</div>
								<div className="grid grid-cols-2 gap-[12px]">
									<ToggleCard
										title="Require Numbers"
										description="Passwords must contain numbers"
										name="password_policy.require_numbers"
										value={get(formik.values, 'password_policy.require_numbers', true)}
										onChange={(e) => formik.setFieldValue('password_policy.require_numbers', e.target.checked)}
									/>
									<ToggleCard
										title="Require Uppercase"
										description="Passwords must contain uppercase letters"
										name="password_policy.require_uppercase"
										value={get(formik.values, 'password_policy.require_uppercase', true)}
										onChange={(e) => formik.setFieldValue('password_policy.require_uppercase', e.target.checked)}
									/>
								</div>
								<div className="grid grid-cols-2 gap-[12px]">
									<ToggleCard
										title="Require Lowercase"
										description="Passwords must contain lowercase letters"
										name="password_policy.require_lowercase"
										value={get(formik.values, 'password_policy.require_lowercase', true)}
										onChange={(e) => formik.setFieldValue('password_policy.require_lowercase', e.target.checked)}
									/>
									<ToggleCard
										title="Require Special Characters"
										description="Passwords must contain special characters"
										name="password_policy.require_special_chars"
										value={get(formik.values, 'password_policy.require_special_chars', true)}
										onChange={(e) => formik.setFieldValue('password_policy.require_special_chars', e.target.checked)}
									/>
								</div>
								<InputField
									key="password_policy.password_history_count"
									label="Password History Count"
									name="password_policy.password_history_count"
									id="password_policy.password_history_count"
									type="number"
									placeholder="3"
									value={get(formik.values, 'password_policy.password_history_count', 3)}
									onChange={formik.handleChange}
									formik={formik}
								/>
							</div>
						</div>
						<div className="sticky bottom-0 flex flex-col gap-[8px] bg-[#ffffff] pt-[24px] font-lato text-[#696969]">
							<SubmitButton label={'Create User Role'} formik={formik} />
						</div>
					</form>
				);
			}}
		</Formik>
	);
};

export default AddNewUserRolesForm;
