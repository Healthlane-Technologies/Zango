import { useLocation } from 'react-router-dom';

export default function BreadCrumbs() {
	let location = useLocation();
	return (
		<div className="flex flex-wrap gap-[5px]">
			{location.pathname
				.split('/')
				.filter((each, index) => each && index !== 1 && index !== 3)
				.map((each, index, filterBreadCrumb) => {
					console.log(each, index);
					let suffixSlash = index === filterBreadCrumb.length - 1 ? ' / ' : '';
					let prefixSlash = index < filterBreadCrumb.length - 2 ? ' / ' : '';
					return (
						<span
							className={`font-lato text-[10px] font-black uppercase tracking-[2px] ${
								suffixSlash ? 'text-[#212429]' : 'text-[#ababae]'
							}`}
						>
							{suffixSlash} {each.replaceAll('-', ' ')} {prefixSlash}
						</span>
					);
				})}
		</div>
	);
}
