import { orderBy } from 'lodash';
import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import useApi from '../../../../hooks/useApi';
import {
	selectAppsData,
	selectPollingTaskIds,
	selectRerenderPage,
	selectSortBy,
	setAppsData,
	toggleRerenderPage,
} from '../../slice';
import LaunchNewAppModal from '../Modals/LaunchNewAppModal';
import Apps from './Apps';
import LandingPage from './LandingPage';

export default function Platform() {
	const appsData = useSelector(selectAppsData);
	const rerenderPage = useSelector(selectRerenderPage);
	const sortBy = useSelector(selectSortBy);
	const pollingTaskIds = useSelector(selectPollingTaskIds);
	const dispatch = useDispatch();
	const triggerApi = useApi();

	function updateAppsData(value) {
		dispatch(setAppsData(value));
	}

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

	const makeTaskApiCall = async (eachTaskId) => {
		const { response, success } = await triggerApi({
			url: `/api/v1/apps/?action=get_app_creation_status&task_id=${eachTaskId}`,
			type: 'GET',
			loader: false,
		});
		if (success && response) {
			if (response?.status === 'Deployed' || response?.status === 'Failed') {
				clearInterval(window[`task${eachTaskId.split('-').join('')}`]);
				dispatch(toggleRerenderPage());
			}
		}
	};

	useEffect(() => {
		makeApiCall();

		if (pollingTaskIds?.length) {
			pollingTaskIds?.map((eachTaskId) => {
				if (window[`task${eachTaskId.split('-').join('')}`]) {
				} else {
					window[`task${eachTaskId.split('-').join('')}`] = setInterval(() => {
						makeTaskApiCall(eachTaskId);
					}, 5000);
				}
			});
		}
	}, [rerenderPage, sortBy]);

	if (appsData) {
		return (
			<>
				{appsData?.length ? <Apps /> : <LandingPage />}
				<LaunchNewAppModal />
			</>
		);
	} else {
		return null;
	}
}
