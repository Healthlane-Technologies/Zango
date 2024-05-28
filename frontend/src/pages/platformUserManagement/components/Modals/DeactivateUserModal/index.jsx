import { useDispatch, useSelector } from 'react-redux';
import Modal from '../../../../../components/Modal';
import {
	closeIsDeactivateUserModalOpen,
	selectIsDeactivateUserModalOpen,
	selectPlatformUserManagementFormData,
} from '../../../slice';
import DeactivateUserForm from './DeactivateUserForm';

function DeactivateUserModal() {
	const isDeactivateUserModalOpen = useSelector(
		selectIsDeactivateUserModalOpen
	);
	const platformUserManagementFormData = useSelector(
		selectPlatformUserManagementFormData
	);

	const dispatch = useDispatch();

	function closeModal() {
		dispatch(closeIsDeactivateUserModalOpen());
	}

	return (
		<>
			<Modal
				label={`Deactivate ${platformUserManagementFormData?.name}’s Profile`}
				show={isDeactivateUserModalOpen}
				closeModal={closeModal}
				ModalBody={<DeactivateUserForm closeModal={closeModal} />}
			/>
		</>
	);
}

export default DeactivateUserModal;
