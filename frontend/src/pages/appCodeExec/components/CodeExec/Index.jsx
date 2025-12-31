import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams, useNavigate } from 'react-router-dom';
import useApi from '../../../../hooks/useApi';
import BreadCrumbs from '../../../app/components/BreadCrumbs';
import {
	setExecuteCodeModalOpen,
	setExecutionHistoryModalOpen,
	selectRerenderPage,
	selectAppCodeExecData,
	setAppCodeExecData,
	setSelectedCodeExec,
} from '../../slice/Index';
import ExecuteCodeModal from '../Modals/ExecuteCodeModal';
import ExecutionHistoryModal from '../Modals/ExecutionHistoryModal';
import CodeExecTable from '../table/Index';
import './Index.css';

export default function CodeExec() {
	const { appId } = useParams();
	const navigate = useNavigate();
	const dispatch = useDispatch();
	const triggerApi = useApi();

	const rerenderPage = useSelector(selectRerenderPage);
	const appCodeExecData = useSelector(selectAppCodeExecData);

	const [loading, setLoading] = useState(true);
	const [searchTerm, setSearchTerm] = useState('');
	const [page, setPage] = useState(1);
	const [pageSize] = useState(20);
	const [totalPages, setTotalPages] = useState(1);

	const updateAppCodeExecData = (value) => {
		dispatch(setAppCodeExecData(value));
	};

	// Fetch code executions data
	const fetchCodeExecutions = async () => {
		setLoading(true);
		try {
			const queryParams = new URLSearchParams({
				page: page.toString(),
				page_size: pageSize.toString(),
				search: searchTerm,
			});

			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/codeexec/?${queryParams.toString()}`,
				type: 'GET',
				loader: false,
			});

			if (success && response) {
				updateAppCodeExecData(response);
				setTotalPages(response.codeexecs?.total_pages || 1);
			}
		} catch (error) {
			console.error('Error fetching code executions:', error);
		} finally {
			setLoading(false);
		}
	};

	useEffect(() => {
		fetchCodeExecutions();
	}, [appId, page, searchTerm, rerenderPage]);

	const handleAddCodeExec = () => {
		navigate(`/platform/apps/${appId}/codeexec/new`);
	};

	const handleEditCodeExec = (codeexec) => {
		navigate(`/platform/apps/${appId}/codeexec/edit?id=${codeexec.id}`);
	};

	const handleExecuteCode = (codeexec) => {
		dispatch(setSelectedCodeExec(codeexec));
		dispatch(setExecuteCodeModalOpen(true));
	};

	const handleViewHistory = (codeexec) => {
		dispatch(setSelectedCodeExec(codeexec));
		dispatch(setExecutionHistoryModalOpen(true));
	};

	const handlePageChange = (newPage) => {
		setPage(newPage);
	};

	const handleSearch = (searchValue) => {
		setSearchTerm(searchValue);
		setPage(1);
	};

	return (
		<div className="codeexec-container">
			<BreadCrumbs
				breadcrumbs={[
					{ label: 'Apps', path: '/apps' },
					{ label: 'Code Execution', path: '' },
				]}
			/>

			<div className="codeexec-header">
				<div className="codeexec-title-section">
					<h1>Code Execution</h1>
					<p>Manage and execute code snippets</p>
				</div>
				<button
					className="btn btn-primary"
					onClick={handleAddCodeExec}
				>
					<span className="btn-icon">+</span> Add Code Execution
				</button>
			</div>

			<div className="codeexec-search-section">
				<input
					type="text"
					placeholder="Search code executions..."
					value={searchTerm}
					onChange={(e) => handleSearch(e.target.value)}
					className="search-input"
				/>
			</div>

			{loading ? (
				<div className="loading-container">
					<p>Loading code executions...</p>
				</div>
			) : (
				<>
					{appCodeExecData?.codeexecs?.records?.length > 0 ? (
						<>
							<CodeExecTable
								data={appCodeExecData?.codeexecs?.records || []}
								onEdit={handleEditCodeExec}
								onExecute={handleExecuteCode}
								onViewHistory={handleViewHistory}
							/>
							<div className="pagination-footer">
								<button
									disabled={page === 1}
									onClick={() => handlePageChange(page - 1)}
									className="pagination-btn pagination-prev"
								>
									← Previous
								</button>
								<span className="pagination-info">
									Page <span className="page-num">{page}</span> of <span className="page-num">{totalPages}</span>
								</span>
								<button
									disabled={page === totalPages}
									onClick={() => handlePageChange(page + 1)}
									className="pagination-btn pagination-next"
								>
									Next →
								</button>
							</div>
						</>
					) : (
						<div className="empty-state">
							<p>No code executions found</p>
							<button
								className="btn btn-primary"
								onClick={handleAddCodeExec}
							>
								Create your first code execution
							</button>
						</div>
					)}
				</>
			)}

			<ExecuteCodeModal />
			<ExecutionHistoryModal />
		</div>
	);
}
