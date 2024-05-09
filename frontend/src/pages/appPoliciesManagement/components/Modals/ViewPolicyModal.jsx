import { Dialog, Transition } from '@headlessui/react';
import Editor from '@monaco-editor/react';
import { Formik } from 'formik';
import { Fragment, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import * as Yup from 'yup';
import { ReactComponent as ModalCloseIcon } from '../../../../assets/images/svg/modal-close-icon.svg';
import useApi from '../../../../hooks/useApi';
import { transformToFormDataStringify } from '../../../../utils/form';
import {
	closeIsViewPolicyModalOpen,
	selectAppPoliciesManagementFormData,
	selectIsEditViewPolicy,
	selectIsViewPolicyModalOpen,
	toggleIsEditViewPolicy,
	toggleRerenderPage,
} from '../../slice';

const ViewPolicyForm = ({ closeModal }) => {
	const appPoliciesManagementFormData = useSelector(
		selectAppPoliciesManagementFormData
	);
	return (
		<div className="complete-hidden-scroll-style flex grow flex-col gap-4 overflow-y-auto">
			<div className="flex grow flex-col gap-[24px]">
				<div className="flex grow flex-col gap-[24px]">
					<pre className="font-lato text-[14px] leading-[20px] tracking-[0.2px] text-[#212429]">
						{JSON.stringify(appPoliciesManagementFormData?.statement, null, 4)}
					</pre>
				</div>
			</div>
			<div className="sticky bottom-0 flex flex-col  items-end gap-[8px] bg-[#ffffff] pt-[24px] font-lato text-[#696969]">
				<button
					type="button"
					className="flex w-fit items-center justify-center rounded-[4px] bg-primary px-[16px] py-[10px] font-lato text-[14px] font-bold leading-[20px] text-white disabled:opacity-[0.38]"
					onClick={closeModal}
				>
					<span>Done</span>
				</button>
			</div>
		</div>
	);
};

const EditPolicyConfigure = ({ closeModal }) => {
	let { appId } = useParams();
	const dispatch = useDispatch();

	const appPoliciesManagementFormData = useSelector(
		selectAppPoliciesManagementFormData
	);

	const editorRef = useRef(null);

	function handleEditorDidMount(editor, monaco) {
		editorRef.current = editor;
		setTimeout(function () {
			editor.getAction('editor.action.formatDocument').run();
		}, 100);
	}

	const triggerApi = useApi();
	let initialValues = {
		statement: JSON.stringify(
			appPoliciesManagementFormData?.statement,
			null,
			4
		),
	};

	let validationSchema = Yup.object({
		statement: Yup.string().required('Required'),
	});

	let onSubmit = (values) => {
		let tempValues = values;
		tempValues['statement'] = JSON.parse(values.statement);

		let dynamicFormData = transformToFormDataStringify(tempValues);

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
							<Editor
								height="100%"
								language="json"
								value={formik.values.statement}
								options={{
									readOnly: false,
									formatOnPaste: true,
									formatOnType: true,
								}}
								onMount={handleEditorDidMount}
								onChange={(value) => {
									formik.setFieldValue('statement', value);
								}}
							/>
						</div>

						<div className="sticky bottom-0 flex items-center justify-end gap-[8px] bg-[#ffffff] pt-[24px] font-lato text-[#696969]">
							<button
								type="button"
								className="flex w-fit items-center justify-center rounded-[4px] border border-primary bg-[#ffffff] px-[16px] py-[10px] font-lato text-[14px] font-bold leading-[20px] text-primary disabled:opacity-[0.38]"
								onClick={closeModal}
							>
								<span>Cancel</span>
							</button>
							<button
								type="submit"
								className="flex w-fit items-center justify-center rounded-[4px] bg-primary px-[16px] py-[10px] font-lato text-[14px] font-bold leading-[20px] text-white disabled:opacity-[0.38]"
							>
								<span>Save</span>
							</button>
						</div>
					</form>
				);
			}}
		</Formik>
	);
};

export default function ViewPolicyModal() {
	const isViewPolicyModalOpen = useSelector(selectIsViewPolicyModalOpen);
	const isEditViewPolicy = useSelector(selectIsEditViewPolicy);
	const dispatch = useDispatch();

	const appPoliciesManagementFormData = useSelector(
		selectAppPoliciesManagementFormData
	);

	function closeModal() {
		dispatch(closeIsViewPolicyModalOpen());
	}

	function handleEditJson() {
		dispatch(toggleIsEditViewPolicy());
	}

	return (
		<>
			<Transition appear show={isViewPolicyModalOpen} as={Fragment}>
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
								<Dialog.Panel className="relative flex h-screen max-h-screen min-h-full w-full max-w-[1001px] transform flex-col gap-[32px] overflow-hidden bg-white px-[24px] pb-[40px] pt-[52px] text-left align-middle shadow-xl transition-all md:pl-[32px] md:pr-[32px] md:pt-[32px]">
									<div className="flex justify-end md:absolute md:right-0 md:top-0">
										<button
											type="button"
											className="flex justify-end focus:outline-none md:absolute md:right-[16px] md:top-[16px]"
											onClick={closeModal}
										>
											<ModalCloseIcon />
										</button>
									</div>
									<Dialog.Title as="div" className="flex flex-col gap-2">
										<div className="flex items-end gap-[16px]">
											<h4 className="font-source-sans-pro text-[22px] font-semibold leading-[28px]">
												{appPoliciesManagementFormData?.name}
											</h4>
											{/* {isEditViewPolicy ? null : (
												<button
													type="button"
													onClick={handleEditJson}
													disabled={
														appPoliciesManagementFormData?.type === 'system'
															? true
															: false
													}
													className="disabled:opacity-50"
												>
													<span className="font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-primary ">
														Edit JSON
													</span>
												</button>
											)} */}
										</div>
									</Dialog.Title>
									{isEditViewPolicy ? (
										<EditPolicyConfigure closeModal={closeModal} />
									) : (
										<ViewPolicyForm closeModal={closeModal} />
									)}
								</Dialog.Panel>
							</div>
						</div>
					</Transition.Child>
				</Dialog>
			</Transition>
		</>
	);
}
