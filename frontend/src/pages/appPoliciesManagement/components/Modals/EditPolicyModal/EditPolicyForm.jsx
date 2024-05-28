import { Formik } from 'formik';
import { get } from 'lodash';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import * as Yup from 'yup';
import InputField from '../../../../../components/Form/InputField';
import MultiSelectField from '../../../../../components/Form/MultiSelectField';
import SubmitButton from '../../../../../components/Form/SubmitButton';
import TextareaField from '../../../../../components/Form/TextareaField';
import useApi from '../../../../../hooks/useApi';
import { transformToFormData } from '../../../../../utils/form';
import {
	selectAppPoliciesManagementData,
	selectAppPoliciesManagementFormData,
	toggleRerenderPage,
} from '../../../slice';

const EditPolicyForm = ({ closeModal }) => {
	let { appId } = useParams();
	const dispatch = useDispatch();

	const appPoliciesManagementData = useSelector(
		selectAppPoliciesManagementData
	);

	const appPoliciesManagementFormData = useSelector(
		selectAppPoliciesManagementFormData
	);

	const triggerApi = useApi();
	let initialValues = {
		name: appPoliciesManagementFormData?.name ?? '',
		description: appPoliciesManagementFormData?.description ?? '',
		roles:
			appPoliciesManagementFormData?.roles?.map(({ id, name }) => {
				return id;
			}) ?? [],
	};

	let validationSchema = Yup.object({
		name: Yup.string().required('Required'),
		description: Yup.string().required('Required'),
	});

	let onSubmit = (values) => {
		let tempValues = values;
		if (tempValues['phone']) {
			tempValues['phone'] = '+91' + tempValues['phone'];
		}

		let dynamicFormData = transformToFormData(tempValues);

		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/policies/${appPoliciesManagementFormData?.id}/`,
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
							<div className="flex grow flex-col gap-[24px]">
								<InputField
									key="name"
									label="Policy Name"
									name="name"
									id="name"
									placeholder="Enter policy name"
									value={get(formik.values, 'name', '')}
									onChange={formik.handleChange}
									formik={formik}
									disabled={true}
								/>
								<TextareaField
									key="description"
									label="Policy Description"
									name="description"
									id="description"
									placeholder="Enter policy description"
									value={get(formik.values, 'description', '')}
									onChange={formik.handleChange}
									formik={formik}
									disabled={true}
								/>
								<MultiSelectField
									key="roles"
									label="Roles"
									name="roles"
									id="roles"
									placeholder="Select roles"
									value={get(formik.values, 'roles', [])}
									optionsDataName="roles"
									optionsData={
										appPoliciesManagementData?.dropdown_options?.roles ?? []
									}
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

export default EditPolicyForm;
