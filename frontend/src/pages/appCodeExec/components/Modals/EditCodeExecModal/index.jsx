import { useDispatch, useSelector } from 'react-redux';
import {
	selectIsEditCodeExecModalOpen,
	setEditCodeExecModalOpen,
	selectSelectedCodeExec,
} from '../../../slice/Index';
import EditCodeExecForm from './EditCodeExecForm';
import '../shared.css';

export default function EditCodeExecModal() {
	const dispatch = useDispatch();
	const isOpen = useSelector(selectIsEditCodeExecModalOpen);
	const selectedCodeExec = useSelector(selectSelectedCodeExec);

	const handleClose = () => {
		dispatch(setEditCodeExecModalOpen(false));
	};

	if (!isOpen || !selectedCodeExec) return null;

	return (
		<div className="modal-overlay" onClick={handleClose}>
			<div className="modal-content" onClick={(e) => e.stopPropagation()}>
				<div className="modal-header">
					<h2>Edit Code Execution</h2>
					<button
						className="modal-close-btn"
						onClick={handleClose}
					>
						✕
					</button>
				</div>
				<div className="modal-body">
					<EditCodeExecForm
						codeexec={selectedCodeExec}
						onClose={handleClose}
					/>
				</div>
			</div>
		</div>
	);
}
