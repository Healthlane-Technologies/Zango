import { useSelector } from 'react-redux';
import { selectAppsData } from '../../../slice';
import LaunchNewAppButton from '../LaunchNewAppButton';
import EachApp from './EachApp';
import Filters from './Filters';
import LaunchingApp from './LaunchingApp';

export default function Apps() {
	const appsData = useSelector(selectAppsData);

	// Split by status so suspended apps live in their own labelled section
	// at the bottom — visually distinct without being buried out of sight.
	const active = [];
	const suspended = [];
	(appsData || []).forEach((app) => {
		if (app?.status === 'suspended') suspended.push(app);
		else active.push(app);
	});

	// `suspended` renders the same card as `deployed` — the card component
	// reads `status` and applies its own suspended styling + kebab menu.
	const renderApp = (eachApp) => {
		if (eachApp?.status === 'staged') {
			return <LaunchingApp key={eachApp?.uuid} data={eachApp} />;
		}
		if (eachApp?.status === 'deployed' || eachApp?.status === 'suspended') {
			return <EachApp key={eachApp?.uuid} data={eachApp} />;
		}
		return null;
	};

	return (
		<div className="flex h-full grow flex-col gap-[32px] px-[20px] pt-[29px] md:px-[46px]">
			<div className="flex items-center justify-between pr-[18px]">
				<span className="font-source-sans-pro text-[22px] font-semibold leading-[28px] text-[#000000]">
					Apps
				</span>
				<div>
					<LaunchNewAppButton />
				</div>
			</div>
			<div className="flex min-h-0 grow flex-col gap-[16px] overflow-y-auto pb-[29px]">
				<div className="flex items-center justify-end gap-[8px] pr-[18px]">
					<Filters />
				</div>
				<div
					data-cy="app_list"
					className="complete-hidden-scroll-style grid grid-cols-1 items-stretch justify-start gap-[26px] sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-4 2xl:grid-cols-5"
				>
					{active.map(renderApp)}
				</div>

				{suspended.length ? (
					<div className="mt-[16px] flex flex-col gap-[16px]">
						<div
							className="flex items-center gap-[10px] pr-[18px]"
							data-cy="suspended_apps_heading"
						>
							<span className="font-source-sans-pro text-[15px] font-semibold text-[#5A607A]">
								Suspended
							</span>
							<span
								className="inline-flex items-center gap-[6px] rounded-full border px-[8px] py-[2px] font-lato text-[10.5px] font-bold uppercase tracking-[0.06em]"
								style={{
									backgroundColor: '#FEF6E7',
									borderColor: 'rgba(218,144,17,0.28)',
									color: '#8A5A07',
								}}
							>
								<span
									aria-hidden
									style={{
										width: 6,
										height: 6,
										borderRadius: 999,
										backgroundColor: '#DA9011',
										boxShadow: '0 0 0 2px rgba(218,144,17,0.22)',
									}}
								/>
								{suspended.length}
							</span>
							<span className="font-lato text-[12px] text-[#8389A3]">
								blocked from serving traffic · data preserved
							</span>
						</div>
						<div
							data-cy="suspended_app_list"
							className="complete-hidden-scroll-style grid grid-cols-1 items-stretch justify-start gap-[26px] sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-4 2xl:grid-cols-5"
						>
							{suspended.map(renderApp)}
						</div>
					</div>
				) : null}
			</div>
		</div>
	);
}
