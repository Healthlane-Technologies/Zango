import { Formik } from 'formik';
import { get } from 'lodash';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import * as Yup from 'yup';
import InputField from '../../../../../components/Form/InputField';
import MultiSelectField from '../../../../../components/Form/MultiSelectField';
import SubmitButton from '../../../../../components/Form/SubmitButton';
import useApi from '../../../../../hooks/useApi';
import { transformToFormData } from '../../../../../utils/form';
import {
	selectAppUserManagementData,
	selectAppUserManagementFormData,
	toggleRerenderPage,
} from '../../../slice';

const EditUserDetailsForm = ({ closeModal }) => {
	let { appId } = useParams();
	const dispatch = useDispatch();

	const appUserManagementData = useSelector(selectAppUserManagementData);
	const appUserManagementFormData = useSelector(
		selectAppUserManagementFormData
	);

	const triggerApi = useApi();
	let initialValues = {
		name: appUserManagementFormData?.name ?? '',
		email: appUserManagementFormData?.email ?? '',
		mobile: appUserManagementFormData?.mobile
			? appUserManagementFormData?.mobile.indexOf('+91') > -1
				? appUserManagementFormData?.mobile?.slice(3) ?? ''
				: appUserManagementFormData?.mobile
			: '',
		roles: appUserManagementFormData?.roles?.map((eachApp) => eachApp.id) ?? [],
	};

	let validationSchema = Yup.object().shape(
		{
			name: Yup.string().required('Required'),
			email: Yup.string().when(['mobile'], {
				is: (mobile) => {
					if (!mobile) return true;
				},
				then: Yup.string().email('Invalid email address').required('Required'),
				otherwise: Yup.string(),
			}),
			mobile: Yup.string().when(['email'], {
				is: (email) => {
					if (!email) return true;
				},
				then: Yup.string()
					.min(10, 'Must be 10 digits')
					.max(10, 'Must be 10 digits')
					.required('Required'),
				otherwise: Yup.string()
					.min(10, 'Must be 10 digits')
					.max(10, 'Must be 10 digits'),
			}),
			roles: Yup.array().min(1, 'Minimun one is required').required('Required'),
		},
		[['name'], ['mobile', 'email'], ['email', 'mobile'], ['roles']]
	);

	let onSubmit = (values) => {
		let tempValues = values;

		let dynamicFormData = transformToFormData(tempValues);

		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/users/${appUserManagementFormData?.id}/`,
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
								label="Full Name"
								name="name"
								id="name"
								placeholder="Enter full name of the user"
								value={get(formik.values, 'name', '')}
								onChange={formik.handleChange}
								formik={formik}
							/>
							<InputField
								key="email"
								label="Email"
								name="email"
								id="email"
								placeholder="Enter"
								value={get(formik.values, 'email', '')}
								onChange={formik.handleChange}
								formik={formik}
							/>
							<div className="flex flex-col gap-[4px]">
								<label
									htmlFor="mobile"
									className="font-lato text-form-xs font-semibold text-[#A3ABB1]"
								>
									Mobile
								</label>
								<div className="flex gap-[12px] rounded-[6px] border border-[#DDE2E5] px-[12px] py-[14px]">
									<span className="font-lato text-[#6C747D]">+91</span>
									<input
										id="mobile"
										name="mobile"
										type="number"
										onChange={formik.handleChange}
										onBlur={formik.handleBlur}
										value={formik.values.mobile}
										className="font-lato placeholder:text-[#9A9A9A] hover:outline-0 focus:outline-0"
										placeholder="00000 00000"
									/>
								</div>
								{formik.touched.mobile && formik.errors.mobile ? (
									<div className="font-lato text-form-xs text-[#cc3300]">
										{formik.errors.mobile}
									</div>
								) : null}
							</div>
							<MultiSelectField
								key="roles"
								label="User Role"
								name="roles"
								id="roles"
								placeholder="Select roles"
								value={get(formik.values, 'roles', [])}
								optionsDataName="roles"
								optionsData={
									appUserManagementData?.dropdown_options?.roles ?? []
								}
								formik={formik}
							/>
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

export default EditUserDetailsForm;
