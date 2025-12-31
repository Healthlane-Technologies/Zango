import { useState, useRef, useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { useParams } from 'react-router-dom';
import { toggleRerenderPage } from '../../slice/Index';
import { deleteCodeExecution } from '../../../../services/codeexecApi';
import './RowMenu.css';

export default function RowMenu({ codeexec, onEdit, onExecute, onViewHistory }) {
	const [menuOpen, setMenuOpen] = useState(false);
	const [isDeleting, setIsDeleting] = useState(false);
	const [menuPosition, setMenuPosition] = useState({ top: 0, left: 0 });
	const buttonRef = useRef(null);
	const dispatch = useDispatch();
	const { appId } = useParams();

	const handleMenuToggle = () => {
		if (!menuOpen && buttonRef.current) {
			const rect = buttonRef.current.getBoundingClientRect();
			setMenuPosition({
				top: rect.bottom + 5,
				left: rect.left - 100,
			});
		}
		setMenuOpen(!menuOpen);
	};

	useEffect(() => {
		const handleClickOutside = (event) => {
			if (buttonRef.current && !buttonRef.current.contains(event.target)) {
				setMenuOpen(false);
			}
		};

		if (menuOpen) {
			document.addEventListener('click', handleClickOutside);
		}

		return () => {
			document.removeEventListener('click', handleClickOutside);
		};
	}, [menuOpen]);

	const handleEdit = () => {
		onEdit();
		setMenuOpen(false);
	};

	const handleExecute = () => {
		onExecute();
		setMenuOpen(false);
	};

	const handleViewHistory = () => {
		onViewHistory();
		setMenuOpen(false);
	};

	const handleDelete = async () => {
		if (!window.confirm('Are you sure you want to delete this code execution?')) {
			return;
		}

		setIsDeleting(true);
		try {
			const response = await deleteCodeExecution(appId, codeexec.id);

			if (response.ok) {
				dispatch(toggleRerenderPage());
				setMenuOpen(false);
			} else {
				alert('Error deleting code execution');
			}
		} catch (error) {
			console.error('Error deleting code execution:', error);
			alert('Error deleting code execution');
		} finally {
			setIsDeleting(false);
		}
	};

	return (
		<div className="row-menu-container">
			<button
				ref={buttonRef}
				className="menu-toggle-btn"
				onClick={handleMenuToggle}
				title="Actions"
			>
				⋮
			</button>

			{menuOpen && (
				<div
					className="menu-dropdown"
					style={{
						top: `${menuPosition.top}px`,
						left: `${menuPosition.left}px`,
					}}
				>
					<button
						className="menu-item"
						onClick={handleEdit}
					>
						✎ Edit
					</button>
					<button
						className="menu-item"
						onClick={handleExecute}
					>
						▶ Execute
					</button>
					<button
						className="menu-item"
						onClick={handleViewHistory}
					>
						📋 View History
					</button>
					<div className="menu-divider"></div>
					<button
						className="menu-item menu-item-danger"
						onClick={handleDelete}
						disabled={isDeleting}
					>
						🗑 Delete
					</button>
				</div>
			)}
		</div>
	);
}
