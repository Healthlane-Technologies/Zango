import React from 'react';
import BotChat from './BotChat';
import { ReactComponent as RestartIcon } from '../../../../../assets/images/svg/restart-icon.svg';
import useApi from '../../../../../hooks/useApi';

const ChatText = ({ data, appId, getConversationHistory }) => {
	const triggerApi = useApi();

	const restartConversation = async (conversationId) => {
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
			loader: true,
			payload: payloadData,
		});
		if (success && response) {
			console.log('print restart response here', response);
			getConversationHistory();
		}
	};
	return (
		<div className="w-full px-[24px]">
			{data.map((messages, key) => (
				<React.Fragment key={key}>
					<>
						<div className="mt-[40px] mb-[8px] h-[2px] bg-[#DDE2E5]"></div>
						{messages.Status === 'open' ? (
							<></>
						) : (
							<div className="flex justify-end">
								<button
									onClick={() =>
										restartConversation(messages['conversation_id'])
									}
									className="flex cursor-pointer items-center justify-end gap-[10px] text-right text-sm font-semibold text-[#212429]"
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
							<div className="flex flex-col gap-[8px] p-[8px]" key={index}>
								{message.role === 'user' ? (
									<div className="mt-[8px] max-w-[70%] self-end rounded-[6px] bg-[#5048ED] px-[10px] py-[4px] text-white">
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
				</React.Fragment>
			))}
		</div>
	);
};

export default ChatText;
