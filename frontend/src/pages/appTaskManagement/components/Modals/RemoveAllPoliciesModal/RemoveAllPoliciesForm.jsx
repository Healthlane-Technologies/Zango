import { Formik } from 'formik';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import * as Yup from 'yup';
import { ReactComponent as DeactivateUserRolesIcon } from '../../../../../assets/images/svg/deactivate-user-icon.svg';
import SubmitButton from '../../../../../components/Form/SubmitButton';
import useApi from '../../../../../hooks/useApi';
import { transformToFormDataOrder } from '../../../../../utils/form';
import {
	selectAppTaskManagementData,
	selectAppTaskManagementFormData,
	toggleRerenderPage,
} from '../../../slice';

const RemoveAllPoliciesForm = ({ closeModal }) => {
	const dispatch = useDispatch();
	const { appId } = useParams();

	const appTaskManagementFormData = useSelector(
		selectAppTaskManagementFormData
	);

	const triggerApi = useApi();
	let initialValues = {};

	let validationSchema = Yup.object({});

	let onSubmit = (values) => {
		let dynamicFormData = transformToFormDataOrder(values);

		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/tasks/${appTaskManagementFormData?.id}/`,
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
							<div className="flex grow flex-col items-center justify-center gap-[16px]">
								<DeactivateUserRolesIcon />
								<p className="max-w-[201px] text-center font-lato text-[16px] leading-[24px] tracking-[0.2px] text-[#212429]">
									Sure you want to remove all policies?
								</p>
							</div>
							<p className="flex flex-col font-lato text-[14px] leading-[20px] tracking-[0.2px] text-[#212429]">
								<span>Note:</span>
								<span>
									This will not delete the task but only remove all associated
									policies and can be added anytime later.
								</span>
							</p>
						</div>
						<div className="sticky bottom-0 flex flex-col gap-[8px] bg-[#ffffff] pt-[24px] font-lato text-[#696969]">
							<SubmitButton
								label={'Remove all Policies'}
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

export default RemoveAllPoliciesForm;
