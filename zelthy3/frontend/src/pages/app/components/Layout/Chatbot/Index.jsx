import { Formik } from 'formik';
import _ from 'lodash';
import React, { useEffect, useRef, useState } from 'react';
import { Popper } from 'react-popper';
import { useParams } from 'react-router-dom';
import * as Yup from 'yup';
import { ReactComponent as ChatbotIcon } from '../../../../../assets/images/svg/chatbot-icon.svg';
import { ReactComponent as CloseIcon } from '../../../../../assets/images/svg/close-icon.svg';
import { ReactComponent as PlusIcon } from '../../../../../assets/images/svg/plus-icon.svg';
import { ReactComponent as SendIcon } from '../../../../../assets/images/svg/send-icon.svg';
import useApi from '../../../../../hooks/useApi';
import ChatText from './ChatText';
import RadioPillField from './RadioPillField';

const Chatbot = () => {
	const [activeConversationId, setActiveConversationId] = useState('');
	const [isNewConversation, setIsNewConversation] = useState(false);
	const [isOpen, setIsOpen] = useState(false);
	const triggerRef = useRef(null);
	const popoverRef = useRef(null);

	let { appId } = useParams();
	const triggerApi = useApi();
	// const [messages, setMessages] = useState([
	// 	{
	// 		assist_message: 'can you help me create modal',
	// 		type: 'break',
	// 		action: 'get_assist',
	// 		knowledge_base: '1',
	// 	},
	// 	{
	// 		assist_message: 'can you help me create modal',
	// 		type: 'user',
	// 		action: 'get_assist',
	// 		knowledge_base: '1',
	// 	},
	// 	{
	// 		assist_message: [
	// 			{
	// 				content:
	// 					"Sure! I am ready to help you create your requested model.<br/> For this I will be adding the model's class in the module's models.py file. The proposed model's class is <br/>",
	// 				content_meta: {
	// 					type: 'text',
	// 				},
	// 			},
	// 			{
	// 				content:
	// 					"from django.db import models\nfrom zelthy.apps.dynamic_models.models import DynamicModelBase\nfrom zelthy.apps.dynamic_models.fields import ZForeignKey\n\nclass Patient(DynamicModelBase):\n    GENDER_CHOICES = [\n        ('male', 'Male'),\n        ('female', 'Female'),\n        ('other', 'Other'),\n    ]\n\n    name = models.CharField(max_length=255)\n    age = models.IntegerField()\n    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)\n    address = models.CharField(max_length=255, blank=True, null=True)\n    phone_number = models.CharField(max_length=15, blank=True, null=True)\n    email = models.EmailField(blank=True, null=True)\n\n    def __str__(self):\n        return self.name",
	// 				content_meta: {
	// 					type: 'code',
	// 					code_language: 'python',
	// 				},
	// 			},
	// 		],
	// 		type: 'bot',
	// 		allow_execution: true,
	// 		exection_json: {
	// 			execution: 'createModel',
	// 			module: 'patients',
	// 			'models.py':
	// 				"from django.db import models\nfrom zelthy.apps.dynamic_models.models import DynamicModelBase\nfrom zelthy.apps.dynamic_models.fields import ZForeignKey\n\nclass Patient(DynamicModelBase):\n    GENDER_CHOICES = [\n        ('male', 'Male'),\n        ('female', 'Female'),\n        ('other', 'Other'),\n    ]\n\n    name = models.CharField(max_length=255)\n    age = models.IntegerField()\n    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)\n    address = models.CharField(max_length=255, blank=True, null=True)\n    phone_number = models.CharField(max_length=15, blank=True, null=True)\n    email = models.EmailField(blank=True, null=True)\n\n    def __str__(self):\n        return self.name",
	// 		},
	// 	},
	// 	{
	// 		assist_message: 'can you help me create modal',
	// 		type: 'break',
	// 		action: 'get_assist',
	// 		knowledge_base: '1',
	// 	},
	// 	{
	// 		assist_message: 'thanks',
	// 		type: 'user',
	// 		action: 'get_assist',
	// 		knowledge_base: '1',
	// 	},
	// 	{
	// 		assist_message: [
	// 			{
	// 				content:
	// 					"Sure! I am ready to help you create your requested model.<br/> For this I will be adding the model's class in the module's models.py file. The proposed model's class is <br/>",
	// 				content_meta: {
	// 					type: 'text',
	// 				},
	// 			},
	// 			{
	// 				content:
	// 					'https://www.youtube.com/embed/XHTrLYShBRQ?si=ZjT4H8YyTtgUPAhv',
	// 				content_meta: {
	// 					type: 'url',
	// 				},
	// 			},
	// 		],
	// 		type: 'bot',
	// 	},
	// 	{
	// 		assist_message: 'can you help me create modal',
	// 		type: 'break',
	// 		status: 'new',
	// 		action: 'get_assist',
	// 		knowledge_base: '1',
	// 	},
	// 	{
	// 		assist_message: 'show me the map',
	// 		type: 'user',
	// 		action: 'get_assist',
	// 		knowledge_base: '1',
	// 	},
	// 	{
	// 		assist_message: [
	// 			{
	// 				content:
	// 					"Sure! I am ready to help you create your requested model.<br/> For this I will be adding the model's class in the module's models.py file. The proposed model's class is <br/>",
	// 				content_meta: {
	// 					type: 'text',
	// 				},
	// 			},
	// 			{
	// 				content:
	// 					'https://www.openstreetmap.org/export/embed.html?bbox=-0.004017949104309083%2C51.47612752641776%2C0.00030577182769775396%2C51.478569861898606&layer=mapnik',
	// 				content_meta: {
	// 					type: 'url',
	// 				},
	// 			},
	// 		],
	// 		type: 'bot',
	// 	},
	// ]);
	const [messages, setMessages] = useState([]);
	const getConversationHistory = async () => {
		let payloadData = new FormData();
		payloadData.append(
			'data',
			JSON.stringify({
				action: 'get_conversations',
			})
		);
		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/code-assist/conversation/`,
			type: 'POST',
			loader: true,
			payload: payloadData,
		});
		if (success && response) {
			response['conversations'].length === 0
				? setIsNewConversation(true)
				: setIsNewConversation(false);
			setMessages([...response.conversations]);
		}
	};
	useEffect(() => {
		getConversationHistory();
	}, []);

	useEffect(() => {
		let activeMessage = messages.slice(-1);
		if (activeMessage[0]) {
			setActiveConversationId(activeMessage[0]['conversation_id']);
		}
		console.log('activeMessage ======>', activeMessage);
	}, [messages]);

	let initialValues = {
		message: '',
		filter: '',
	};
	let validationSchema = Yup.object().shape({
		message: Yup.string().trim().required('command text Required'),
		filter: Yup.string().required('please select one category'),
	});

	const onSubmit = (values, actions) => {
		console.log('submitted', values);
		let postData = {
			action: isNewConversation ? 'create_conversation' : 'update_conversation',
			action_data: {
				message: values.message,
				knowledge_base: values.filter,
			},
		};
		if (!isNewConversation) {
			postData['conversation_id'] = activeConversationId;
		}
		console.log('print update convo post data', postData);

		let update_conversation_form = new FormData();
		update_conversation_form.append('data', JSON.stringify(postData));

		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/code-assist/conversation/`,
				type: 'POST',
				loader: true,
				payload: update_conversation_form,
			});
			if (success && response) {
				// updateAppConfigurationData(response);
				if (isNewConversation) {
					setMessages([...messages, response]);
					setIsNewConversation(false);
				} else {
					let tempData = messages;
					tempData.forEach((conversation, index) => {
						if (conversation['conversation_id'] === response.conversation_id) {
							conversation.Messages.push(...response.Messages);
							conversation['allow_execution'] = response['allow_execution'];
							conversation['execution_data'] = response['execution_data'];
						}
					});
					setMessages([...tempData]);
				}
				actions.resetForm();
			}
		};
		makeApiCall();
	};

	const createNewConversation = () => {
		setIsNewConversation(true);
	};

	//   const openPopover = () => {
	// 		setIsOpen(true);
	// 	};

	const closePopover = () => {
		setIsOpen(false);
	};

	const togglePopover = () => {
		setIsOpen((prev) => !prev);
	};

	return (
		<div className="relative z-50">
			<button
				ref={triggerRef}
				onClick={togglePopover}
				className="fixed bottom-0 right-0"
			>
				<ChatbotIcon />
			</button>
			{isOpen && (
				<Popper
					referenceElement={triggerRef.current}
					placement="top"
					modifiers={[
						{
							name: 'eventListeners',
							enabled: true,
							phase: 'write',
							options: {
								scroll: true,
							},
						},
					]}
				>
					{({ ref, style }) => (
						<div
							ref={(node) => {
								ref(node);
								popoverRef.current = node;
							}}
							style={style}
							className="popover-content"
						>
							<div className="mx-3 h-[80vh] w-[800px] rounded-[6px] bg-white shadow-table-menu">
								<div className="border-[#DDE2E5} relative h-[64px] border-b-[1px]">
									<div className="fixed top-[16px] left-[26px] text-lg font-semibold text-[#000]">
										Code Assist
									</div>

									<div
										className="fixed top-[16px] right-[26px] cursor-pointer"
										onClick={() => closePopover()}
									>
										<CloseIcon />
									</div>
								</div>
								<div className="h-[calc(100%-178px)] overflow-auto">
									<ChatText
										data={messages}
										appId={appId}
										getConversationHistory={getConversationHistory}
									/>
									{isNewConversation && (
										<div className="mx-6 mt-[40px] mb-[8px] h-[2px] bg-[#DDE2E5]"></div>
									)}
									<div
										className="mr-[24px] cursor-pointer text-right text-sm font-semibold text-[#5048ED]"
										onClick={() => createNewConversation()}
									>
										start new conversation
									</div>
								</div>
								<Formik
									initialValues={initialValues}
									validationSchema={validationSchema}
									onSubmit={(values, actions) => {
										return new Promise((resolve) => {
											onSubmit(values, actions);
											resolve();
										});
									}}
								>
									{(formik) => {
										return (
											<form onSubmit={formik.handleSubmit}>
												<div className="flex h-[114px]  p-[8px]">
													<div className="flex h-full w-full flex-col justify-between rounded-[6px] border-[1px] px-[4px] py-[6px]">
														<div className="flex justify-between">
															<textarea
																className="mx-[5px] h-[40px] w-full p-1 text-sm focus:ring-0"
																type="text"
																name="message"
																id="message"
																onChange={formik.handleChange}
																onBlur={formik.handleBlur}
																value={formik.values.message}
																placeholder="Select or Type any Command"
															/>
															<button
																type="submit"
																className="mr-[5px] flex items-center gap-2 rounded-full bg-[#F0F3F4] px-[10px] py-[2px]"
															>
																<SendIcon className="h-4 w-4" />
															</button>
															{/* <input
															type="submit"
															// className="left-[-9999px], absolute h-[1px] w-[1px]"
															// tabindex="-1"
														/> */}
														</div>

														<div className="flex gap-[10px] divide-x-[1px]">
															<div className="ml-[5px]">
																<PlusIcon />
															</div>
															<div className="pl-[10px]">
																<RadioPillField
																	key="filter"
																	label="Filter"
																	name="filter"
																	id="filter"
																	radioData={[
																		{
																			id: 'Zelthy Basics',
																			value: 'basics',
																			label: 'Zelthy Basics',
																		},
																		{
																			id: 'Models',
																			value: 'models',
																			label: 'Models',
																		},
																		{
																			id: 'Crud Pkg',
																			value: 'crud',
																			label: 'Crud Pkg',
																		},
																		{
																			id: 'Frames Pkg',
																			value: 'frames',
																			label: 'Frames Pkg',
																		},
																		{
																			id: 'Login-Signup Pkg',
																			value: 'login_signup',
																			label: 'Login-Signup Pkg',
																		},
																		{
																			id: 'Generic',
																			value: 'generic',
																			label: 'Generic',
																		},
																	]}
																	placeholder=""
																	value={_.get(formik.values, 'filter', '')}
																	onChange={formik.handleChange}
																	formik={formik}
																/>
															</div>
														</div>
													</div>
												</div>
											</form>
										);
									}}
								</Formik>
							</div>
						</div>
					)}
				</Popper>
			)}
		</div>
	);
};

export default Chatbot;
