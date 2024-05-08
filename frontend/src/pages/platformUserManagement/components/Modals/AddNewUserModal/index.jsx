import { useDispatch, useSelector } from 'react-redux';
import Modal from '../../../../../components/Modal';
import {
	closeIsAddNewUserModalOpen,
	selectIsAddNewUserModalOpen,
} from '../../../slice';
import AddNewUserForm from './AddNewUserForm';

function AddNewUserModal() {
	const isAddNewUserModalOpen = useSelector(selectIsAddNewUserModalOpen);
	const dispatch = useDispatch();

	function closeModal() {
		dispatch(closeIsAddNewUserModalOpen());
	}

	return (
		<Modal
			label="Add New User"
			show={isAddNewUserModalOpen}
			closeModal={closeModal}
			ModalBody={<AddNewUserForm closeModal={closeModal} />}
		/>
	);
}

export default AddNewUserModal;
