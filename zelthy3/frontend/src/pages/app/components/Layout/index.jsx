import { Link } from 'react-router-dom';
import { useWindowSizeHeight } from '../../../../utils/helper';
import ProfileMenu from './ProfileMenu';

import { ReactComponent as ZelthyIcon } from '../../../../assets/images/svg/zelthy-icon.svg';
import NavSearchForm from './NavSearchForm';
import SideMenu from './SideMenu';

export default function Layout({ children }) {
	useWindowSizeHeight();

	return (
		<>
			<nav className="flex items-center justify-between border-b-[1px] border-[#DDE2E5] py-[8px] pl-[24px] pr-[40px]">
				<div className="flex items-center justify-between gap-[48px]">
					<Link to="/platform">
						<ZelthyIcon />
					</Link>
					<NavSearchForm />
				</div>
				<div className="flex items-center gap-[40px]">
					<ProfileMenu />
				</div>
			</nav>
			<main className="small-device-height-fix2 flex grow overflow-y-auto">
				<SideMenu />
				{children}
			</main>
		</>
	);
}
