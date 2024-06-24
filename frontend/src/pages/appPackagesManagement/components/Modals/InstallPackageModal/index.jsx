import { useDispatch, useSelector } from 'react-redux';
import Modal from '../../../../../components/Modal';
import {
	closeIsInstallPackageModalOpen,
	selectIsInstallPackageModalOpen,
} from '../../../slice';
import InstallPackageForm from './InstallPackageForm';

function InstallPackageModal() {
	const isInstallPackageModalOpen = useSelector(
		selectIsInstallPackageModalOpen
	);
	const dispatch = useDispatch();

	function closeModal() {
		dispatch(closeIsInstallPackageModalOpen());
	}

	return (
		<Modal
			label={'Install Package'}
			show={isInstallPackageModalOpen}
			closeModal={closeModal}
			ModalBody={<InstallPackageForm closeModal={closeModal} />}
		/>
	);
}

export default InstallPackageModal;
