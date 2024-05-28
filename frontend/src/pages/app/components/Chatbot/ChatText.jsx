import React, { useState } from 'react';
import { ReactComponent as RestartIcon } from '../../../../assets/images/svg/restart-icon.svg';
import useApi from '../../../../hooks/useApi';
import BotChat from './BotChat';

const ChatText = ({
	data,
	appId,
	getConversationHistory,
	setErrorMessage,
	setIsLoading,
}) => {
	const triggerApi = useApi();
	const [disableRestartConversation, setDisableRestartConversation] =
		useState(false);
	const restartConversation = async (conversationId) => {
		setDisableRestartConversation(true);
		setIsLoading(true);
		let payloadData = new FormData();
		payloadData.append(
			'data',
			JSON.stringify({
				action: 'restart_conversation',
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
			getConversationHistory();
		} else {
			setErrorMessage(response.message);
			setIsLoading(false);
		}
		setDisableRestartConversation(false);
	};
	return (
		<div className="w-full px-6 pb-10">
			{data.map((messages, key, array) => (
				<div key={key} className="relative flex flex-col gap-2">
					<>
						<div className="  mt-[40px]   h-[2px] bg-[#DDE2E5]"></div>
						{key === array.length - 1 ? (
							<></>
						) : (
							<div className="sticky top-0 z-[11] flex w-full justify-end bg-white p-2">
								<button
									disabled={disableRestartConversation}
									onClick={() =>
										restartConversation(messages['conversation_id'])
									}
									className="flex cursor-pointer items-center justify-end gap-[10px] text-right text-sm font-semibold text-[#212429] disabled:opacity-50"
								>
									<div>
										<RestartIcon />
									</div>
									<div>restart conversation</div>
								</button>
							</div>
						)}
					</>
					{messages['Messages'].map((message, index, array) => {
						return (
							<div className="flex flex-col " key={index}>
								{message.role === 'user' ? (
									<div className=" max-w-[70%] self-end rounded-[6px] bg-[#5048ED] px-3 py-2 text-white">
										{message.content}
									</div>
								) : (
									message.role === 'assistant' && (
										<BotChat
											item={message}
											executionData={
												messages?.allow_execution &&
												index === array.length - 1 && {
													allow_execution: messages?.allow_execution,
													execution_data: messages?.execution_data,
												}
											}
											key={key}
										/>
									)
								)}
							</div>
						);
					})}
				</div>
			))}
		</div>
	);
};

export default ChatText;
