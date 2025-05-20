import { useDispatch, useSelector } from 'react-redux';
import Modal from '../../../../../components/Modal';
import {
	selectIsEditSecretModalOpen,
	setEditSecretModalOpen,
} from '../../../slice/Index';
import EditSecretForm from './EditSecretForm';

function EditSecretModal() {
	const isEditSecretModalOpen = useSelector(selectIsEditSecretModalOpen);
	const dispatch = useDispatch();

	function closeModal() {
		dispatch(setEditSecretModalOpen(false));
	}

	return (
		<Modal
			label="Edit New Secret"
			show={isEditSecretModalOpen}
			closeModal={closeModal}
			ModalBody={<EditSecretForm closeModal={closeModal} />}
		/>
	);
}

export default EditSecretModal;
