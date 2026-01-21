import { useDispatch, useSelector } from 'react-redux';
import Modal from '../../../../../components/Modal';
import {
	closeIsEditUserRolesDetailModalOpen,
	selectIsEditUserRolesDetailModalOpen,
	selectAppUserRolesFormData,
} from '../../../slice';
import EditUserRolesDetailsForm from './EditUserRolesDetailsForm';

function EditUserRolesDetailsModal() {
	const isEditUserRolesDetailModalOpen = useSelector(
		selectIsEditUserRolesDetailModalOpen
	);
	const appUserRolesFormData = useSelector(selectAppUserRolesFormData);
	const dispatch = useDispatch();
	
	// Check if this is a reserved role
	const isReservedRole = appUserRolesFormData?.name === 'AnonymousUsers' || appUserRolesFormData?.name === 'SystemUsers';

	function closeModal() {
		dispatch(closeIsEditUserRolesDetailModalOpen());
	}

	return (
		<>
			<Modal
				label={isReservedRole ? "Edit Role Policies" : "Edit User Role"}
				show={isEditUserRolesDetailModalOpen}
				closeModal={closeModal}
				ModalBody={<EditUserRolesDetailsForm closeModal={closeModal} />}
			/>
		</>
	);
}

export default EditUserRolesDetailsModal;
