import { Link } from 'react-router-dom';
import { useWindowSizeHeight } from '../../../../utils/helper';
import ProfileMenu from './ProfileMenu';

import { ReactComponent as ZelthyIcon } from '../../../../assets/images/svg/zelthy-icon.svg';
import NavSearchForm from './NavSearchForm';

export default function Layout({ children }) {
	useWindowSizeHeight();

	return (
		<>
			<nav className="flex items-center justify-between border-b-[1px] border-[#DDE2E5] py-[8px] pl-[24px] pr-[40px]">
				<div className="flex items-center justify-between gap-[48px]">
					<Link to="/msdodtrack038/orders">
						<ZelthyIcon />
					</Link>
					<NavSearchForm />
				</div>
				<div className="flex items-center gap-[40px]">
					<ProfileMenu />
				</div>
			</nav>
			<main className="small-device-height-fix flex grow">{children}</main>
			<footer className="flex items-center justify-center gap-[8px] border-t-[1px] border-[#DDE2E5] p-[8px]">
				<span className="font-lato text-[11px] leading-[16px] text-[#495057]">
					V 2.0
				</span>
				<span className="font-lato text-[12px] font-bold leading-[16px] text-[#C7CED3]">
					•
				</span>
				<span className="font-lato text-[11px] leading-[16px] text-[#495057]">
					© zelthy
				</span>
				<span className="font-lato text-[12px] font-bold leading-[16px] text-[#C7CED3]">
					•
				</span>
				<span className="font-lato text-[11px] leading-[16px] text-[#495057]">
					Documents
				</span>
				<span className="font-lato text-[12px] font-bold leading-[16px] text-[#C7CED3]">
					•
				</span>
				<span className="font-lato text-[11px] leading-[16px] text-[#495057]">
					License 273781
				</span>
			</footer>
		</>
	);
}
