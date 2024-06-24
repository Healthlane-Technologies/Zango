import { useDispatch, useSelector } from 'react-redux';
import Modal from '../../../../../components/Modal';
import {
	closeIsRemoveAllPoliciesModalOpen,
	selectIsRemoveAllPoliciesModalOpen,
} from '../../../slice';
import RemoveAllPoliciesForm from './RemoveAllPoliciesForm';

function RemoveAllPoliciesModal() {
	const isRemoveAllPoliciesModalOpen = useSelector(
		selectIsRemoveAllPoliciesModalOpen
	);
	const dispatch = useDispatch();

	function closeModal() {
		dispatch(closeIsRemoveAllPoliciesModalOpen());
	}

	return (
		<>
			<Modal
				label="Remove all asdPolicies"
				show={isRemoveAllPoliciesModalOpen}
				closeModal={closeModal}
				ModalBody={<RemoveAllPoliciesForm closeModal={closeModal} />}
			/>
		</>
	);
}

export default RemoveAllPoliciesModal;
