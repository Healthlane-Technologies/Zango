import { useSelector } from 'react-redux';
import { ReactComponent as EachAppIcon } from '../../../../../assets/images/svg/each-app-icon.svg';
import { selectAppConfigurationData } from '../../../slice';
import EachDescriptionRow from './EachDescriptionRow';
import { ReactComponent as SingleFileIcon } from '../../../../../assets/images/svg/single-file.svg';
import { getRepoName } from '../../../../../utils/helper';

function DetailsTable() {
	const appConfigurationData = useSelector(selectAppConfigurationData);

	return (
		<table data-cy="app_details" className="w-fit border-spacing-x-4">
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
				<EachDescriptionRow
					label="Template:"
					content={
						appConfigurationData?.app?.app_template?(
							<a target='__blank'
							 href={appConfigurationData?.app?.app_template} 
							 className='whitespace-nowrap cursor-pointer font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#5048ED]'>
								<SingleFileIcon />
							</a>
						):(
						<span className="whitespace-nowrap font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
							No Template found
						</span>
						)
					}
				/>
				<EachDescriptionRow
					label="Github Repository:"
					content={
						appConfigurationData?.app?.extra_config?.git_config?.repo_url ? (
							<a
								href={appConfigurationData?.app?.extra_config?.git_config?.repo_url}
								alt="#"
								target={'_blank'}
								className="w-fit"
							>
								<span className="whitespace-nowrap font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#5047ED]">
									{appConfigurationData?.app?.extra_config?.git_config?.repo_url ? getRepoName(appConfigurationData?.app?.extra_config?.git_config?.repo_url) : null}
								</span>
							</a>
						) : (
							<span className="whitespace-nowrap font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
								Not configured
							</span>
						)
					}
				/>
				{
					appConfigurationData?.app?.extra_config?.git_config?.repo_url ? (<>
						<EachDescriptionRow
							label="Development:"
							content={
								<span className="whitespace-nowrap font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
									{appConfigurationData?.app?.extra_config?.git_config?.branch?.dev}
								</span>
							}
						/>
						<EachDescriptionRow
							label="Staging:"
							content={
								<span className="whitespace-nowrap font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
									{appConfigurationData?.app?.extra_config?.git_config?.branch?.staging}
								</span>
							}
						/>
						<EachDescriptionRow
							label="Production:"
							content={
								<span className="whitespace-nowrap font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
									{appConfigurationData?.app?.extra_config?.git_config?.branch?.prod}
								</span>
							}
						/>
					</>) : null
				}

			</tbody>
		</table>
	);
}

export default DetailsTable;
