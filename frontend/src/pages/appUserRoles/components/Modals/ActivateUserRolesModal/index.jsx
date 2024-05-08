import { useDispatch, useSelector } from 'react-redux';
import Modal from '../../../../../components/Modal';
import {
	closeIsActivateUserRolesModalOpen,
	selectAppUserRolesFormData,
	selectIsActivateUserRolesModalOpen,
} from '../../../slice';
import ActivateUserRolesForm from './ActivateUserRolesForm';

function ActivateUserRolesModal() {
	const appUserRolesFormData = useSelector(selectAppUserRolesFormData);
	const isActivateUserRolesModalOpen = useSelector(
		selectIsActivateUserRolesModalOpen
	);
	const dispatch = useDispatch();

	function closeModal() {
		dispatch(closeIsActivateUserRolesModalOpen());
	}

	return (
		<Modal
			label={`Activate ${appUserRolesFormData?.name}`}
			show={isActivateUserRolesModalOpen}
			closeModal={closeModal}
			ModalBody={<ActivateUserRolesForm closeModal={closeModal} />}
		/>
	);
}

export default ActivateUserRolesModal;
