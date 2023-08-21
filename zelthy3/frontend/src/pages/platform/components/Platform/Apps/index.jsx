import { useSelector, useDispatch } from 'react-redux';
import { open } from '../../../slice';

import { ReactComponent as LaunchNewAppIcon } from '../../../../../assets/images/svg/launch-new-app-icon.svg';
import EachApp from './EachApp';
import Filters from './Filters';
import LaunchingApp from './LaunchingApp';

export default function Apps() {
	const dispatch = useDispatch();

	const handleLaunchNewApp = () => {
		dispatch(open());
	};

	const DATA = [
		{
			app_id: '42cc3113-7faa-4e00-89ab-423489fd30d1',
			name: 'App Name',
			status: 'deployed',
			domain_url: 'https://test.zelthy.com',
			description:
				'Description of the app will come here and this could be one or more sentences.',
			logo: null,
			launched_at: '2012-01-26T13:51:50.417-07:00',
			updated_at: '2012-01-26T13:51:50.417-07:00',
		},
		{
			app_id: '42cc3113-7faa-4e00-89ab-423489fd3021',
			name: 'App Name',
			status: 'deployed',
			domain_url: 'https://test.zelthy.com',
			description:
				'Description of the app will come here and this could be one or more sentences.',
			logo: null,
			launched_at: '2023-08-05T13:51:50.417-07:00',
			updated_at: '2023-08-08T13:51:50.417-07:00',
		},
	];

	return (
		<div className="flex grow flex-col gap-[32px] px-[20px] pt-[29px] md:px-[46px]">
			<div className="flex items-center justify-between pr-[18px]">
				<span className="font-source-sans-pro text-[22px] font-semibold leading-[28px] text-[#000000]">
					Apps
				</span>

				<div>
					<button
						onClick={handleLaunchNewApp}
						className="flex grow gap-[8px] rounded-[4px] bg-primary px-[16px] py-[7px]"
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
				<div className="complete-hidden-scroll-style grid grid-cols-1 items-stretch justify-start gap-[26px] overflow-y-auto pb-[29px] sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-4 2xl:grid-cols-5">
					<LaunchingApp
						key={121}
						data={{
							app_id: '42cc3113-7faa-4e00-89ab-423489fd3021',
							name: 'App Name',
							status: 'deployed',
							domain_url: 'https://test.zelthy.com',
							description:
								'Description of the app will come here and this could be one or more sentences.',
							logo: null,
							launched_at: '2023-08-05T13:51:50.417-07:00',
							updated_at: '2023-08-08T13:51:50.417-07:00',
						}}
					/>
					{DATA?.map((eachApp) => (
						<EachApp key={eachApp?.app_id} data={eachApp} />
					))}
				</div>
			</div>
		</div>
	);
}
