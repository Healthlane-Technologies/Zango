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
	selectAppUserRolesData,
	selectAppUserRolesFormData,
	toggleRerenderPage,
} from '../../../slice';

const EditUserRolesDetailsForm = ({ closeModal }) => {
	let { appId } = useParams();
	const dispatch = useDispatch();

	const appUserRolesData = useSelector(selectAppUserRolesData);
	const appUserRolesFormData = useSelector(selectAppUserRolesFormData);

	const triggerApi = useApi();
	let initialValues = {
		name: appUserRolesFormData?.name ?? '',
		policies:
			appUserRolesFormData?.attached_policies?.map((eachApp) => eachApp.id) ??
			[],
	};

	let validationSchema = Yup.object({
		name: Yup.string().required('Required'),
	});

	let onSubmit = (values) => {
		let tempValues = values;

		let dynamicFormData = transformToFormData(tempValues);

		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/roles/${appUserRolesFormData?.id}/`,
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

export default EditUserRolesDetailsForm;
