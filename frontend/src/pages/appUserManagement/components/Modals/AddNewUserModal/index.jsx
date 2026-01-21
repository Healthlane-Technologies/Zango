import { useDispatch, useSelector } from 'react-redux';
import StandardModal from '../../../../../components/StandardModal';
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
		<StandardModal
			label="Add New User"
			show={isAddNewUserModalOpen}
			closeModal={closeModal}
			size="lg"
			ModalBody={<AddNewUserForm closeModal={closeModal} />}
		/>
	);
}

export default AddNewUserModal;
