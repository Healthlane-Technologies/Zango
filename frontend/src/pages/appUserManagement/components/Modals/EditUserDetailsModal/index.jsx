import { useDispatch, useSelector } from 'react-redux';
import StandardModal from '../../../../../components/StandardModal';
import {
	closeIsEditUserDetailModalOpen,
	selectIsEditUserDetailModalOpen,
} from '../../../slice';
import EditUserDetailsForm from './EditUserDetailsForm';

function EditUserDetailsModal() {
	const isEditUserDetailModalOpen = useSelector(
		selectIsEditUserDetailModalOpen
	);
	const dispatch = useDispatch();

	function closeModal() {
		dispatch(closeIsEditUserDetailModalOpen());
	}

	return (
		<StandardModal
			label="Edit User Details"
			show={isEditUserDetailModalOpen}
			closeModal={closeModal}
			size="lg"
			ModalBody={<EditUserDetailsForm closeModal={closeModal} />}
		/>
	);
}

export default EditUserDetailsModal;
