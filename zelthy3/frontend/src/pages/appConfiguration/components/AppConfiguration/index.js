import BreadCrumbs from '../BreadCrumbs';
import { useSelector, useDispatch } from 'react-redux';
import {
	openIsUpdateAppDetailsModalOpen,
	selectAppConfigurationData,
	selectRerenderPage,
	setAppConfigurationData,
} from '../../slice';

import { ReactComponent as EachAppIcon } from '../../../../assets/images/svg/each-app-icon.svg';
import UpdateAppDetailsModal from '../Models/UpdateAppDetailsModal';
import useApi from '../../../../hooks/useApi';
import { useEffect } from 'react';
import { useParams } from 'react-router-dom';

export default function AppConfiguration() {
	let { appId } = useParams();
	const rerenderPage = useSelector(selectRerenderPage);

	const appConfigurationData = useSelector(selectAppConfigurationData);

	const dispatch = useDispatch();

	const handleUpdateAppDetails = () => {
		dispatch(openIsUpdateAppDetailsModalOpen());
	};

	function updateAppConfigurationData(value) {
		dispatch(setAppConfigurationData(value));
	}

	const triggerApi = useApi();

	useEffect(() => {
		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				updateAppConfigurationData(response);
			}
		};

		makeApiCall();
	}, [rerenderPage]);

	return (
		<>
			<div className="flex grow flex-col gap-[40px]">
				<div className="flex items-center justify-between pt-[22px] pb-[24px] pl-[40px] pr-[48px]">
					<BreadCrumbs />
				</div>
				<div className="flex grow flex-col gap-[20px] pl-[40px] pr-[48px]">
					<div className="flex items-end gap-[24px]">
						<h3 className="font-source-sans-pro text-[22px] font-semibold leading-[28px] text-[#000000]">
							{appConfigurationData?.apps?.name}
						</h3>
						<button
							type="button"
							onClick={handleUpdateAppDetails}
							className="flex"
						>
							<span className="font-lato text-[14px] font-bold leading-[20px] text-primary">
								update details
							</span>
						</button>
					</div>
					<table className="w-100 border-spacing-x-4">
						<tbody>
							<tr className="py-[4px] first:pb-[4px] last:pt-[4px]">
								<td className="align-baseline">
									<span className="whitespace-nowrap font-lato text-[14px] leading-[20px] tracking-[0.2px] text-[#A3ABB1]">
										App Description:
									</span>
								</td>
								<td className="w-full pl-[20px]">
									<span className="whitespace-nowrap font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
										{appConfigurationData?.apps?.description}
									</span>
								</td>
							</tr>
							<tr className="py-[4px] first:pb-[4px] last:pt-[4px]">
								<td className="align-baseline">
									<span className="whitespace-nowrap font-lato text-[14px] leading-[20px] tracking-[0.2px] text-[#A3ABB1]">
										Logo:
									</span>
								</td>
								<td className="w-full pl-[20px]">
									{appConfigurationData?.apps?.logo ? (
										<img
											src={appConfigurationData?.apps?.logo}
											className="h-[56px] w-[56px]"
											alt="#"
										/>
									) : (
										<EachAppIcon className="h-[56px] w-[56px]" />
									)}
								</td>
							</tr>
							<tr className="py-[4px] first:pb-[4px] last:pt-[4px]">
								<td className="align-baseline">
									<span className="whitespace-nowrap font-lato text-[14px] leading-[20px] tracking-[0.2px] text-[#A3ABB1]">
										Fav Icon:
									</span>
								</td>
								<td className="w-full pl-[20px]">
									{appConfigurationData?.apps?.fav_icon ? (
										<img
											src={appConfigurationData?.apps?.fav_icon}
											className="h-[56px] w-[56px]"
											alt="#"
										/>
									) : (
										<EachAppIcon className="h-[56px] w-[56px]" />
									)}
								</td>
							</tr>
							<tr className="py-[4px] first:pb-[4px] last:pt-[4px]">
								<td className="align-baseline">
									<span className="whitespace-nowrap font-lato text-[14px] leading-[20px] tracking-[0.2px] text-[#A3ABB1]">
										Domain:
									</span>
								</td>
								<td className="w-full pl-[20px]">
									<div className="flex flex-col gap-[8px]">
										{appConfigurationData?.apps?.domains?.map((eachDomain) => {
											return (
												<span className="whitespace-nowrap font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
													{eachDomain}
												</span>
											);
										})}
									</div>
								</td>
							</tr>
							<tr className="py-[4px] first:pb-[4px] last:pt-[4px]">
								<td className="align-baseline">
									<span className="whitespace-nowrap font-lato text-[14px] leading-[20px] tracking-[0.2px] text-[#A3ABB1]">
										Timezone:
									</span>
								</td>
								<td className="w-full pl-[20px]">
									<span className="whitespace-nowrap font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
										{appConfigurationData?.apps?.timezone}
									</span>
								</td>
							</tr>
							<tr className="py-[4px] first:pb-[4px] last:pt-[4px]">
								<td className="align-baseline">
									<span className="whitespace-nowrap font-lato text-[14px] leading-[20px] tracking-[0.2px] text-[#A3ABB1]">
										Date-Time Format:
									</span>
								</td>
								<td className="w-full pl-[20px]">
									<span className="whitespace-nowrap font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
										{appConfigurationData?.apps?.datetime_format}
										<span className="text-[#A3ABB1]">
											(August 05 2006, 3:05 PM)
										</span>
									</span>
								</td>
							</tr>
						</tbody>
					</table>
				</div>
			</div>
			<UpdateAppDetailsModal />
		</>
	);
}
