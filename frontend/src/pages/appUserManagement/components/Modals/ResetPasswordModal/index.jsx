import { useDispatch, useSelector } from 'react-redux';
import Modal from '../../../../../components/Modal';
import {
	closeIsResetPasswordModalOpen,
	selectIsResetPasswordModalOpen,
} from '../../../slice';
import ResetPasswordForm from './ResetPasswordForm';

function ResetPasswordModal() {
	const isResetPasswordModalOpen = useSelector(selectIsResetPasswordModalOpen);
	const dispatch = useDispatch();

	function closeModal() {
		dispatch(closeIsResetPasswordModalOpen());
	}

	return (
		<Modal
			label="Reset Password"
			show={isResetPasswordModalOpen}
			closeModal={closeModal}
			ModalBody={<ResetPasswordForm closeModal={closeModal} />}
		/>
	);
}

export default ResetPasswordModal;
