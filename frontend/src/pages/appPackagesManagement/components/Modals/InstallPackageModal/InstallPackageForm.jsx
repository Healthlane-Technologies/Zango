import { Formik } from 'formik';
import { get } from 'lodash';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import * as Yup from 'yup';
import InputField from '../../../../../components/Form/InputField';
import SelectField from '../../../../../components/Form/SelectField';
import SubmitButton from '../../../../../components/Form/SubmitButton';
import useApi from '../../../../../hooks/useApi';
import { transformToFormData } from '../../../../../utils/form';
import {
	selectAppPackagesManagementFormData,
	toggleRerenderPage,
} from '../../../slice';

const InstallPackageForm = ({ closeModal }) => {
	let { appId } = useParams();
	const dispatch = useDispatch();

	const appPackagesManagementFormData = useSelector(
		selectAppPackagesManagementFormData
	);

	const triggerApi = useApi();

	let initialValues = {
		name: appPackagesManagementFormData?.name ?? '',
		version: '',
	};

	let validationSchema = Yup.object({
		name: Yup.string().required('Required'),
		version: Yup.string().required('Required'),
	});

	let onSubmit = (values) => {
		let tempValues = values;
		let dynamicFormData = transformToFormData(tempValues);

		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/packages/?action=install`,
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
						<div className="flex grow flex-col gap-[24px]">
							<InputField
								key="name"
								label="Package Name"
								name="name"
								id="name"
								placeholder="Enter"
								value={get(formik.values, 'name', '')}
								onChange={formik.handleChange}
								formik={formik}
								disabled={true}
							/>
							<SelectField
								key="version"
								label="Version"
								name="version"
								id="version"
								placeholder="Select version"
								value={get(formik.values, 'version', '')}
								optionsDataName="version"
								optionsData={
									appPackagesManagementFormData?.versions?.map(
										(eachVersion) => {
											return { id: eachVersion, label: eachVersion };
										}
									) ?? []
								}
								formik={formik}
							/>
						</div>
						<div className="sticky bottom-0 flex flex-col gap-[8px] bg-[#ffffff] pt-[24px] font-lato text-[#696969]">
							<SubmitButton label={'Install Package'} formik={formik} />
						</div>
					</form>
				);
			}}
		</Formik>
	);
};

export default InstallPackageForm;
