import { useDispatch, useSelector } from 'react-redux';
import Modal from '../../../../../components/Modal';
import { close, selectIsLaunchNewAppModalOpen } from '../../../slice';
import LaunchNewAppForm from './LaunchNewAppForm';

export default function LaunchNewAppModal() {
	const isLaunchNewAppModalOpen = useSelector(selectIsLaunchNewAppModalOpen);
	const dispatch = useDispatch();

	function closeModal() {
		dispatch(close());
	}

	return (
		<>
			<Modal
				label="Launch New App"
				show={isLaunchNewAppModalOpen}
				closeModal={closeModal}
				ModalBody={<LaunchNewAppForm closeModal={closeModal} />}
			/>
		</>
	);
}
