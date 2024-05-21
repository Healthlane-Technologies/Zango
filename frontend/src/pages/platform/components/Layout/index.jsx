import debounce from 'just-debounce-it';
import { useLayoutEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { ReactComponent as ZelthyIcon } from '../../../../assets/images/svg/zelthy-icon.svg';
import {
	getPlatformVersion,
	useWindowSizeHeight,
} from '../../../../utils/helper';
import NavSearchForm from './NavSearchForm';
import ProfileMenu from './ProfileMenu';

export default function Layout({ children }) {
	const navRef = useRef(null);
	const footerRef = useRef(null);

	useWindowSizeHeight();

	useLayoutEffect(() => {
		function setElementOffsetHeight() {
			document.documentElement.style.setProperty(
				'--navHeight',
				`${navRef?.current?.offsetHeight}px`
			);
			document.documentElement.style.setProperty(
				'--footerHeight',
				`${footerRef?.current?.offsetHeight}px`
			);
		}

		const heightChange = debounce(() => setElementOffsetHeight());

		window.addEventListener('resize', heightChange);
		heightChange();
		return () => window.removeEventListener('resize', heightChange);
	}, []);

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
			<main className="small-device-height-fix flex grow overflow-y-auto">
				{children}
			</main>
			<footer
				ref={footerRef}
				className="flex items-center justify-center gap-[8px] border-t-[1px] border-[#DDE2E5] p-[8px]"
			>
				<span className="font-lato text-[11px] leading-[16px] text-[#495057]">
					V {getPlatformVersion()}
				</span>
				<span className="font-lato text-[12px] font-bold leading-[16px] text-[#C7CED3]">
					•
				</span>
				<span className="font-lato text-[11px] leading-[16px] text-[#495057]">
					© {new Date().getFullYear()} HEALTHLANE TECHNOLOGIES PVT. LTD
				</span>
				<span className="font-lato text-[12px] font-bold leading-[16px] text-[#C7CED3]">
					•
				</span>
				<a
					href="https://www.zango.dev/docs/"
					alt="#"
					target={'_blank'}
					className="m-0 inline-flex p-0"
				>
					<span className="font-lato text-[11px] leading-[16px] text-[#495057]">
						Docs
					</span>
				</a>

				{/* <span className="font-lato text-[12px] font-bold leading-[16px] text-[#C7CED3]">
					•
				</span>
				<span className="font-lato text-[11px] leading-[16px] text-[#495057]">
					License 273781
				</span> */}
			</footer>
		</>
	);
}
