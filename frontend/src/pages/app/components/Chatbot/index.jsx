import { Formik } from 'formik';
import _ from 'lodash';
import Lottie from 'lottie-react';
import React, { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { Popper } from 'react-popper';
import { useParams } from 'react-router-dom';
import * as Yup from 'yup';
import { ReactComponent as ChatbotIcon } from '../../../../assets/images/svg/chatbot-icon.svg';
import { ReactComponent as CloseIcon } from '../../../../assets/images/svg/close-icon.svg';
import { ReactComponent as PlusIcon } from '../../../../assets/images/svg/plus-icon.svg';
import { ReactComponent as SendIcon } from '../../../../assets/images/svg/send-icon.svg';
import animationData from '../../../../assets/images/zelthy-loader.json';
import useApi from '../../../../hooks/useApi';
import ChatText from './ChatText';
import RadioPillField from './RadioPillField';

const Chatbot = () => {
	const [userMessage, setUserMessage] = useState('');
	const [isNewConversation, setIsNewConversation] = useState(false);
	const [isLoading, setIsLoading] = useState(false);
	const [errorMessage, setErrorMessage] = useState(false);
	const [isOpen, setIsOpen] = useState(false);
	const [messages, setMessages] = useState([]);

	const triggerRef = useRef(null);
	const popoverRef = useRef(null);
	const scrollBottomRef = useRef(null);
	let { appId } = useParams();
	const triggerApi = useApi();

	/**
	 * Scrolls to the bottom of the page.
	 */
	const scrollToBottom = () => {
		const { scrollHeight } = scrollBottomRef.current;
		scrollBottomRef.current.scrollTo(0, scrollHeight);
	};

	/**
	 * Updates the messages based on the provided data.
	 *
	 * @param {object} data - The data used to update the messages.
	 * @param {boolean} isNewConversation - Indicates if it is a new conversation.
	 */
	function updateMessages(data, isNewConversation) {
		if (isNewConversation) {
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

	/**
	 * Returns the conversation ID of the active conversation.
	 *
	 * @return {string} The conversation ID of the active conversation.
	 */
	const getActiveConversationId = () => {
		let activeMessage = messages.slice(-1);
		return activeMessage[0]['conversation_id'];
	};

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
			setUserMessage('');
		} else {
			setUserMessage(response.message);
			setIsLoading(false);
		}
	};

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
				}, 5000);
			} else if (response.status === 'completed') {
				updateMessages(response, isNewConversation);
				setUserMessage('');
				setIsLoading(false);
			}
		} else {
			setUserMessage(response.message);
			setIsLoading(false);
		}
	};

	useEffect(() => {
		getConversationHistory();
	}, []);

	useLayoutEffect(() => {
		if (scrollBottomRef.current) {
			scrollToBottom();
		}
	}, [isLoading, isOpen, messages, isNewConversation]);

	let initialValues = {
		message: '',
		filter: '',
	};
	let validationSchema = Yup.object().shape({
		message: Yup.string().trim().required('command text Required'),
		filter: Yup.string().required('please select one category'),
	});

	const onSubmit = (values, actions) => {
		let postData = {
			action: isNewConversation ? 'create_conversation' : 'update_conversation',
			action_data: {
				message: values.message,
				knowledge_base: values.filter,
			},
		};
		if (!isNewConversation) {
			postData['conversation_id'] = getActiveConversationId();
		}

		let update_conversation_form = new FormData();
		update_conversation_form.append('data', JSON.stringify(postData));

		const makeApiCall = async () => {
			setUserMessage(values.message);
			actions.resetForm({ values: { message: '', filter: values.filter } });
			setIsLoading(true);

			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/code-assist/conversation/`,
				type: 'POST',
				loader: false,
				payload: update_conversation_form,
			});
			if (success && response) {
				getConversationMessages(response.conversation_id);

				setErrorMessage('');
			} else {
				setErrorMessage(response.message);
				setIsLoading(false);
			}
		};
		makeApiCall();
	};
	const createNewConversation = () => {
		setIsNewConversation(true);
	};

	const closePopover = () => {
		setIsOpen(false);
	};

	const togglePopover = () => {
		setIsOpen((prev) => !prev);
	};

	return (
		<div className="relative z-[10]">
			<button
				ref={triggerRef}
				onClick={togglePopover}
				className="fixed bottom-[50px] right-0"
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
									<div className="fixed left-[26px] top-[16px] text-lg font-semibold text-[#000]">
										Code Assist
									</div>

									<div
										className="fixed right-[26px] top-[16px] cursor-pointer"
										onClick={() => closePopover()}
									>
										<CloseIcon />
									</div>
								</div>
								<div
									className="h-[calc(100%-178px)] overflow-auto scroll-smooth"
									ref={scrollBottomRef}
								>
									<ChatText
										data={messages}
										appId={appId}
										getConversationHistory={getConversationHistory}
										setErrorMessage={setErrorMessage}
										setIsLoading={setIsLoading}
									/>
									{isNewConversation && (
										<div className="mx-6 my-10  h-[2px] bg-[#DDE2E5]"></div>
									)}
									{userMessage && (
										<div className="flex flex-col px-6">
											<div className=" max-w-[70%] self-end rounded-[6px] bg-[#5048ED] px-3 py-2 text-white">
												{userMessage}
											</div>
										</div>
									)}
									{errorMessage && !isLoading && (
										<div className="mt-2 flex justify-center bg-error px-3 py-2 font-semibold text-error-text text-white">
											{errorMessage}
										</div>
									)}

									{isLoading && (
										<div
											className={`relative flex ${
												messages.length === 0 ? 'h-[calc(100%-36px)]' : ''
											} min-h-[100px] items-center justify-center`}
										>
											{' '}
											<Lottie
												animationData={animationData}
												className="lottie-container h-[100px] w-[100px] [&>svg]:!transform-none"
											/>
											{/* <div className="mini-spinner"></div> */}
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
