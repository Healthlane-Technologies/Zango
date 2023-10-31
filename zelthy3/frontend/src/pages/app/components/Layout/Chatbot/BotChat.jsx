import Editor from '@monaco-editor/react';
import React, { useState } from 'react';
import { useDispatch } from 'react-redux';
import { useParams } from 'react-router-dom';
import { ReactComponent as CopyIcon } from '../../../../../assets/images/svg/copy-icon.svg';
import { ReactComponent as DislikeIcon } from '../../../../../assets/images/svg/dislike-icon.svg';
import { ReactComponent as LikeIcon } from '../../../../../assets/images/svg/like-icon.svg';
import { ReactComponent as PopoutIcon } from '../../../../../assets/images/svg/popout-icon.svg';
import useApi from '../../../../../hooks/useApi';
import { openIsDraggablePopoverOpen, setPopOverLink } from '../../../slice';

const BotChat = ({ item, executionData }) => {
	const [executionMsg, setExecutionMsg] = useState('');
	const [hideCommit, setHideCommit] = useState(false);
	const dispatch = useDispatch();
	let { appId } = useParams();
	const triggerApi = useApi();
	// console.log(item, executionData, executionData?.allow_execution);
	const handleCommit = (data) => {
		console.log('print commit data here', data);
		let postData = data;

		let formdata = new FormData();

		formdata.append('data', JSON.stringify(postData));

		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/code-assist/execute/`,
				type: 'POST',
				loader: false,
				payload: formdata,
			});
			if (success && response) {
				setHideCommit(true);
				setExecutionMsg(response.message);
				console.log('print execution data', response);
			} else {
				setHideCommit(false);
				if (response.message) {
					setExecutionMsg(response.message);
				} else {
					setExecutionMsg('An Error Occurred');
				}
			}
		};
		makeApiCall();
	};
	return (
		<div className="flex">
			<div
				className={`${
					item.content_meta.type === 'text' ? 'max-w-[70%]' : 'w-[70%]'
				} `}
			>
				<div className=" w-full self-start rounded-[6px] bg-[#F0F3F4] px-3 py-2">
					<>
						{item.content_meta.type === 'text' ? (
							<div className=" text-[#212429}  text-sm">{item.content}</div>
						) : item.content_meta.type === 'code' ? (
							<div className="relative w-full">
								<CopyIcon
									className="absolute top-0 right-0 z-10 cursor-pointer"
									onClick={() => {
										navigator.clipboard.writeText(item.content);
									}}
								/>
								<Editor
									height="300px"
									width={'100%'}
									defaultLanguage={item.content_meta.code_language}
									defaultValue={item.content}
									className="overflow-none"
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
										dispatch(setPopOverLink(item.content));
										dispatch(openIsDraggablePopoverOpen());
									}}
								/>

								<iframe
									className="h-[300px] w-full"
									src={item.content}
									title="W3Schools Free Online Web Tutorials"
								></iframe>
							</div>
						)}
					</>

					{executionData && executionData?.allow_execution && (
						<div className="mt-[8px] flex gap-[8px]">
							<button
								className={`rounded-[4px] bg-[#5048ED] px-[16px] py-[6px] text-sm font-bold text-white ${
									hideCommit ? 'hidden' : ''
								}`}
								onClick={() => handleCommit(executionData.execution_data)}
							>
								Commit
							</button>
						</div>
					)}
				</div>
				{executionMsg && (
					<div
						className={`mt-[8px] text-xs  ${
							hideCommit ? 'text-[#229470]' : 'text-danger-red'
						}`}
					>
						{executionMsg}
					</div>
				)}
			</div>
			{/* <div className="flex grow justify-end gap-[8px] self-end text-right">
				<LikeIcon className="cursor-pointer" />
				<DislikeIcon className="cursor-pointer" />
			</div> */}
		</div>
	);
};

export default BotChat;
