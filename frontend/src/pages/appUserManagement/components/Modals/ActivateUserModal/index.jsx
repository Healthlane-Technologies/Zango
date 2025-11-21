import { useDispatch, useSelector } from 'react-redux';
import StandardModal from '../../../../../components/StandardModal';
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
			<StandardModal
				label={`Activate ${appUserManagementFormData?.name}`}
				show={isActivateUserModalOpen}
				closeModal={closeModal}
				size="sm"
				ModalBody={<ActivateUserForm closeModal={closeModal} />}
			/>
		</>
	);
}

export default ActivateUserModal;
