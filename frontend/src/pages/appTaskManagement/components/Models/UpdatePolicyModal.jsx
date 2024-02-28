import { Dialog, Transition } from '@headlessui/react';
import Editor from '@monaco-editor/react';
import { Formik } from 'formik';
import { get } from 'lodash';
import { Fragment, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import * as Yup from 'yup';
import { ReactComponent as ModalCloseIcon } from '../../../../assets/images/svg/modal-close-icon.svg';
import CheckboxField from '../../../../components/Form/CheckboxField';
import MultiSelectField from '../../../../components/Form/MultiSelectField';
import useApi from '../../../../hooks/useApi';
import { transformToFormDataOrder } from '../../../../utils/helper';
import {
	closeIsUpdatePolicyModalOpen,
	selectAppTaskManagementData,
	selectAppTaskManagementFormData,
	selectIsUpdatePolicyModalOpen,
	toggleRerenderPage,
} from '../../slice';

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
									<div className="flex flex-col gap-[4px]">
										<label
											htmlFor="minute"
											className="font-lato text-form-xs font-semibold text-[#A3ABB1]"
										>
											Minute
										</label>
										<input
											id="minute"
											name="minute"
											type="text"
											onChange={formik.handleChange}
											onBlur={formik.handleBlur}
											value={formik.values.minute}
											className="rounded-[6px] border border-[#DDE2E5] px-[16px] py-[14px] font-lato placeholder:text-[#9A9A9A] hover:outline-0 focus:outline-0"
											placeholder="Enter"
										/>
										{formik.touched.minute && formik.errors.minute ? (
											<div className="font-lato text-form-xs text-[#cc3300]">
												{formik.errors.minute}
											</div>
										) : null}
									</div>
									<div className="flex flex-col gap-[4px]">
										<label
											htmlFor="hour"
											className="font-lato text-form-xs font-semibold text-[#A3ABB1]"
										>
											Hour
										</label>
										<input
											id="hour"
											name="hour"
											type="text"
											onChange={formik.handleChange}
											onBlur={formik.handleBlur}
											value={formik.values.hour}
											className="rounded-[6px] border border-[#DDE2E5] px-[16px] py-[14px] font-lato placeholder:text-[#9A9A9A] hover:outline-0 focus:outline-0"
											placeholder="Enter"
										/>
										{formik.touched.hour && formik.errors.hour ? (
											<div className="font-lato text-form-xs text-[#cc3300]">
												{formik.errors.hour}
											</div>
										) : null}
									</div>
									<div className="flex flex-col gap-[4px]">
										<label
											htmlFor="day_of_week"
											className="font-lato text-form-xs font-semibold text-[#A3ABB1]"
										>
											Day of Week
										</label>
										<input
											id="day_of_week"
											name="day_of_week"
											type="text"
											onChange={formik.handleChange}
											onBlur={formik.handleBlur}
											value={formik.values.day_of_week}
											className="rounded-[6px] border border-[#DDE2E5] px-[16px] py-[14px] font-lato placeholder:text-[#9A9A9A] hover:outline-0 focus:outline-0"
											placeholder="Enter"
										/>
										{formik.touched.day_of_week && formik.errors.day_of_week ? (
											<div className="font-lato text-form-xs text-[#cc3300]">
												{formik.errors.day_of_week}
											</div>
										) : null}
									</div>
									<div className="flex flex-col gap-[4px]">
										<label
											htmlFor="day_of_month"
											className="font-lato text-form-xs font-semibold text-[#A3ABB1]"
										>
											Day of Month
										</label>
										<input
											id="day_of_month"
											name="day_of_month"
											type="text"
											onChange={formik.handleChange}
											onBlur={formik.handleBlur}
											value={formik.values.day_of_month}
											className="rounded-[6px] border border-[#DDE2E5] px-[16px] py-[14px] font-lato placeholder:text-[#9A9A9A] hover:outline-0 focus:outline-0"
											placeholder="Enter"
										/>
										{formik.touched.day_of_month &&
										formik.errors.day_of_month ? (
											<div className="font-lato text-form-xs text-[#cc3300]">
												{formik.errors.day_of_month}
											</div>
										) : null}
									</div>
									<div className="flex flex-col gap-[4px]">
										<label
											htmlFor="month_of_year"
											className="font-lato text-form-xs font-semibold text-[#A3ABB1]"
										>
											Month of Year
										</label>
										<input
											id="month_of_year"
											name="month_of_year"
											type="text"
											onChange={formik.handleChange}
											onBlur={formik.handleBlur}
											value={formik.values.month_of_year}
											className="rounded-[6px] border border-[#DDE2E5] px-[16px] py-[14px] font-lato placeholder:text-[#9A9A9A] hover:outline-0 focus:outline-0"
											placeholder="Enter"
										/>
										{formik.touched.month_of_year &&
										formik.errors.month_of_year ? (
											<div className="font-lato text-form-xs text-[#cc3300]">
												{formik.errors.month_of_year}
											</div>
										) : null}
									</div>
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
							<button
								type="submit"
								className="flex w-full items-center justify-center rounded-[4px] bg-primary px-[16px] py-[10px] font-lato text-[14px] font-bold leading-[20px] text-white disabled:opacity-[0.38]"
								// disabled={!(formik.isValid && formik.dirty)}
							>
								<span>Update Task</span>
							</button>
						</div>
					</form>
				);
			}}
		</Formik>
	);
};

