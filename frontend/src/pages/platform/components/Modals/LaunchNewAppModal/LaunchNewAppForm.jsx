import { Formik } from 'formik';
import { get } from 'lodash';
import { useDispatch } from 'react-redux';
import * as Yup from 'yup';
import InputField from '../../../../../components/Form/InputField';
import SubmitButton from '../../../../../components/Form/SubmitButton';
import TextareaField from '../../../../../components/Form/TextareaField';
import FileUpload from '../../../../../components/Form/FileUpload';
import useApi from '../../../../../hooks/useApi';
import { transformToFormDataOrder } from '../../../../../utils/form';
import { setPollingTastIds, toggleRerenderPage } from '../../../slice';

const LaunchNewAppForm = ({ closeModal }) => {
	const dispatch = useDispatch();
	const triggerApi = useApi();

	let initialValues = {
		name: '',
		description: '',
		app_template: null
	};

	let validationSchema = Yup.object().shape({
		name: Yup.string(),
		description: Yup.string(),
		app_template: Yup.mixed().test('fileType', 'Only ZIP files are allowed', (value) => {
			if (value) {
				const fileType = value.type;
				return fileType === 'application/zip' || fileType === 'application/x-zip-compressed';
			}
			return true; 
		}),
	  	}).test('custom', null, function(value) {
		if (value.app_template) {
		  return true; 
		}
		
		if (!value.name && !value.description) {
		  return this.createError({
			path: 'app_template',
			message: 'Required',
		  });
		}
		
		if (value.name && !value.description) {
		  return this.createError({
			path: 'description',
			message: 'Required',
		  });
		}
		
		if (!value.name && value.description) {
		  return this.createError({
			path: 'name',
			message: 'Required',
		  });
		}
		
		return true;
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
							<div className='w-full flex my-4'>
								<div className="w-full flex items-center">
      							<div className="flex-grow h-px bg-[#A3ABB1]"></div>
      							<p className="mx-4 text-sm text-[#A3ABB1] font-medium">OR</p>
      							<div className="flex-grow h-px bg-[#A3ABB1]"></div>
    							</div>						
							</div>
							<FileUpload
								formik={formik}
								label={'Template'}
								id={'app_template'}
								fileValue={null}
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
