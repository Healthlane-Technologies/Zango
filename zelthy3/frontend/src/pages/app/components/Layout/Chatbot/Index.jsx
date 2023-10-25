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
// import launchingAppLoaderGif from '../../../../../assets/images/gif/launching-app-loader.gif';

import useApi from '../../../../../hooks/useApi';
import ChatText from './ChatText';
import RadioPillField from './RadioPillField';

const Chatbot = () => {
	const [activeConversationId, setActiveConversationId] = useState('');
	const [isNewConversation, setIsNewConversation] = useState(false);
	const [isLoading, setIsLoading] = useState(false);
	const [isOpen, setIsOpen] = useState(false);
	const triggerRef = useRef(null);
	const popoverRef = useRef(null);
	const scrollBottomRef = useRef(null);

	let { appId } = useParams();
	const triggerApi = useApi();
	const [messages, setMessages] = useState([]);

	const scrollToBottom = () => {
		if (scrollBottomRef.current) {
			scrollBottomRef.current.scrollTop = scrollBottomRef.current.scrollHeight;
			return setTimeout(() => {
				return scrollBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
			}, 200);
		}
	};
	function updateMessages(data, isNewConversation) {
		if (isNewConversation) {
			// console.log('before====>', messages);
			setMessages([...messages, data]);
			setIsNewConversation(false);
		} else {
			let tempData = messages;

			tempData.forEach((conversation, index, array) => {
				if (conversation['conversation_id'] === data.conversation_id) {
					conversation.Messages.push(...data.Messages);
					conversation['allow_execution'] = data['allow_execution'];
					conversation['execution_data'] = data['execution_data'];
				}
			});
			setMessages([...tempData]);
		}
	}
	const getConversationHistory = async () => {
		setIsLoading(true);

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
			loader: false,
			payload: payloadData,
		});
		if (success && response) {
			response['conversations'].length === 0
				? setIsNewConversation(true)
				: setIsNewConversation(false);
			setMessages([...response.conversations]);
			setIsLoading(false);
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
		// console.log('activeMessage ======>', activeMessage);
		console.log('Messagess======>', messages);
	}, [messages]);

	let initialValues = {
		message: '',
		filter: '',
	};
	let validationSchema = Yup.object().shape({
		message: Yup.string().trim().required('command text Required'),
		filter: Yup.string().required('please select one category'),
	});
	const getConversationMessages = async (conversationId) => {
		let payloadData = new FormData();
		payloadData.append(
			'data',
			JSON.stringify({
				action: 'get_conversation_message',
				conversation_id: conversationId,
			})
		);
		const { response, success } = await triggerApi({
			url: `/api/v1/apps/${appId}/code-assist/conversation/`,
			type: 'POST',
			loader: false,
			payload: payloadData,
		});
		if (success && response) {
			if (response.status === 'waiting') {
				setTimeout(() => {
					getConversationMessages(conversationId);
				}, 500);
			} else if (response.status === 'completed') {
				updateMessages(response, isNewConversation);
				setIsLoading(false);
			}
		}
	};

	const onSubmit = (values, actions) => {
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
		// console.log('print update convo post data', postData);

		let update_conversation_form = new FormData();
		update_conversation_form.append('data', JSON.stringify(postData));

		const makeApiCall = async () => {
			setIsLoading(true);
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/code-assist/conversation/`,
				type: 'POST',
				loader: false,
				payload: update_conversation_form,
			});
			if (success && response) {
				// updateAppConfigurationData(response);
				// updateMessages(response, isNewConversation);
				getConversationMessages(response.conversation_id);
				actions.resetForm({ values: { message: '', filter: values.filter } });
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
		<div className="relative z-[1000]">
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
										<div className="mx-6 my-10  h-[2px] bg-[#DDE2E5]"></div>
									)}
									{isLoading && (
										<div
											className={`relative flex ${
												messages.length === 0 ? 'h-[calc(100%-36px)]' : ''
											} min-h-[100px] items-center justify-center`}
										>
											{' '}
											{/* <img
												src={launchingAppLoaderGif}
												alt="#"
												className="h-[78px] max-h-[78px] min-h-[78px] w-[79px] min-w-[79px] max-w-[79px]"
											/> */}
											<div className="mini-spinner"></div>
										</div>
									)}

									{!isNewConversation && (
										<div className="sticky bottom-0 z-10 mr-2 bg-white p-2 text-right text-sm font-semibold   text-[#5048ED] ">
											<button
												className="disabled:opacity-50"
												disabled={isLoading}
												onClick={() => createNewConversation()}
											>
												start new conversation
											</button>
										</div>
									)}
									<div className="h-0 w-0 bg-black" ref={scrollBottomRef}></div>
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
												<div className="flex h-[114px]  px-[8px] pb-[8px]">
													<div className="flex h-full w-full flex-col justify-between rounded-[6px] border-[1px] px-[4px] py-[6px] focus-within:border-primary">
														<div className="flex justify-between">
															<textarea
																className="mx-[5px] h-[40px] w-full p-1 text-sm focus:outline-none focus:ring-0 disabled:opacity-50"
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
																disabled={isLoading}
																className="mr-[5px] flex h-6 items-center gap-2 rounded-full bg-[#F0F3F4] px-[10px] py-[2px] disabled:opacity-50"
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
