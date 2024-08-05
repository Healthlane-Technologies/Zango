import { useState } from 'react';
import { useDispatch } from 'react-redux';
import { useParams } from 'react-router-dom';
import { ReactComponent as TableSyncIcon } from '../../../assets/images/svg/sync-icon.svg';
import useApi from '../../../hooks/useApi';
import { transformToFormData } from '../../../utils/form';
import { toggleRerenderPage } from '../slice';

export default function SyncTask({ theme = 'light' }) {
	let { appId } = useParams();

	const [isLoading, setIsLoading] = useState(false);
	const dispatch = useDispatch();
	const triggerApi = useApi();

	let handleSyncTaskClick = () => {
		let dynamicFormData = transformToFormData({});

		setIsLoading(true);
		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/tasks/?action=sync_tasks`,
				type: 'POST',
				loader: false,
				notify: true,
				payload: dynamicFormData,
			});

			if (success && response) {
				dispatch(toggleRerenderPage());
				setIsLoading(false);
			} else {
				setIsLoading(false);
			}
		};

		makeApiCall();
	};

	return (
		<div className="flex items-center gap-[16px]">
			<button
				data-cy="sync_task_button"
				type="button"
				className={`flex items-center gap-[12px] ${
					theme === 'light'
						? 'bg-transparent'
						: 'rounded-[4px] bg-primary px-[16px] py-[7px]'
				}`}
				onClick={handleSyncTaskClick}
			>
				<span
					className={`font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] ${
						theme === 'light' ? 'text-primary' : 'text-[#fff]'
					}`}
				>
					Sync Task
				</span>
				<TableSyncIcon
					className={`h-[20px] min-h-[20px] w-[20px] min-w-[20px] ${
						theme === 'light' ? 'text-primary' : 'text-[#fff]'
					} ${isLoading ? 'animate-spin' : ''}`}
				/>
			</button>
		</div>
	);
}
