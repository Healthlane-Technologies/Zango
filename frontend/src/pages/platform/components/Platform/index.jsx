import FirstApp from './FirstApp';
import LaunchNewAppModal from '../Models/LaunchNewAppModal';
import Apps from './Apps';
import useApi from '../../../../hooks/useApi';
import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
	setAppsData,
	selectAppsData,
	selectRerenderPage,
	selectSortBy,
	selectPollingTaskIds,
	toggleRerenderPage,
} from '../../slice';
import { orderBy } from 'lodash';

export default function Platform() {
	const appsData = useSelector(selectAppsData);
	const rerenderPage = useSelector(selectRerenderPage);
	const sortBy = useSelector(selectSortBy);
	const pollingTaskIds = useSelector(selectPollingTaskIds);
	const dispatch = useDispatch();

	function updateAppsData(value) {
		dispatch(setAppsData(value));
	}

	const triggerApi = useApi();

	useEffect(() => {
		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				let filteredData = {
					alphabetical: orderBy(
						[...response.apps],
						[(app) => app.name.toLowerCase()],
						'asc'
					),
					date_created: orderBy([...response.apps], 'created_at', 'desc'),
					last_modified: orderBy([...response.apps], 'modified_at', 'desc'),
				}[sortBy];
				updateAppsData([...filteredData]);
			}
		};

		makeApiCall();

		if (pollingTaskIds?.length) {
			pollingTaskIds?.map((eachTaskId) => {
				if (window[`task${eachTaskId.split('-').join('')}`]) {
				} else {
					window[`task${eachTaskId.split('-').join('')}`] = setInterval(() => {
						const makeTaskApiCall = async () => {
							const { response, success } = await triggerApi({
								url: `/api/v1/apps/?action=get_app_creation_status&task_id=${eachTaskId}`,
								type: 'GET',
								loader: false,
							});
							if (success && response) {
								if (
									response?.status === 'Deployed' ||
									response?.status === 'Failed'
								) {
									clearInterval(
										window[`task${eachTaskId.split('-').join('')}`]
									);
									dispatch(toggleRerenderPage());
								}
							}
						};

						makeTaskApiCall();
					}, 5000);
				}
			});
		}
	}, [rerenderPage, sortBy]);

	if (appsData) {
		return (
			<>
				{appsData?.length ? <Apps /> : <FirstApp />}
				<LaunchNewAppModal />
			</>
		);
	} else {
		return null;
	}
}
