import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import useApi from '../../../../hooks/useApi';
import {
	selectAppConfigurationData,
	selectRerenderPage,
	setAppConfigurationData,
} from '../../slice';
import ModernAppConfiguration from './ModernAppConfiguration';

export default function AppConfiguration() {
	let { appId } = useParams();
	const rerenderPage = useSelector(selectRerenderPage);

	const appConfigurationData = useSelector(selectAppConfigurationData);

	const dispatch = useDispatch();

	function updateAppConfigurationData(value) {
		dispatch(setAppConfigurationData(value));
	}

	const triggerApi = useApi();

	useEffect(() => {
		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}?include_dropdown_options=true`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				updateAppConfigurationData(response);
			}
		};

		makeApiCall();
	}, [rerenderPage]);

	if (!appConfigurationData) {
		return null;
	}

	return <ModernAppConfiguration />;
}
