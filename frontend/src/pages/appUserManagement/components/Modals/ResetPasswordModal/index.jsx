import { useDispatch, useSelector } from 'react-redux';
import StandardModal from '../../../../../components/StandardModal';
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
		<StandardModal
			label="Reset Password"
			show={isResetPasswordModalOpen}
			closeModal={closeModal}
			size="default"
			ModalBody={<ResetPasswordForm closeModal={closeModal} />}
		/>
	);
}

export default ResetPasswordModal;
