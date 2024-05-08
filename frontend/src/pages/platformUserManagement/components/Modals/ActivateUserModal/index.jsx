import { useDispatch, useSelector } from 'react-redux';
import Modal from '../../../../../components/Modal';
import {
	closeIsActivateUserModalOpen,
	selectIsActivateUserModalOpen,
	selectPlatformUserManagementFormData,
} from '../../../slice';
import ActivateUserForm from './ActivateUserForm';

export default function ActivateUserModal() {
	const platformUserManagementFormData = useSelector(
		selectPlatformUserManagementFormData
	);
	const isActivateUserModalOpen = useSelector(selectIsActivateUserModalOpen);
	const dispatch = useDispatch();

	function closeModal() {
		dispatch(closeIsActivateUserModalOpen());
	}

	return (
		<Modal
			label={`Activate ${platformUserManagementFormData?.name}`}
			show={isActivateUserModalOpen}
			closeModal={closeModal}
			ModalBody={<ActivateUserForm closeModal={closeModal} />}
		/>
	);
}
