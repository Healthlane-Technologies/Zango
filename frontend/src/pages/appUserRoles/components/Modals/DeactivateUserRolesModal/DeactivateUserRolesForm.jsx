import { Formik } from 'formik';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import * as Yup from 'yup';
import { ReactComponent as DeactivateUserRolesIcon } from '../../../../../assets/images/svg/deactivate-user-icon.svg';
import SubmitButton from '../../../../../components/Form/SubmitButton';
import useApi from '../../../../../hooks/useApi';
import { transformToFormDataOrder } from '../../../../../utils/form';
import { selectAppUserRolesFormData, toggleRerenderPage } from '../../../slice';

const DeactivateUserRolesForm = ({ closeModal }) => {
	let { appId } = useParams();
	const dispatch = useDispatch();

	const appUserRolesFormData = useSelector(selectAppUserRolesFormData);

	const triggerApi = useApi();
	let initialValues = {
		is_active: false,
	};

	let validationSchema = Yup.object({
		is_active: Yup.boolean()
			.required('Required')
			.oneOf([false], 'Deactivate User'),
	});

	let onSubmit = (values) => {
		let tempValues = values;

		let dynamicFormData = transformToFormDataOrder(tempValues);

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
							<div className="flex grow flex-col items-center justify-center gap-[16px]">
								<DeactivateUserRolesIcon />
								<p className="max-w-[201px] text-center font-lato text-[16px] leading-[24px] tracking-[0.2px] text-[#212429]">
									Sure you want to deactivate {appUserRolesFormData?.name}?
								</p>
							</div>
							<p className="flex flex-col font-lato text-[14px] leading-[20px] tracking-[0.2px] text-[#212429]">
								<span>Note:</span>
								<span>
									This will not delete the user role but only disable it and can
									be enabled anytime later.
								</span>
							</p>
						</div>
						<div className="sticky bottom-0 flex flex-col gap-[8px] bg-[#ffffff] pt-[24px] font-lato text-[#696969]">
							<SubmitButton
								label={'Deactivate User Role'}
								formik={formik}
								allowDisabled={false}
								theme="danger"
							/>
						</div>
					</form>
				);
			}}
		</Formik>
	);
};

export default DeactivateUserRolesForm;
