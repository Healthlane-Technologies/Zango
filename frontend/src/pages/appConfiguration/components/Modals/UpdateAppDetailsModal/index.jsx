import { useDispatch, useSelector } from 'react-redux';
import Modal from '../../../../../components/Modal';
import {
	closeIsUpdateAppDetailsModalOpen,
	selectIsUpdateAppDetailsModalOpen,
} from '../../../slice';
import UpdateAppDetailsForm from './UpdateAppDetailsForm';

function UpdateAppDetailsModal() {
	const isUpdateAppDetailsModalOpen = useSelector(
		selectIsUpdateAppDetailsModalOpen
	);
	const dispatch = useDispatch();

	function closeModal() {
		dispatch(closeIsUpdateAppDetailsModalOpen());
	}

	return (
		<Modal
			label="Update App Details"
			show={isUpdateAppDetailsModalOpen}
			closeModal={closeModal}
			ModalBody={<UpdateAppDetailsForm closeModal={closeModal} />}
		/>
	);
}

export default UpdateAppDetailsModal;
