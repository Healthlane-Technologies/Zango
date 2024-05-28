import { useDispatch, useSelector } from 'react-redux';
import Modal from '../../../../../components/Modal';
import {
	closeIsUpdateTaskModalOpen,
	selectIsUpdateTaskModalOpen,
} from '../../../slice';
import UpdateTaskForm from './UpdateTaskForm';

export default function UpdateTaskModal() {
	const isUpdateTaskModalOpen = useSelector(selectIsUpdateTaskModalOpen);
	const dispatch = useDispatch();

	function closeModal() {
		dispatch(closeIsUpdateTaskModalOpen());
	}

	return (
		<Modal
			label="Update Task"
			show={isUpdateTaskModalOpen}
			closeModal={closeModal}
			ModalBody={<UpdateTaskForm closeModal={closeModal} />}
		/>
	);
}
