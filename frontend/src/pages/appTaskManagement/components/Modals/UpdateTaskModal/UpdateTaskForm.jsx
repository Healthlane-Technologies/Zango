import Editor from '@monaco-editor/react';
import { Formik } from 'formik';
import { get } from 'lodash';
import { useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import * as Yup from 'yup';
import CheckboxField from '../../../../../components/Form/CheckboxField';
import InputField from '../../../../../components/Form/InputField';
import MultiSelectField from '../../../../../components/Form/MultiSelectField';
import SubmitButton from '../../../../../components/Form/SubmitButton';
import useApi from '../../../../../hooks/useApi';
import { transformToFormDataOrder } from '../../../../../utils/form';
import {
	selectAppTaskManagementData,
	selectAppTaskManagementFormData,
	toggleRerenderPage,
} from '../../../slice';

const UpdatePolicyForm = ({ closeModal }) => {
	let { appId } = useParams();
	const appTaskManagementData = useSelector(selectAppTaskManagementData);

	const appTaskManagementFormData = useSelector(
		selectAppTaskManagementFormData
	);
	const dispatch = useDispatch();

	const editorRef = useRef(null);

	function handleEditorDidMount(editor, monaco) {
		editorRef.current = editor;
		setTimeout(function () {
			editor.getAction('editor.action.formatDocument').run();
		}, 100);
	}

	const triggerApi = useApi();
	let initialValues = {
		policies:
			appTaskManagementFormData?.attached_policies?.map(
				(eachApp) => eachApp.id
			) ?? [],
		kwargs: JSON.stringify(appTaskManagementFormData?.kwargs, null, 4),
		minute: appTaskManagementFormData?.crontab?.minute ?? '*',
		hour: appTaskManagementFormData?.crontab?.hour ?? '*',
		day_of_week: appTaskManagementFormData?.crontab?.day_of_week ?? '*',
		day_of_month: appTaskManagementFormData?.crontab?.day_of_month ?? '*',
		month_of_year: appTaskManagementFormData?.crontab?.month_of_year ?? '*',
		is_enabled: appTaskManagementFormData?.is_enabled ?? false,
	};

	let validationSchema = Yup.object({
		kwargs: Yup.string()
			.test('json', 'Invalid JSON format', (value) => {
				try {
					JSON.parse(value);
					return true;
				} catch (error) {
					return false;
				}
			})
			.required('Required'),
		minute: Yup.string().required('Required'),
		hour: Yup.string().required('Required'),
		day_of_week: Yup.string().required('Required'),
		day_of_month: Yup.string().required('Required'),
		month_of_year: Yup.string().required('Required'),
	});

	let onSubmit = (values) => {
		let crontab_exp = JSON.stringify({
			minute: values?.minute,
			hour: values?.hour,
			day_of_week: values?.day_of_week,
			day_of_month: values?.day_of_month,
			month_of_year: values?.month_of_year,
		});

		let tempValues = {
			policies: values?.policies,
			crontab_exp: crontab_exp,
			is_enabled: values?.is_enabled,
			kwargs: JSON.stringify(JSON.parse(values?.kwargs)),
		};

		let dynamicFormData = transformToFormDataOrder(tempValues);

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
						<div className="flex grow flex-col gap-[24px]">
							<div className="flex flex-col gap-[4px]">
								<table className="w-100 border-spacing-x-4">
									<tbody>
										<tr className="py-[4px] first:pb-[4px] last:pt-[4px]">
											<td className="align-baseline">
												<span className="whitespace-nowrap font-lato text-[14px] leading-[20px] tracking-[0.2px] text-[#A3ABB1]">
													Task Name:
												</span>
											</td>
											<td className="w-full pl-[16px]">
												<span className="whitespace-nowrap font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
													{appTaskManagementFormData?.name}
												</span>
											</td>
										</tr>
										<tr className="py-[4px] first:pb-[4px] last:pt-[4px]">
											<td className="align-baseline">
												<span className="whitespace-nowrap font-lato text-[14px] leading-[20px] tracking-[0.2px] text-[#A3ABB1]">
													Task ID:
												</span>
											</td>
											<td className="w-full pl-[16px]">
												<span className="whitespace-nowrap font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
													{appTaskManagementFormData?.id}
												</span>
											</td>
										</tr>
									</tbody>
								</table>
							</div>
							<MultiSelectField
								key="policies"
								label="Policy"
								name="policies"
								id="policies"
								placeholder="Select policies"
								value={get(formik.values, 'policies', [])}
								optionsDataName="policies"
								optionsData={
									appTaskManagementData?.dropdown_options?.policies ?? []
								}
								formik={formik}
							/>
							<div className="flex h-full min-h-[300px] flex-col gap-[4px]">
								<label
									htmlFor="kwargs"
									className="font-lato text-[12px] font-semibold text-[#A3ABB1]"
								>
									Kwargs
								</label>
								<div className="flex grow flex-col rounded-[6px] border border-[#DDE2E5] px-[16px] py-[14px] ">
									<Editor
										id="kwargs"
										height="100%"
										language="json"
										value={formik.values.kwargs}
										options={{
											readOnly: false,
											formatOnPaste: true,
											formatOnType: true,
										}}
										onMount={handleEditorDidMount}
										onChange={(value) => {
											formik.setFieldValue('kwargs', value);
										}}
									/>
								</div>
								{formik.touched.kwargs && formik.errors.kwargs ? (
									<div className="font-lato text-form-xs text-[#cc3300]">
										{formik.errors.kwargs}
									</div>
								) : null}
							</div>

							<div className="flex flex-col gap-[16px]">
								<h4 className="font-source-sans-pro text-[18px] font-semibold leading-[24px] tracking-[-0.2px] text-[#212429]">
									Schedule (UTC)
								</h4>
								<div className="grid grid-cols-2 gap-4">
									<InputField
										key="minute"
										label="Minute"
										name="minute"
										id="minute"
										placeholder="Enter"
										value={get(formik.values, 'minute', '')}
										onChange={formik.handleChange}
										formik={formik}
									/>
									<InputField
										key="hour"
										label="Hour"
										name="hour"
										id="hour"
										placeholder="Enter"
										value={get(formik.values, 'hour', '')}
										onChange={formik.handleChange}
										formik={formik}
									/>
									<InputField
										key="day_of_week"
										label="Day of Week"
										name="day_of_week"
										id="day_of_week"
										placeholder="Enter"
										value={get(formik.values, 'day_of_week', '')}
										onChange={formik.handleChange}
										formik={formik}
									/>
									<InputField
										key="day_of_month"
										label="Day of Month"
										name="day_of_month"
										id="day_of_month"
										placeholder="Enter"
										value={get(formik.values, 'day_of_month', '')}
										onChange={formik.handleChange}
										formik={formik}
									/>
									<InputField
										key="month_of_year"
										label="Month of Year"
										name="month_of_year"
										id="month_of_year"
										placeholder="Enter"
										value={get(formik.values, 'month_of_year', '')}
										onChange={formik.handleChange}
										formik={formik}
									/>
								</div>
							</div>
							<CheckboxField
								key="is_enabled"
								label="Is Enabled"
								content=""
								name="is_enabled"
								id="is_enabled"
								placeholder=""
								value={get(formik.values, 'is_enabled', '')}
								onChange={formik.handleChange}
								formik={formik}
							/>
						</div>
						<div className="sticky bottom-0 flex flex-col gap-[8px] bg-[#ffffff] pt-[24px] font-lato text-[#696969]">
							<SubmitButton
								label={'Update Task'}
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

export default UpdatePolicyForm;
