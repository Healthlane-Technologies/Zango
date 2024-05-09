import { Formik } from 'formik';
import { get } from 'lodash';
import { useDispatch, useSelector } from 'react-redux';
import * as Yup from 'yup';
import InputField from '../../../../../components/Form/InputField';
import MultiSelectField from '../../../../../components/Form/MultiSelectField';
import SubmitButton from '../../../../../components/Form/SubmitButton';
import useApi from '../../../../../hooks/useApi';
import { transformToFormData } from '../../../../../utils/form';
import {
	selectPlatformUserManagementData,
	selectPlatformUserManagementFormData,
	toggleRerenderPage,
} from '../../../slice';

const EditUserDetailsForm = ({ closeModal }) => {
	const dispatch = useDispatch();
	const platformUserManagementData = useSelector(
		selectPlatformUserManagementData
	);

	const triggerApi = useApi();
	const platformUserManagementFormData = useSelector(
		selectPlatformUserManagementFormData
	);

	let initialValues = {
		name: platformUserManagementFormData?.name ?? '',
		email: platformUserManagementFormData?.email ?? '',
		apps:
			platformUserManagementFormData?.apps?.map((eachApp) => eachApp.uuid) ??
			[],
	};

	let validationSchema = Yup.object({
		name: Yup.string().required('Required'),
		email: Yup.string().email('Invalid email address').required('Required'),
		apps: Yup.array().min(1, 'Minimun one is required').required('Required'),
	});

	let onSubmit = (values) => {
		let tempValues = values;

		let dynamicFormData = transformToFormData(tempValues);

		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/auth/platform-users/${platformUserManagementFormData?.id}/`,
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
							<MultiSelectField
								key="apps"
								label="Apps Access"
								name="apps"
								id="apps"
								placeholder="Select app(s)"
								value={get(formik.values, 'apps', [])}
								optionsDataName="apps"
								optionsData={
									platformUserManagementData?.dropdown_options?.apps ?? []
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
