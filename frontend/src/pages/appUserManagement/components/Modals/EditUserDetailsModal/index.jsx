import { useDispatch, useSelector } from 'react-redux';
import Modal from '../../../../../components/Modal';
import {
	closeIsEditUserDetailModalOpen,
	selectIsEditUserDetailModalOpen,
} from '../../../slice';
import EditUserDetailsForm from './EditUserDetailsForm';

function EditUserDetailsModal() {
	const isEditUserDetailModalOpen = useSelector(
		selectIsEditUserDetailModalOpen
	);
	const dispatch = useDispatch();

	function closeModal() {
		dispatch(closeIsEditUserDetailModalOpen());
	}

	return (
		<Modal
			label="Edit User Details"
			show={isEditUserDetailModalOpen}
			closeModal={closeModal}
			ModalBody={<EditUserDetailsForm closeModal={closeModal} />}
		/>
	);
}

export default EditUserDetailsModal;
