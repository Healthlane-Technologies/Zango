import React from 'react'
import { useDispatch, useSelector } from 'react-redux';
import Modal from '../../../../../components/Modal';
import TaskHistoryContainer from './TaskHistoryContainer';
import { openIsTaskHistoryModalOpen, selectIsTaskHistoryModalOpen } from '../../../slice';
function TaskHistoryModal() {
    // const appUserManagementFormData = useSelector(
	// 	selectAppUserManagementFormData
	// );
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



// import { useDispatch, useSelector } from 'react-redux';
// // import Modal from '../../../../../components/Modal';
// import {
// 	closeIsActivateUserModalOpen,
// 	selectAppUserManagementFormData,
// 	selectIsActivateUserModalOpen,
// } from '../../../slice';
// import ActivateUserForm from './ActivateUserForm';
// import Modal from '../../../../../components/Modal';

// function ActivateUserModal() {
// 	const appUserManagementFormData = useSelector(
// 		selectAppUserManagementFormData
// 	);
// 	const isActivateUserModalOpen = useSelector(selectIsActivateUserModalOpen);
// 	const dispatch = useDispatch();

// 	function closeModal() {
// 		dispatch(closeIsActivateUserModalOpen());
// 	}

// 	return (
// 		<>
// 			<Modal
// 				label={`Activate ${appUserManagementFormData?.name}`}
// 				show={isActivateUserModalOpen}
// 				closeModal={closeModal}
// 				ModalBody={<ActivateUserForm closeModal={closeModal} />}
// 			/>
// 		</>
// 	);
// }

// export default ActivateUserModal;