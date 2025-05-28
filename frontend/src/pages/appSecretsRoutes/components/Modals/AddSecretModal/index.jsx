import { useDispatch, useSelector } from 'react-redux';
import Modal from '../../../../../components/Modal';
import {
	selectIsAddSecretModalOpen,
	setAddSecretModalOpen
} from '../../../slice/Index';
import AddSecretForm from './AddSecretForm';

function AddSecretModal() {
	const isAddSecretModalOpen = useSelector(selectIsAddSecretModalOpen);
	const dispatch = useDispatch();

	function closeModal() {
		dispatch(setAddSecretModalOpen(false));
	}

	return (
		<Modal
			label="Add New Secret"
			show={isAddSecretModalOpen}
			closeModal={closeModal}
			ModalBody={<AddSecretForm closeModal={closeModal} />}
		/>
	);
}

export default AddSecretModal;
