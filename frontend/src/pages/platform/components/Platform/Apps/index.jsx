import { useSelector } from 'react-redux';
import { selectAppsData } from '../../../slice';
import LaunchNewAppButton from '../LaunchNewAppButton';
import EachApp from './EachApp';
import Filters from './Filters';
import LaunchingApp from './LaunchingApp';

export default function Apps() {
	const appsData = useSelector(selectAppsData);

	return (
		<div className="flex grow flex-col gap-[32px] px-[20px] pt-[29px] md:px-[46px]">
			<div className="flex items-center justify-between pr-[18px]">
				<span className="font-source-sans-pro text-[22px] font-semibold leading-[28px] text-[#000000]">
					Apps
				</span>
				<div>
					<LaunchNewAppButton />
				</div>
			</div>
			<div className="flex grow flex-col gap-[16px] overflow-y-auto">
				<div className="flex items-center justify-end gap-[8px] pr-[18px]">
					<Filters />
				</div>
				<div data-cy= "app_list" className="complete-hidden-scroll-style grid grid-cols-1 items-stretch justify-start gap-[26px] overflow-y-auto pb-[29px] sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-4 2xl:grid-cols-5">
					{appsData?.map(
						(eachApp) =>
							({
								staged: <LaunchingApp key={eachApp?.uuid} data={eachApp} />,
								deployed: <EachApp key={eachApp?.uuid} data={eachApp} />,
							}[eachApp?.status])
					)}
				</div>
			</div>
		</div>
	);
}
