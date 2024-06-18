import { useSelector } from 'react-redux';
import { Link, useLocation } from 'react-router-dom';
import { selectAppConfigurationData } from '../../appConfiguration/slice';

export default function BreadCrumbs() {
	let location = useLocation();
	let uuid = location.pathname.split('/')[3];
	const appConfigurationData = useSelector(selectAppConfigurationData);

	return (
		<div className="flex flex-wrap gap-[5px]">
			{location.pathname
				.split('/')
				.filter((each, index) => each && index !== 1)
				.map((each, index, filterBreadCrumb) => {
					let url = filterBreadCrumb.slice(0, index + 1).join('/');
					let suffixSlash = index === filterBreadCrumb.length - 1 ? ' / ' : '';
					let prefixSlash = index < filterBreadCrumb.length - 2 ? ' / ' : '';
					return (
						<Link
							key={
								{
									0: 'platform/apps/',
									1: `/platform/apps/${uuid}/app-settings/app-configuration/`,
									2: url,
									3: url,
								}[index]
							}
							to={
								{
									0: '/platform/apps/',
									1: `/platform/apps/${uuid}/app-settings/app-configuration/`,
									2: url,
									3: url,
								}[index]
							}
							className={`font-lato text-[10px] font-black uppercase tracking-[2px] ${
								suffixSlash ? 'text-[#212429]' : 'text-[#ababae]'
							}`}
						>
							{suffixSlash}{' '}
							{index !== 1
								? each.replaceAll('-', ' ')
								: appConfigurationData?.app?.name}{' '}
							{prefixSlash}
						</Link>
					);
				})}
		</div>
	);
}
