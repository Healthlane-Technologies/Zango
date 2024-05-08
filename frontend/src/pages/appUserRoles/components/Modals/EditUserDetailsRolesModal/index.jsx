import { useDispatch, useSelector } from 'react-redux';
import Modal from '../../../../../components/Modal';
import {
	closeIsEditUserRolesDetailModalOpen,
	selectIsEditUserRolesDetailModalOpen,
} from '../../../slice';
import EditUserRolesDetailsForm from './EditUserRolesDetailsForm';

function EditUserRolesDetailsModal() {
	const isEditUserRolesDetailModalOpen = useSelector(
		selectIsEditUserRolesDetailModalOpen
	);
	const dispatch = useDispatch();

	function closeModal() {
		dispatch(closeIsEditUserRolesDetailModalOpen());
	}

	return (
		<>
			<Modal
				label="Edit User Role"
				show={isEditUserRolesDetailModalOpen}
				closeModal={closeModal}
				ModalBody={<EditUserRolesDetailsForm closeModal={closeModal} />}
			/>
		</>
	);
}

export default EditUserRolesDetailsModal;
