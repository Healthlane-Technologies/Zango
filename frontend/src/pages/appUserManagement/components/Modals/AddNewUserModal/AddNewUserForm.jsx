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
	toggleRerenderPage,
} from '../../../slice';
import CountryCodeSelector from '../../../../../components/Form/CountryCodeSelector';
import { useState , useLayoutEffect} from 'react';
import { countryCodeList } from '../../../../../utils/countryCodes';
import toast from 'react-hot-toast';
import Notifications from '../../../../../components/Notifications';

const AddNewUserForm = ({ closeModal }) => {
	const [countryCode,setCountryCode] = useState({
		name: 'India',
		dial_code: '+91',
		code: 'IN',
	})
	let { appId } = useParams();
	const dispatch = useDispatch();

	const appUserManagementData = useSelector(selectAppUserManagementData);
	const triggerApi = useApi();
	let pn_country_code = appUserManagementData?.pn_country_code ?? '+91'
	useLayoutEffect(()=>{
		let countryCodeObj = countryCodeList.find((c)=>c.dial_code===pn_country_code)
		setCountryCode(countryCodeObj)
	},[])
	let initialValues = {
		name: '',
		email: '',
		mobile: '',
		password: '',
		roles: [],
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
					.required('Required'),
			}),
			password: Yup.string().required('Required'),
			roles: Yup.array().min(1, 'Minimun one is required').required('Required'),
		},
		[
			['name'],
			['mobile', 'email'],
			['email', 'mobile'],
			['password'],
			['roles'],
		]
	);

	let onSubmit = (values) => {
		let tempValues = values
		if(values.mobile){
			tempValues = {...values,mobile:countryCode?.dial_code+values.mobile}
		}
		let dynamicFormData = transformToFormData(tempValues);

		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/users/`,
				type: 'POST',
				loader: true,
				payload: dynamicFormData,
			});

			if (success) {
				closeModal();
				dispatch(toggleRerenderPage());
			}
			else{
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
							<div data-cy="numeric_field" className="flex flex-col gap-[4px]">
								<label
									htmlFor="mobile"
									className="font-lato text-form-xs font-semibold text-[#A3ABB1]"
								>
									Mobile
								</label>
								<div className="flex gap-[12px] rounded-[6px] border border-[#DDE2E5] px-[12px]">
									<span className="font-lato text-[#6C747D]">
										<CountryCodeSelector countryCode={countryCode} setCountryCode={setCountryCode} />
									</span>
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
									<div data-cy="error_message" className="font-lato text-form-xs text-[#cc3300]">
										{formik.errors.mobile}
									</div>
								) : null}
							</div>
							<InputField
								key="password"
								label="Password"
								name="password"
								id="password"
								placeholder="Enter password"
								value={get(formik.values, 'password', '')}
								onChange={formik.handleChange}
								formik={formik}
								type="password"
							/>
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
							<SubmitButton label={'Add User'} formik={formik} />
						</div>
					</form>
				);
			}}
		</Formik>
	);
};

export default AddNewUserForm;
