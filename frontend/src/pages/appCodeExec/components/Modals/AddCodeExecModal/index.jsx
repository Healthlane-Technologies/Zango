import { useDispatch, useSelector } from 'react-redux';
import {
	selectIsAddCodeExecModalOpen,
	setAddCodeExecModalOpen,
} from '../../../slice/Index';
import AddCodeExecForm from './AddCodeExecForm';
import '../shared.css';

export default function AddCodeExecModal() {
	const dispatch = useDispatch();
	const isOpen = useSelector(selectIsAddCodeExecModalOpen);

	const handleClose = () => {
		dispatch(setAddCodeExecModalOpen(false));
	};

	if (!isOpen) return null;

	return (
		<div className="modal-overlay" onClick={handleClose}>
			<div className="modal-content" onClick={(e) => e.stopPropagation()}>
				<div className="modal-header">
					<h2>Add Code Execution</h2>
					<button
						className="modal-close-btn"
						onClick={handleClose}
					>
						✕
					</button>
				</div>
				<div className="modal-body">
					<AddCodeExecForm onClose={handleClose} />
				</div>
			</div>
		</div>
	);
}
