import { Formik } from 'formik';
import { get } from 'lodash';
import { useDispatch, useSelector } from 'react-redux';
import * as Yup from 'yup';
import InputField from '../../../../../components/Form/InputField';
import SubmitButton from '../../../../../components/Form/SubmitButton';
import useApi from '../../../../../hooks/useApi';
import { transformToFormData } from '../../../../../utils/form';
import {
	selectPlatformUserManagementFormData,
	toggleRerenderPage,
} from '../../../slice';

const ResetPasswordForm = ({ closeModal }) => {
	const dispatch = useDispatch();
	const platformUserManagementFormData = useSelector(
		selectPlatformUserManagementFormData
	);

	const triggerApi = useApi();
	let initialValues = {
		password: '',
	};

	let validationSchema = Yup.object().shape({
		password: Yup.string().required('Required'),
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
				notify: true,
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
								key="password"
								label="Password"
								name="password"
								id="password"
								type="password"
								placeholder="Enter password"
								value={get(formik.values, 'password', '')}
								onChange={formik.handleChange}
								formik={formik}
							/>
						</div>
						<div className="sticky bottom-0 flex flex-col gap-[8px] bg-[#ffffff] pt-[24px] font-lato text-[#696969]">
							<SubmitButton label={'Reset Password'} formik={formik} />
						</div>
					</form>
				);
			}}
		</Formik>
	);
};

export default ResetPasswordForm;
