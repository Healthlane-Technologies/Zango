import React from 'react'
import { useDispatch, useSelector } from 'react-redux';
import Modal from '../../../../../components/Modal';
import TaskHistoryContainer from './TaskHistoryContainer';
import { openIsTaskHistoryModalOpen, selectIsTaskHistoryModalOpen } from '../../../slice';
function TaskHistoryModal() {
	const isTaskHistoryModalOpen = useSelector(selectIsTaskHistoryModalOpen);
	const dispatch = useDispatch();

	function closeModal() {
		dispatch(openIsTaskHistoryModalOpen(false));
	}

  return (
    <>
    <Modal
        label={`Tasks History`}
        show={isTaskHistoryModalOpen}
        closeModal={closeModal}
        ModalBody={<TaskHistoryContainer/>}
    />
</>
  )
}

export default TaskHistoryModal


