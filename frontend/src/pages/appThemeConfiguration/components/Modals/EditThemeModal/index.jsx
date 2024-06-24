import { useDispatch, useSelector } from 'react-redux';
import Modal from '../../../../../components/Modal';
import {
	closeIsEditThemeModalOpen,
	selectIsEditThemeModalOpen,
} from '../../../slice';
import EditThemeForm from './EditThemeForm';

function EditThemeModal() {
	const isEditThemeModalOpen = useSelector(selectIsEditThemeModalOpen);
	const dispatch = useDispatch();

	function closeModal() {
		dispatch(closeIsEditThemeModalOpen());
	}

	return (
		<Modal
			label="Edit App Theme"
			show={isEditThemeModalOpen}
			closeModal={closeModal}
			ModalBody={<EditThemeForm closeModal={closeModal} />}
		/>
	);
}

export default EditThemeModal;
