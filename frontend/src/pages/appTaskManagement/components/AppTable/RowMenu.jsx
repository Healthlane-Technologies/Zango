import { Menu, Transition } from '@headlessui/react';
import { Fragment, useEffect, useState } from 'react';
import { usePopper } from 'react-popper';
import { useDispatch, useSelector } from 'react-redux';
import { ReactComponent as TableRowKebabIcon } from '../../../../assets/images/svg/table-row-kebab-icon.svg';
import {
	openIsRemoveAllPoliciesModalOpen,
	openIsTaskHistoryModalOpen,
	openIsUpdateTaskModalOpen,
	selectAppTaskManagementData,
	selectIsTaskHistoryModalOpen,
	setAppTaskHistoryData,
} from '../../slice';
import { useParams } from 'react-router-dom';
import useApi from '../../../../hooks/useApi';

export default function RowMenu({ rowData }) {
	let { appId } = useParams();
	const triggerApi = useApi();
	const [referenceElement, setReferenceElement] = useState(null);
	const [popperElement, setPopperElement] = useState(null);
	const { styles, attributes } = usePopper(referenceElement, popperElement, {
		placement: 'bottom-end',
		modifiers: [
			{
				name: 'offset',
				options: {
					offset: [16, 8],
				},
			},
		],
	});

	const dispatch = useDispatch();
	const isTaskHistoryModalOpen = useSelector(selectIsTaskHistoryModalOpen);
	const handleEditUserDetails = () => {
		dispatch(openIsUpdateTaskModalOpen(rowData));
	};

	const handleDeactivateUser = () => {
		dispatch(openIsRemoveAllPoliciesModalOpen(rowData));
	};
	const appTaskManagementData = useSelector(selectAppTaskManagementData);

	const updateAppTaskHistorydata = (response) => {
		dispatch(setAppTaskHistoryData(response));
	};
	const handleTaskHistory = (selectedTaskId) => {
		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/tasks/${selectedTaskId}/`,
				type: 'GET',
				loader: true,
			});

			if (success && response) {
				updateAppTaskHistorydata(response);
			}
		};

		makeApiCall();

		
		dispatch(openIsTaskHistoryModalOpen(true));
	};

	return (
		<Menu as="div" className="relative flex">
			<Menu.Button
				className="flex w-full justify-center focus:outline-none"
				ref={(ref) => setReferenceElement(ref)}
			>
				<TableRowKebabIcon className="text-[#5048ED]" />
			</Menu.Button>
			<Transition
				as={Fragment}
				// @ts-ignore
				ref={(ref) => setPopperElement(ref)}
				style={styles['popper']}
				{...attributes['popper']}
			>
				<Menu.Items className="absolute right-0 top-[30px] w-[186px] origin-top-right rounded-[4px] bg-white shadow-table-menu focus:outline-none">
					<div className="p-[4px]">
						<Menu.Item>
							{({ active }) => (
								<button
									data-cy="update_task_button"
									type="button"
									className="flex w-full"
									onClick={handleEditUserDetails}
								>
									<div
										className={`${
											active ? 'bg-[#F0F3F4]' : ''
										} flex w-full flex-col rounded-[2px] px-[12px] py-[8px]`}
									>
										<span className="text-start font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
											Update Task
										</span>
										<span className="text-start font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#6C747D]">
											edit, delete policy, schedule
										</span>
									</div>
								</button>
							)}
						</Menu.Item>
						<Menu.Item>
							{({ active }) => (
								<button
									data-cy="remove_all_policies_button"
									type="button"
									className="flex w-full disabled:opacity-[0.38]"
									onClick={() => handleTaskHistory(rowData?.id)}
								>
									<div
										className={`${
											active ? 'bg-[#F0F3F4]' : ''
										} flex w-full flex-col rounded-[2px] px-[12px] py-[8px]`}
									>
										<span className="text-start font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
											Task History
										</span>
									</div>
								</button>
							)}
						</Menu.Item>
					</div>
				</Menu.Items>
			</Transition>
		</Menu>
	);
}
