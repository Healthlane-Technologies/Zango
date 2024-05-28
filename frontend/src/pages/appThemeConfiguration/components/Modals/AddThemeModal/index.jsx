import { useDispatch, useSelector } from 'react-redux';
import Modal from '../../../../../components/Modal';
import {
	closeIsAddThemeModalOpen,
	selectIsAddThemeModalOpen,
} from '../../../slice';
import AddThemeForm from './AddThemeForm';

function AddThemeModal() {
	const isAddThemeModalOpen = useSelector(selectIsAddThemeModalOpen);
	const dispatch = useDispatch();

	function closeModal() {
		dispatch(closeIsAddThemeModalOpen());
	}

	return (
		<Modal
			label="Add App Theme"
			show={isAddThemeModalOpen}
			closeModal={closeModal}
			ModalBody={<AddThemeForm closeModal={closeModal} />}
		/>
	);
}

export default AddThemeModal;
