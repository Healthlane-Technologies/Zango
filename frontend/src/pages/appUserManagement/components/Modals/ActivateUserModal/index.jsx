import { useDispatch, useSelector } from 'react-redux';
import Modal from '../../../../../components/Modal';
import {
	closeIsActivateUserModalOpen,
	selectAppUserManagementFormData,
	selectIsActivateUserModalOpen,
} from '../../../slice';
import ActivateUserForm from './ActivateUserForm';

function ActivateUserModal() {
	const appUserManagementFormData = useSelector(
		selectAppUserManagementFormData
	);
	const isActivateUserModalOpen = useSelector(selectIsActivateUserModalOpen);
	const dispatch = useDispatch();

	function closeModal() {
		dispatch(closeIsActivateUserModalOpen());
	}

	return (
		<>
			<Modal
				label={`Activate ${appUserManagementFormData?.name}`}
				show={isActivateUserModalOpen}
				closeModal={closeModal}
				ModalBody={<ActivateUserForm closeModal={closeModal} />}
			/>
		</>
	);
}

export default ActivateUserModal;
