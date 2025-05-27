import { Formik } from 'formik';
import { get } from 'lodash';
import { useDispatch } from 'react-redux';
import { useParams } from 'react-router-dom';
import * as Yup from 'yup';
import InputField from '../../../../../components/Form/InputField';
import SubmitButton from '../../../../../components/Form/SubmitButton';
import useApi from '../../../../../hooks/useApi';
import { transformToFormData } from '../../../../../utils/form';
import { toggleRerenderPage } from '../../../slice/Index';

const AddSecretForm = ({ closeModal }) => {
	let { appId } = useParams();
	const dispatch = useDispatch();
	const triggerApi = useApi();

	let initialValues = {
		key: '',
		value: '',
	};

	let validationSchema = Yup.object().shape({
		key: Yup.string()
			.required('Required')
			.matches(/^[A-Z][a-z0-9_]*$/, 'Key must start with uppercase letter and can contain lowercase letters, numbers and underscores'),
		value: Yup.string().required('Required'),
	});

	let onSubmit = (values) => {
		let dynamicFormData = transformToFormData(values);

		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/secrets/`,
				type: 'POST',
				loader: true,
				payload: dynamicFormData,
			});

			if (success) {
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
								key="key"
								label="Key"
								name="key"
								id="key"
								placeholder="Enter secret key, e.g., Mysecret_key"
								value={get(formik.values, 'key', '')}
								onChange={formik.handleChange}
								formik={formik}
							/>
							<InputField
								key="value"
								label="Value"
								name="value"
								id="value"
								placeholder="Enter secret value"
								value={get(formik.values, 'value', '')}
								onChange={formik.handleChange}
								formik={formik}
							/>
						</div>
						<div className="sticky bottom-0 flex flex-col gap-[8px] bg-[#ffffff] pt-[24px] font-lato text-[#696969]">
							<SubmitButton label={'Add Secret'} formik={formik} />
						</div>
					</form>
				);
			}}
		</Formik>
	);
};

export default AddSecretForm;
