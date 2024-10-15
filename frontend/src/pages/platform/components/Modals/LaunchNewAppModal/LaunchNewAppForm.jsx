import { Formik } from 'formik';
import { get } from 'lodash';
import { useDispatch } from 'react-redux';
import * as Yup from 'yup';
import InputField from '../../../../../components/Form/InputField';
import SubmitButton from '../../../../../components/Form/SubmitButton';
import TextareaField from '../../../../../components/Form/TextareaField';
import useApi from '../../../../../hooks/useApi';
import { transformToFormDataOrder } from '../../../../../utils/form';
import { setPollingTastIds, toggleRerenderPage } from '../../../slice';

const LaunchNewAppForm = ({ closeModal }) => {
	const dispatch = useDispatch();
	const triggerApi = useApi();

	let initialValues = {
		name: '',
		description: '',
	};

	let validationSchema = Yup.object({
		name: Yup.string()
			.required('Required')
			.test('no-spaces', 
					'App name cannot contain spaces',
					value => !/\s/.test(value)),
		description: Yup.string().required('Required'),
	});

	const makeApiCall = async (dynamicFormData) => {
		const { response, success } = await triggerApi({
			url: `/api/v1/apps/`,
			type: 'POST',
			loader: true,
			notify: true,
			payload: dynamicFormData,
		});

		if (success && response) {
			dispatch(setPollingTastIds(response?.task_id));
			closeModal();
			dispatch(toggleRerenderPage());
		}
	};

	let onSubmit = (values) => {
		let tempValues = values;
		let dynamicFormData = transformToFormDataOrder(tempValues);

		makeApiCall(dynamicFormData);
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
								label="App Name"
								name="name"
								id="name"
								placeholder="Enter"
								value={get(formik.values, 'name', '')}
								onChange={formik.handleChange}
								formik={formik}
							/>
							<TextareaField
								key="description"
								label="Description"
								name="description"
								id="description"
								placeholder="Enter"
								value={get(formik.values, 'description', '')}
								onChange={formik.handleChange}
								formik={formik}
							/>
						</div>
						<div className="sticky bottom-0 flex flex-col gap-[8px] bg-[#ffffff] pt-[24px] font-lato text-[#696969]">
							<SubmitButton label={'Launch App'} formik={formik} />
						</div>
					</form>
				);
			}}
		</Formik>
	);
};

export default LaunchNewAppForm;