export default function UpdatePolicyModal() {
	const isUpdatePolicyModalOpen = useSelector(selectIsUpdatePolicyModalOpen);
	const dispatch = useDispatch();

	function closeModal() {
		dispatch(closeIsUpdatePolicyModalOpen());
	}

	return (
		<>
			<Transition appear show={isUpdatePolicyModalOpen} as={Fragment}>
				<Dialog as="div" className="relative z-10" onClose={() => {}}>
					<Transition.Child
						as={Fragment}
						enter="ease-in-out duration-700"
						enterFrom="opacity-0"
						enterTo="opacity-100"
						leave="ease-in-out duration-700"
						leaveFrom="opacity-100"
						leaveTo="opacity-0"
					>
						<div className="fixed inset-0 bg-black bg-opacity-[.67]" />
					</Transition.Child>

					<Transition.Child
						as={Fragment}
						enter="transform transition ease-in-out duration-500"
						enterFrom="translate-x-full"
						enterTo="translate-x-0"
						leave="transform transition ease-in-out duration-500"
						leaveFrom="translate-x-0"
						leaveTo="translate-x-full"
					>
						<div className="fixed inset-0 overflow-y-auto">
							<div className="flex h-screen max-h-screen min-h-full grow items-center justify-center text-center md:justify-end">
								<Dialog.Panel className="relative flex h-screen max-h-screen min-h-full w-full max-w-[498px] transform flex-col gap-[32px] overflow-hidden bg-white px-[24px] pt-[52px] pb-[40px] text-left align-middle shadow-xl transition-all md:pl-[32px] md:pr-[72px] md:pt-[32px]">
									<div className="flex justify-end md:absolute md:top-0 md:right-0">
										<button
											type="button"
											className="flex justify-end focus:outline-none md:absolute md:top-[16px] md:right-[16px]"
											onClick={closeModal}
										>
											<ModalCloseIcon />
										</button>
									</div>
									<Dialog.Title as="div" className="flex flex-col gap-2">
										<div className="flex flex-col gap-[2px]">
											<h4 className="font-source-sans-pro text-[22px] font-semibold leading-[28px]">
												Update Task
											</h4>
										</div>
									</Dialog.Title>
									<UpdatePolicyForm closeModal={closeModal} />
								</Dialog.Panel>
							</div>
						</div>
					</Transition.Child>
				</Dialog>
			</Transition>
		</>
	);
}
