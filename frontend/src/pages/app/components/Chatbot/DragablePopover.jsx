import { Transition } from '@headlessui/react';
import React, { useState } from 'react';
import Draggable from 'react-draggable';
import { useDispatch, useSelector } from 'react-redux';
import { ResizableBox } from 'react-resizable';
import { ReactComponent as CloseIcon } from '../../../../assets/images/svg/close-icon.svg';
import { ReactComponent as RefreshIcon } from '../../../../assets/images/svg/refresh-icon.svg';
import {
	closeIsDraggablePopoverOpen,
	openIsDraggablePopoverOpen,
	selectIsDraggablePopoverOpen,
	selectPopOverLink,
} from '../../slice';

const DragablePopover = () => {
	const isDraggablePopoverOpen = useSelector(selectIsDraggablePopoverOpen);
	const popOverLink = useSelector(selectPopOverLink);
	let [isOpen, setIsOpen] = useState(true);
	const dispatch = useDispatch();
	const [count, setCount] = useState(0);

	function closeModal() {
		setIsOpen(false);
		dispatch(closeIsDraggablePopoverOpen());
	}

	function openModal() {
		setIsOpen(true);
		dispatch(openIsDraggablePopoverOpen());
	}
	return (
		<>
			<Transition show={isDraggablePopoverOpen}>
				<Draggable
					cancel=".react-resizable-handle"
					defaultPosition={{ x: 0, y: 0 }}
				>
					<ResizableBox
						width={450}
						height={300}
						className="flex flex-grow"
						resizeHandles={['ne', 'e', 'n']}
					>
						<div className="relative flex flex-grow rounded-[6px] bg-[#F0F3F4] p-[8px] pt-[30px]">
							<div className="fixed right-[20px] top-[6px] flex cursor-pointer items-center gap-[8px]">
								<RefreshIcon
									className="w-3"
									onClick={() => {
										setCount(count + 1);
										openModal();
									}}
								/>
								<CloseIcon className="w-3" onClick={() => closeModal()} />
							</div>
							<iframe
								className="h-full w-full border-[2px] bg-white"
								src={popOverLink}
								key={count}
								title="W3Schools Free Online Web Tutorials"
							></iframe>
						</div>
					</ResizableBox>
				</Draggable>
			</Transition>
		</>
	);
};

export default DragablePopover;
