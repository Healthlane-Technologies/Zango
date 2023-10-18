import React from 'react';
import BotChat from './BotChat';
import { ReactComponent as RestartIcon } from '../../../../../assets/images/svg/restart-icon.svg';

const ChatText = ({ data }) => {

	return (
		<div className="w-full px-[24px]">
			{data.map((el) => {
				return (
					<div className="flex flex-col gap-[8px] p-[8px]">
						{el.type === 'user' ? (
							<div className="mt-[8px] max-w-[70%] self-end rounded-[6px] bg-[#5048ED] px-[10px] py-[4px] text-white">
								{el.assist_message}
							</div>
						) : el.type === 'bot' ? (
							<BotChat item={el} />
						) : (
							<>
								<div className="mt-[40px] mb-[8px] h-[2px] bg-[#DDE2E5]"></div>
								{el.status === 'new' ? (
									<></>
								) : (
									<div className="flex cursor-pointer items-center justify-end gap-[10px] text-sm font-semibold text-[#212429]">
										<div>
											<RestartIcon />
										</div>
										<div>restart conversation</div>
									</div>
								)}
							</>
						)}
					</div>
				);
			})}
		</div>
	);
};

export default ChatText;
