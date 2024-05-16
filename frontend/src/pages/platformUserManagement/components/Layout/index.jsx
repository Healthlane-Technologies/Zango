import { Link } from 'react-router-dom';
import { useWindowSizeHeight } from '../../../../utils/helper';
import ProfileMenu from './ProfileMenu';

import { ReactComponent as ZelthyIcon } from '../../../../assets/images/svg/zelthy-icon.svg';
import NavSearchForm from './NavSearchForm';
import debounce from 'just-debounce-it';
import { useRef } from 'react';
import { useLayoutEffect } from 'react';

export default function Layout({ children }) {
	const navRef = useRef(null);

	useLayoutEffect(() => {
		function setElementOffsetHeight() {
			document.documentElement.style.setProperty(
				'--navHeight',
				`${navRef?.current?.offsetHeight}px`
			);
		}

		const heightChange = debounce(() => setElementOffsetHeight());

		window.addEventListener('resize', heightChange);
		heightChange();
		return () => window.removeEventListener('resize', heightChange);
	}, []);

	useWindowSizeHeight();

	return (
		<>
			<nav
				ref={navRef}
				className="flex items-center justify-between border-b-[1px] border-[#DDE2E5] py-[8px] pl-[24px] pr-[40px]"
			>
				<div className="flex items-center justify-between gap-[48px]">
					<Link to="/platform">
						<ZelthyIcon className="max-h-[20px] w-fit" />
					</Link>
					<NavSearchForm />
				</div>
				<div className="flex items-center gap-[40px]">
					<ProfileMenu />
				</div>
			</nav>
			<main className="small-device-height-fix2 flex grow overflow-y-auto">
				{children}
			</main>
		</>
	);
}
