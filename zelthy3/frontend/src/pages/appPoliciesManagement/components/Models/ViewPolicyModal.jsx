import { Dialog, Transition } from '@headlessui/react';
import { Fragment, useState, useEffect } from 'react';

import { useField, Formik, FieldArray, Field, ErrorMessage } from 'formik';
import * as Yup from 'yup';
import { get } from 'lodash';
import { transformToFormDataOrder } from '../../../../utils/helper';
import useApi from '../../../../hooks/useApi';

import { useSelector, useDispatch } from 'react-redux';
import {
	closeIsViewPolicyModalOpen,
	selectIsViewPolicyModalOpen,
} from '../../slice';

import { ReactComponent as ModalCloseIcon } from '../../../../assets/images/svg/modal-close-icon.svg';

import Editor, { loader } from '@monaco-editor/react';
import { useRef } from 'react';

const ViewPolicyForm = ({ closeModal }) => {
	const triggerApi = useApi();
	let initialValues = {
		full_name: '',
		email: '',
		phone: '',
	};

	let validationSchema = Yup.object({
		full_name: Yup.string().required('Required'),
		email: Yup.string().email('Invalid email address').required('Required'),
		phone: Yup.string()
			.min(9, 'Must be 9 digits')
			.max(9, 'Must be 9 digits')
			.required('Required'),
	});

	let onSubmit = (values) => {
		let tempValues = values;
		if (tempValues['phone']) {
			tempValues['phone'] = '+91' + tempValues['phone'];
		}

		let dynamicFormData = transformToFormDataOrder(tempValues);

		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/generate-order/`,
				type: 'POST',
				loader: true,
				payload: dynamicFormData,
			});

			if (success && response) {
				closeModal();
			}
		};

		makeApiCall();
	};

	return (
		<div className="complete-hidden-scroll-style flex grow flex-col gap-4 overflow-y-auto">
			<div className="flex grow flex-col gap-[24px]">
				<div className="flex grow flex-col gap-[24px]">
					<div className="font-lato text-[14px] leading-[20px] tracking-[0.2px] text-[#212429]">
						{
							'{    permissions: [    { type: "dataModel",        name: "patient",        actions: ["view", "edit"],        attributes: {only: ["Field 1", "Field 2"]},        records: {filter: object.clinic == currentUser.clinic},        accessTime: "9:00-17:00"    }],    configurations: {        expiry: "26/12/23"}'
						}
					</div>
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
	const editorRef = useRef(null);

	function handleEditorDidMount(editor, monaco) {
		editorRef.current = editor;
		setTimeout(function () {
			editor.getAction('editor.action.formatDocument').run();
		}, 100);
	}

	const code = JSON.stringify({
		permissions: [
			{
				type: 'dataModel',
				name: 'patient',
				actions: ['view', 'edit'],
				attributes: { only: ['Field 1', 'Field 2'] },
				records: { filter: 'object.clinic == currentUser.clinic' },
				accessTime: '9:00-17:00',
			},
		],
		configurations: { expiry: '26/12/23' },
	});
	return (
		<div className="complete-hidden-scroll-style flex grow flex-col gap-4 overflow-y-auto">
			<div className="flex grow flex-col gap-[24px]">
				<Editor
					height="100%"
					language="json"
					value={code}
					options={{
						readOnly: false,
						formatOnPaste: true,
						formatOnType: true,
					}}
					onMount={handleEditorDidMount}
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
					type="button"
					className="flex w-fit items-center justify-center rounded-[4px] bg-primary px-[16px] py-[10px] font-lato text-[14px] font-bold leading-[20px] text-white disabled:opacity-[0.38]"
					onClick={closeModal}
				>
					<span>Save</span>
				</button>
			</div>
		</div>
	);
};

export default function ViewPolicyModal() {
	const isViewPolicyModalOpen = useSelector(selectIsViewPolicyModalOpen);
	const dispatch = useDispatch();

	function closeModal() {
		dispatch(closeIsViewPolicyModalOpen());
	}

	return (
		<>
			<Transition appear show={isViewPolicyModalOpen} as={Fragment}>
				<Dialog as="div" className="relative z-10" onClose={closeModal}>
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
								<Dialog.Panel className="relative flex h-screen max-h-screen min-h-full w-full max-w-[1001px] transform flex-col gap-[32px] overflow-hidden bg-white px-[24px] pt-[52px] pb-[40px] text-left align-middle shadow-xl transition-all md:pl-[32px] md:pr-[32px] md:pt-[32px]">
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
										<div className="flex items-end gap-[16px]">
											<h4 className="font-source-sans-pro text-[22px] font-semibold leading-[28px]">
												Policy Name 6 Config
											</h4>
											<button>
												<span className="font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-primary">
													Edit JSON
												</span>
											</button>
										</div>
									</Dialog.Title>
									{/* <ViewPolicyForm closeModal={closeModal} /> */}
									<EditPolicyConfigure closeModal={closeModal} />
								</Dialog.Panel>
							</div>
						</div>
					</Transition.Child>
				</Dialog>
			</Transition>
		</>
	);
}
