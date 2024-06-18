import { useDispatch, useSelector } from 'react-redux';
import Modal from '../../../../../components/Modal';
import {
	closeIsDeactivateUserRolesModalOpen,
	selectAppUserRolesFormData,
	selectIsDeactivateUserRolesModalOpen,
} from '../../../slice';
import DeactivateUserRolesForm from './DeactivateUserRolesForm';

function DeactivateUserRolesModal() {
	const isDeactivateUserRolesModalOpen = useSelector(
		selectIsDeactivateUserRolesModalOpen
	);
	const appUserRolesFormData = useSelector(selectAppUserRolesFormData);

	const dispatch = useDispatch();

	function closeModal() {
		dispatch(closeIsDeactivateUserRolesModalOpen());
	}

	return (
		<Modal
			label={`Deactivate ${appUserRolesFormData?.name}`}
			show={isDeactivateUserRolesModalOpen}
			closeModal={closeModal}
			ModalBody={<DeactivateUserRolesForm closeModal={closeModal} />}
		/>
	);
}

export default DeactivateUserRolesModal;
