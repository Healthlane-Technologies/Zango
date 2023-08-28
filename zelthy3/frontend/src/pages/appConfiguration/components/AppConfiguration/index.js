import BreadCrumbs from '../BreadCrumbs';
import { useSelector, useDispatch } from 'react-redux';
import { openIsUpdateAppDetailsModalOpen } from '../../slice';

import { ReactComponent as EachAppIcon } from '../../../../assets/images/svg/each-app-icon.svg';
import UpdateAppDetailsModal from '../Models/UpdateAppDetailsModal';

export default function AppConfiguration() {
	const dispatch = useDispatch();

	const handleUpdateAppDetails = () => {
		dispatch(openIsUpdateAppDetailsModalOpen());
	};
	return (
		<>
			<div className="flex grow flex-col gap-[40px]">
				<div className="flex items-center justify-between pt-[22px] pb-[24px] pl-[40px] pr-[48px]">
					<BreadCrumbs />
				</div>
				<div className="flex grow flex-col gap-[20px] pl-[40px] pr-[48px]">
					<div className="flex items-end gap-[24px]">
						<h3 className="font-source-sans-pro text-[22px] font-semibold leading-[28px] text-[#000000]">
							App Name
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
										Description of the app will come here
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
									<EachAppIcon className="h-[56px] w-[56px]" />
									{/* <span className="whitespace-nowrap font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]"></span> */}
								</td>
							</tr>
							<tr className="py-[4px] first:pb-[4px] last:pt-[4px]">
								<td className="align-baseline">
									<span className="whitespace-nowrap font-lato text-[14px] leading-[20px] tracking-[0.2px] text-[#A3ABB1]">
										Fav Icon:
									</span>
								</td>
								<td className="w-full pl-[20px]">
									<span className="whitespace-nowrap font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
										-
									</span>
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
										<span className="whitespace-nowrap font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
											domainame1.com
										</span>
										<span className="whitespace-nowrap font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
											domainame1.com
										</span>
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
										GMT+5:30
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
										MMMM dd yyyy, h:m tt{' '}
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
