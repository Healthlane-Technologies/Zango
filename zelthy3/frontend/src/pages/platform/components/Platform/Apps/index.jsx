import { useSelector, useDispatch } from 'react-redux';
import { open } from '../../../slice';

import { ReactComponent as LaunchNewAppIcon } from '../../../../../assets/images/svg/launch-new-app-icon.svg';
import EachApp from './EachApp';
import Filters from './Filters';

export default function Apps() {
	const dispatch = useDispatch();

	const handleLaunchNewApp = () => {
		dispatch(open());
	};

	const DATA = [
		{
			launched_date: '12/09/2022',
			is_recently_launched: true,
			app_id: 'zc-7651e5',
			app_name: 'App Name',
			description:
				'Description of the app will come here and this could be one or more sentences.',
			modified_date: '28/07/2023',
			app_url: 'https://psphere.app',
			app_icon_url: '',
		},
		{
			launched_date: '12/09/2022',
			is_recently_launched: false,
			app_id: 'zc-7651e52',
			app_name: 'App Name',
			description:
				'Description of the app will come here and this could be one or more sentences.',
			modified_date: '26/07/2023',
			app_url: 'https://psphere.app',
			app_icon_url: '',
		},
		{
			launched_date: '12/09/2022',
			is_recently_launched: true,
			app_id: 'zc-7651e3511',
			app_name: 'App Name',
			description:
				'Description of the app will come here and this could be one or more sentences.',
			modified_date: '26/07/2023',
			app_url: 'https://psphere.app',
			app_icon_url: '',
		},
		{
			launched_date: '12/09/2022',
			is_recently_launched: true,
			app_id: 'zc-7651e522',
			app_name: 'App Name',
			description:
				'Description of the app will come here and this could be one or more sentences.',
			modified_date: '26/07/2023',
			app_url: 'https://psphere.app',
			app_icon_url: '',
		},
		{
			launched_date: '12/09/2022',
			is_recently_launched: false,
			app_id: 'zc-7651e5323',
			app_name: 'App Name',
			description:
				'Description of the app will come here and this could be one or more sentences.',
			modified_date: '26/07/2023',
			app_url: 'https://psphere.app',
			app_icon_url: '',
		},
		{
			launched_date: '12/09/2022',
			is_recently_launched: false,
			app_id: 'zc-7651e5121',
			app_name: 'App Name',
			description:
				'Description of the app will come here and this could be one or more sentences.',
			modified_date: '26/07/2023',
			app_url: 'https://psphere.app',
			app_icon_url: '',
		},
		{
			launched_date: '12/09/2022',
			is_recently_launched: true,
			app_id: 'zc-7651e52123',
			app_name: 'App Name',
			description:
				'Description of the app will come here and this could be one or more sentences.',
			modified_date: '26/07/2023',
			app_url: 'https://psphere.app',
			app_icon_url: '',
		},
		{
			launched_date: '12/09/2022',
			is_recently_launched: false,
			app_id: 'zc-7651e5432',
			app_name: 'App Name',
			description:
				'Description of the app will come here and this could be one or more sentences.',
			modified_date: '26/07/2023',
			app_url: 'https://psphere.app',
			app_icon_url: '',
		},
		{
			launched_date: '12/09/2022',
			is_recently_launched: false,
			app_id: 'zc-7651e556',
			app_name: 'App Name',
			description:
				'Description of the app will come here and this could be one or more sentences.',
			modified_date: '26/07/2023',
			app_url: 'https://psphere.app',
			app_icon_url: '',
		},
	];

	return (
		<div className="flex grow flex-col gap-[32px] px-[46px] pt-[29px]">
			<div className="flex items-center justify-between pr-[18px]">
				<span className="font-source-sans-pro text-[22px] font-semibold leading-[28px] text-[#000000]">
					Apps
				</span>

				<div>
					<button
						onClick={handleLaunchNewApp}
						className="flex grow gap-[8px] rounded-[4px] bg-[#5048ED] px-[16px] py-[7px]"
					>
						<span className="font-lato text-[14px] font-bold leading-[20px] text-[#FFFFFF]">
							Launch New App
						</span>
						<LaunchNewAppIcon />
					</button>
				</div>
			</div>
			<div className="flex grow flex-col gap-[16px] overflow-y-auto">
				<div className="flex items-center justify-end gap-[8px] pr-[18px]">
					<Filters />
				</div>
				<div className="complete-hidden-scroll-style grid grid-cols-1 items-start justify-start gap-[26px] overflow-y-auto pb-[29px] sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-4 2xl:grid-cols-5">
					{DATA?.map((eachApp) => (
						<EachApp key={eachApp?.app_id} data={eachApp} />
					))}
				</div>
			</div>
		</div>
	);
}
