import { useDispatch, useSelector } from 'react-redux';
import Modal from '../../../../../components/Modal';
import {
	closeIsAddNewUserRolesModalOpen,
	selectIsAddNewUserRolesModalOpen,
} from '../../../slice';
import AddNewUserRolesForm from './AddNewUserRolesForm';

function AddNewUserRolesModal() {
	const isAddNewUserRolesModalOpen = useSelector(
		selectIsAddNewUserRolesModalOpen
	);
	const dispatch = useDispatch();

	function closeModal() {
		dispatch(closeIsAddNewUserRolesModalOpen());
	}

	return (
		<Modal
			label="Create New User Role"
			show={isAddNewUserRolesModalOpen}
			closeModal={closeModal}
			ModalBody={<AddNewUserRolesForm closeModal={closeModal} />}
		/>
	);
}

export default AddNewUserRolesModal;
