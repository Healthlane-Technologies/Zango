import { useDispatch, useSelector } from 'react-redux';
import Modal from '../../../../../components/Modal';
import {
	closeIsDeactivateUserModalOpen,
	selectAppUserManagementFormData,
	selectIsDeactivateUserModalOpen,
} from '../../../slice';
import DeactivateUserForm from './DeactivateUserForm';

function DeactivateUserModal() {
	const isDeactivateUserModalOpen = useSelector(
		selectIsDeactivateUserModalOpen
	);
	const appUserManagementFormData = useSelector(
		selectAppUserManagementFormData
	);
	const dispatch = useDispatch();

	function closeModal() {
		dispatch(closeIsDeactivateUserModalOpen());
	}

	return (
		<Modal
			label={`Deactivate ${appUserManagementFormData?.name}'s Profile`}
			show={isDeactivateUserModalOpen}
			closeModal={closeModal}
			ModalBody={<DeactivateUserForm closeModal={closeModal} />}
		/>
	);
}

export default DeactivateUserModal;
