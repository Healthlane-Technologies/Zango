import { Link, useLocation } from 'react-router-dom';

export default function BreadCrumbs() {
	let location = useLocation();
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
							key={url}
							to={url}
							className={`font-lato text-[10px] font-black uppercase tracking-[2px] ${
								suffixSlash ? 'text-[#212429]' : 'text-[#ababae]'
							}`}
						>
							{suffixSlash} {each.replaceAll('-', ' ')} {prefixSlash}
						</Link>
					);
				})}
		</div>
	);
}
