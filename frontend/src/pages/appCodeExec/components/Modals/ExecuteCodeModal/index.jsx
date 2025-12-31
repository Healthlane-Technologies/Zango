import { useDispatch, useSelector } from 'react-redux';
import { useState } from 'react';
import { useParams } from 'react-router-dom';
import {
	selectIsExecuteCodeModalOpen,
	setExecuteCodeModalOpen,
	selectSelectedCodeExec,
	setExecutingCodeExecId,
} from '../../../slice/Index';
import { executeCode } from '../../../../../services/codeexecApi';
import '../shared.css';
import './index.css';

export default function ExecuteCodeModal() {
	const { appId } = useParams();
	const dispatch = useDispatch();
	const isOpen = useSelector(selectIsExecuteCodeModalOpen);
	const selectedCodeExec = useSelector(selectSelectedCodeExec);

	const [isExecuting, setIsExecuting] = useState(false);
	const [executionMessage, setExecutionMessage] = useState('');
	const [executionError, setExecutionError] = useState('');

	const handleClose = () => {
		dispatch(setExecuteCodeModalOpen(false));
		setExecutionMessage('');
		setExecutionError('');
	};

	const handleExecute = async () => {
		if (!selectedCodeExec) return;

		setIsExecuting(true);
		setExecutionMessage('');
		setExecutionError('');

		try {
			const response = await executeCode(appId, selectedCodeExec.id);

			if (response.ok) {
				const data = await response.json();
				if (data.success) {
					setExecutionMessage(
						'Code execution started. Check execution history for results.'
					);
					dispatch(setExecutingCodeExecId(selectedCodeExec.id));
					setTimeout(() => {
						handleClose();
					}, 2000);
				} else {
					setExecutionError(
						data.response?.message || 'Error executing code'
					);
				}
			} else {
				setExecutionError('Error executing code');
			}
		} catch (error) {
			console.error('Error executing code:', error);
			setExecutionError('Error executing code');
		} finally {
			setIsExecuting(false);
		}
	};

	if (!isOpen || !selectedCodeExec) return null;

	return (
		<div className="modal-overlay" onClick={handleClose}>
			<div className="modal-content" onClick={(e) => e.stopPropagation()}>
				<div className="modal-header">
					<h2>Execute Code</h2>
					<button className="modal-close-btn" onClick={handleClose}>
						✕
					</button>
				</div>
				<div className="modal-body execute-modal-body">
					{executionError && (
						<div className="form-error-message">
							{executionError}
						</div>
					)}
					{executionMessage && (
						<div className="form-success-message">
							{executionMessage}
						</div>
					)}

					<div className="execute-info">
						<p>
							<strong>Code Execution:</strong>{' '}
							{selectedCodeExec.name}
						</p>
						<p>
							<strong>Description:</strong>{' '}
							{selectedCodeExec.description || '-'}
						</p>
					</div>

					<div className="code-preview">
						<pre>
							<code>{selectedCodeExec.code}</code>
						</pre>
					</div>

					<p className="warning-text">
						⚠ This will execute the code asynchronously. Check
						the execution history for results.
					</p>

					<div className="form-actions">
						<button
							type="button"
							onClick={handleClose}
							className="btn btn-secondary"
							disabled={isExecuting}
						>
							Cancel
						</button>
						<button
							type="button"
							onClick={handleExecute}
							className="btn btn-primary btn-execute"
							disabled={isExecuting}
						>
							{isExecuting ? 'Executing...' : 'Execute Code'}
						</button>
					</div>
				</div>
			</div>
		</div>
	);
}
