import { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import useApi from '../../../../../hooks/useApi';
import { selectAppPackagesManagementFormData } from '../../../slice';

const ConfigurePackageForm = ({ closeModal }) => {
	let { appId } = useParams();
	const [iframeUrl, setIframeUrl] = useState('');

	const appPackagesManagementFormData = useSelector(
		selectAppPackagesManagementFormData
	);

	const triggerApi = useApi();

	useEffect(() => {
		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/packages/?action=config_url&package_name=${appPackagesManagementFormData?.name}`,
				type: 'GET',
				loader: true,
			});

			if (success && response) {
				setIframeUrl(response?.url);
			}
		};

		makeApiCall();
	}, []);

	return <iframe src={iframeUrl} width={'100%'} height={'100%'}></iframe>;
};

export default ConfigurePackageForm;
