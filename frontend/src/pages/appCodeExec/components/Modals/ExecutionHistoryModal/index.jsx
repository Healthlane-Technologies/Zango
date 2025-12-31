import { useDispatch, useSelector } from 'react-redux';
import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
	selectIsExecutionHistoryModalOpen,
	setExecutionHistoryModalOpen,
	selectSelectedCodeExec,
} from '../../../slice/Index';
import { getExecutionHistory } from '../../../../../services/codeexecApi';
import '../shared.css';
import './index.css';

export default function ExecutionHistoryModal() {
	const { appId } = useParams();
	const dispatch = useDispatch();
	const isOpen = useSelector(selectIsExecutionHistoryModalOpen);
	const selectedCodeExec = useSelector(selectSelectedCodeExec);

	const [executionHistory, setExecutionHistory] = useState([]);
	const [loading, setLoading] = useState(false);

	const handleClose = () => {
		dispatch(setExecutionHistoryModalOpen(false));
	};

	useEffect(() => {
		if (isOpen && selectedCodeExec) {
			fetchExecutionHistory();
		}
	}, [isOpen, selectedCodeExec]);

	const fetchExecutionHistory = async () => {
		setLoading(true);
		try {
			const response = await getExecutionHistory(
				appId,
				selectedCodeExec.id
			);

			if (response.ok) {
				const data = await response.json();
				if (data.success) {
					setExecutionHistory(
						data.response?.execution_history || []
					);
				}
			}
		} catch (error) {
			console.error('Error fetching execution history:', error);
		} finally {
			setLoading(false);
		}
	};

	if (!isOpen || !selectedCodeExec) return null;

	return (
		<div className="modal-overlay" onClick={handleClose}>
			<div className="modal-content" onClick={(e) => e.stopPropagation()}>
				<div className="modal-header">
					<h2>Execution History</h2>
					<button className="modal-close-btn" onClick={handleClose}>
						✕
					</button>
				</div>
				<div className="modal-body history-modal-body">
					<div className="history-info">
						<p>
							<strong>Code Execution:</strong>{' '}
							{selectedCodeExec.name}
						</p>
					</div>

					{loading ? (
						<p className="loading-text">Loading execution history...</p>
					) : executionHistory.length === 0 ? (
						<p className="empty-text">
							No executions yet. Execute the code to see history.
						</p>
					) : (
						<div className="history-list">
							{executionHistory.map((execution, index) => (
								<ExecutionItem
									key={index}
									execution={execution}
									index={index}
								/>
							))}
						</div>
					)}

					<div className="form-actions">
						<button
							type="button"
							onClick={handleClose}
							className="btn btn-primary"
						>
							Close
						</button>
					</div>
				</div>
			</div>
		</div>
	);
}

function ExecutionItem({ execution, index }) {
	const [expanded, setExpanded] = useState(false);

	const getStatusColor = (status) => {
		switch (status) {
			case 'COMPLETED':
				return 'status-completed';
			case 'FAILED':
				return 'status-failed';
			case 'STAGED':
				return 'status-running';
			default:
				return 'status-unknown';
		}
	};

	return (
		<div className="execution-item">
			<button
				className="execution-header"
				onClick={() => setExpanded(!expanded)}
			>
				<div className="execution-title">
					<span className={`status-indicator ${getStatusColor(execution.status)}`}>
						{execution.status}
					</span>
					<span className="execution-index">Execution #{index + 1}</span>
				</div>
				<div className="execution-times">
					<span className="execution-time">
						Start: {execution.start_time || '-'}
					</span>
					<span className="execution-time">
						End: {execution.end_time || 'Running...'}
					</span>
				</div>
				<span className="expand-icon">{expanded ? '▼' : '▶'}</span>
			</button>

			{expanded && (
				<div className="execution-details">
					{execution.logger && (
						<div className="execution-section">
							<h4>Logger Output</h4>
							<pre className="logger-output">
								{JSON.stringify(execution.logger, null, 2)}
							</pre>
						</div>
					)}

					{execution.traceback && (
						<div className="execution-section error-section">
							<h4>Error Traceback</h4>
							<pre className="error-output">
								{execution.traceback}
							</pre>
						</div>
					)}

					{!execution.logger && !execution.traceback && (
						<p className="no-details">No additional details</p>
					)}
				</div>
			)}
		</div>
	);
}
