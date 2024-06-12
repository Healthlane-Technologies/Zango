import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import useApi from '../../../../hooks/useApi';
import BreadCrumbs from '../../../app/components/BreadCrumbs';
import {
	selectAppConfigurationData,
	selectRerenderPage,
	setAppConfigurationData,
} from '../../slice';
import UpdateAppDetailsModal from '../Modals/UpdateAppDetailsModal';
import DetailsTable from './DetailsTable';
import UpdateAppDetailsButton from './UpdateAppDetailsButton';

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

	return (
		<>
			<div className="flex grow flex-col gap-[40px]">
				<div className="flex items-center justify-between pb-[24px] pl-[40px] pr-[48px] pt-[22px]">
					<BreadCrumbs />
				</div>
				<div className="flex grow flex-col gap-[20px] pl-[40px] pr-[48px]">
					<div className="flex items-end gap-[24px]">
						<h3 data-cy="app_name_details_view" className="font-source-sans-pro text-[22px] font-semibold leading-[28px] text-[#000000]">
							{appConfigurationData?.app?.name}
						</h3>
						<UpdateAppDetailsButton />
					</div>
					<DetailsTable />
				</div>
			</div>
			<UpdateAppDetailsModal />
		</>
	);
}
