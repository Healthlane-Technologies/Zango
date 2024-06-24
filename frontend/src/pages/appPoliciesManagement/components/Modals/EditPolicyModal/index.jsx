import { useDispatch, useSelector } from 'react-redux';
import Modal from '../../../../../components/Modal';
import {
	closeIsEditPolicyModalOpen,
	selectIsEditPolicyModalOpen,
} from '../../../slice';
import EditPolicyForm from './EditPolicyForm';

function EditPolicyModal() {
	const isEditPolicyModalOpen = useSelector(selectIsEditPolicyModalOpen);
	const dispatch = useDispatch();

	function closeModal() {
		dispatch(closeIsEditPolicyModalOpen());
	}

	return (
		<Modal
			label="Edit Policy"
			show={isEditPolicyModalOpen}
			closeModal={closeModal}
			ModalBody={<EditPolicyForm closeModal={closeModal} />}
		/>
	);
}

export default EditPolicyModal;
