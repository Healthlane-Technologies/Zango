import Editor from '@monaco-editor/react';
import React, { useState } from 'react';
import { useDispatch } from 'react-redux';
import { useParams } from 'react-router-dom';
import { ReactComponent as CopyIcon } from '../../../../../assets/images/svg/copy-icon.svg';
import { ReactComponent as DislikeIcon } from '../../../../../assets/images/svg/dislike-icon.svg';
import { ReactComponent as LikeIcon } from '../../../../../assets/images/svg/like-icon.svg';
import { ReactComponent as PopoutIcon } from '../../../../../assets/images/svg/popout-icon.svg';
import useApi from '../../../../../hooks/useApi';
import {
	openIsDraggablePopoverOpen,
	setPopOverLink
} from '../../../slice';


const BotChat = ({item}) => {
    const [executionMsg, setExecutionMsg] = useState('')
	const [hideCommit, setHideCommit] = useState(false)
	const dispatch = useDispatch();
    let { appId } = useParams();
		const triggerApi = useApi();
		const handleCommit = (data) => {
			console.log('print commit data here', data);
			let postData =  data.exection_json

			let formdata = new FormData()

			formdata.append('data', JSON.stringify(postData));

			const makeApiCall = async () => {
				const { response, success } = await triggerApi({
					url: `/api/v1/apps/${appId}/code-assist/execute/`,
					type: 'POST',
					loader: true,
					Payload: postData,
				});
				if (success && response) {
					setHideCommit(true)
                    setExecutionMsg(response.message);
					console.log('print excution data', response);
				}
			};
			makeApiCall();
		};
  return (
		<div className="flex">
			<div className="max-w-[70%]">
				<div className="mt-[8px] w-full self-start rounded-[6px] bg-[#F0F3F4] px-[10px] py-[8px]">
					{item.assist_message.map((el) => {
						return (
							<>
								{el.content_meta.type === 'text' ? (
									<div className=" text-[#212429} mb-[8px] text-sm">
										{el.content}
									</div>
								) : el.content_meta.type === 'code' ? (
									<div className="relative w-full">
										<CopyIcon
											className="absolute top-0 right-0 z-10 cursor-pointer"
											onClick={() => {
												navigator.clipboard.writeText(el.content);
											}}
										/>
										<Editor
											height="300px"
											defaultLanguage={el.content_meta.code_language}
											defaultValue={el.content}
											theme="vs-dark"
											options={{
												domReadOnly: true,
												minimap: { enabled: false },
												readOnly: true,
											}}
											readOnly={true}
										/>
									</div>
								) : (
									<div className="relative mt-2">
										<PopoutIcon
											className="absolute top-[12px] right-[12px] z-10 cursor-pointer"
											onClick={() => {
												dispatch(setPopOverLink(el.content));
												dispatch(openIsDraggablePopoverOpen());
											}}
										/>

										<iframe
											className="h-[300px] w-full"
											src={el.content}
											title="W3Schools Free Online Web Tutorials"
										></iframe>
									</div>
								)}
							</>
						);
					})}
					{item.allow_execution && (
						<div className="mt-[8px] flex gap-[8px]">
							<button
								className={`rounded-[4px] bg-[#5048ED] px-[16px] py-[6px] text-sm font-bold text-white ${
									hideCommit ? 'hidden' : ''
								}`}
								onClick={() => handleCommit(item)}
							>
								Commit
							</button>
						</div>
					)}
				</div>
				{executionMsg && (
					<div className="mt-[8px] text-xs text-[#229470]">{executionMsg}</div>
				)}
			</div>
			<div className="flex grow justify-end gap-[8px] self-end text-right">
				<LikeIcon className="cursor-pointer" />
				<DislikeIcon className="cursor-pointer" />
			</div>
		</div>
	);
}

export default BotChat