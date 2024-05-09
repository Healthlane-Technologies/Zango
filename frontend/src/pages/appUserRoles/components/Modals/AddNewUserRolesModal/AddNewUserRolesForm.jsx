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
import { selectAppUserRolesData, toggleRerenderPage } from '../../../slice';

const AddNewUserRolesForm = ({ closeModal }) => {
	let { appId } = useParams();
	const dispatch = useDispatch();
	const appUserRolesData = useSelector(selectAppUserRolesData);
	const triggerApi = useApi();
	let initialValues = {
		name: '',
		policies: [],
	};

	let validationSchema = Yup.object({
		name: Yup.string().required('Required'),
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
