import { useSelector } from 'react-redux';
import { ReactComponent as EachAppIcon } from '../../../../../assets/images/svg/each-app-icon.svg';
import { selectAppConfigurationData } from '../../../slice';
import EachDescriptionRow from './EachDescriptionRow';

function DetailsTable() {
	const appConfigurationData = useSelector(selectAppConfigurationData);

	return (
		<table data-cy="appDetails" className="w-100 border-spacing-x-4">
			<tbody>
				<EachDescriptionRow
					label="App Description:"
					content={
						<pre className="w-100 font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
							{appConfigurationData?.app?.description
								.split('\n')
								.map((str, key) => (
									<p key={key} className="whitespace-normal">
										{str}
									</p>
								))}
						</pre>
					}
				/>
				<EachDescriptionRow
					label="Logo:"
					content={
						appConfigurationData?.app?.logo ? (
							<img
								src={appConfigurationData?.app?.logo}
								className="h-[56px] w-[56px]  object-contain"
								alt="#"
							/>
						) : (
							<EachAppIcon className="h-[56px] w-[56px]" />
						)
					}
				/>
				<EachDescriptionRow
					label="Fav Icon:"
					content={
						appConfigurationData?.app?.fav_icon ? (
							<img
								src={appConfigurationData?.app?.fav_icon}
								className="h-[56px] w-[56px] object-contain"
								alt="#"
							/>
						) : (
							<EachAppIcon className="h-[56px] w-[56px]" />
						)
					}
				/>
				<EachDescriptionRow
					label="Domain:"
					content={
						<div className="flex flex-col gap-[8px]">
							{appConfigurationData?.app?.domains?.map((eachDomain, key) => {
								return (
									<a
										href={`http://${eachDomain?.domain}`}
										alt="#"
										target={'_blank'}
										key={key}
										className="w-fit"
									>
										<span
											key={eachDomain.domain}
											className="whitespace-nowrap font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429] hover:text-[#5048ED]"
										>
											{eachDomain.domain}
										</span>
									</a>
								);
							})}
						</div>
					}
				/>
				<EachDescriptionRow
					label="Timezone:"
					content={
						<span className="whitespace-nowrap font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
							{appConfigurationData?.app?.timezone}
						</span>
					}
				/>
				<EachDescriptionRow
					label="Date-Time Format:"
					content={
						<span className="whitespace-nowrap font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
							{appConfigurationData?.app?.datetime_format_display}
						</span>
					}
				/>
				<EachDescriptionRow
					label="Date Format:"
					content={
						<span className="whitespace-nowrap font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
							{appConfigurationData?.app?.date_format_display}
						</span>
					}
				/>
			</tbody>
		</table>
	);
}

export default DetailsTable;
