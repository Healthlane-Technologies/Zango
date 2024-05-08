import debounce from 'just-debounce-it';
import { useLayoutEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { ReactComponent as ZelthyIcon } from '../../assets/images/svg/zelthy-icon.svg';
import { useWindowSizeHeight } from '../../utils/helper';
import NavSearchForm from './NavSearchForm';
import ProfileMenu from './ProfileMenu';

export default function Layout({
	showFooter = false,
	children,
	SideMenu = null,
	CodeAssist = null,
}) {
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
						<ZelthyIcon />
					</Link>
					<NavSearchForm />
				</div>
				<div className="flex items-center gap-[40px]">
					<ProfileMenu />
				</div>
			</nav>
			<main
				className={`${
					showFooter ? 'small-device-height-fix' : 'small-device-height-fix2'
				}  flex grow overflow-y-auto`}
			>
				{SideMenu}
				{children}
				{CodeAssist}
			</main>
			{showFooter ? (
				<footer
					ref={footerRef}
					className="flex items-center justify-center gap-[8px] border-t-[1px] border-[#DDE2E5] p-[8px]"
				>
					<span className="font-lato text-[11px] leading-[16px] text-[#495057]">
						V 3.0
					</span>
					<span className="font-lato text-[12px] font-bold leading-[16px] text-[#C7CED3]">
						•
					</span>
					<span className="font-lato text-[11px] leading-[16px] text-[#495057]">
						© {new Date().getFullYear()} zelthy
					</span>
					<span className="font-lato text-[12px] font-bold leading-[16px] text-[#C7CED3]">
						•
					</span>
					<a
						href="https://docs.zelthy.com/"
						alt="#"
						target={'_blank'}
						className="m-0 inline-flex p-0"
					>
						<span className="font-lato text-[11px] leading-[16px] text-[#495057]">
							Documents
						</span>
					</a>
				</footer>
			) : null}
		</>
	);
}
