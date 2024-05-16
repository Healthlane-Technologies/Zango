import { Link } from 'react-router-dom';
import { useWindowSizeHeight } from '../../../../utils/helper';
import Chatbot from './Chatbot/Index';
import ProfileMenu from './ProfileMenu';

import debounce from 'just-debounce-it';
import { useLayoutEffect, useRef } from 'react';
import { ReactComponent as ZelthyIcon } from '../../../../assets/images/svg/zelthy-icon.svg';
import NavSearchForm from './NavSearchForm';
import SideMenu from './SideMenu';
import DragablePopover from './Chatbot/DragablePopover';
import Draggable, { DraggableCore } from 'react-draggable';
import { Resizable, ResizableBox } from 'react-resizable';
import { useSelector } from 'react-redux';
import { selectAppPanelInitialData } from '../../../platform/slice';

export default function Layout({ children }) {
	useWindowSizeHeight();

	const navRef = useRef(null);
	const appPanelInitialData = useSelector(selectAppPanelInitialData);

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
				<SideMenu />
				{children}
				{/* <Draggable> */}
				{/* <ResizableBox width={200} height={200}></ResizableBox> */}
				{/* </Draggable> */}
				{appPanelInitialData?.is_codeassist_enabled ? (
					<>
						<div className="absolute bottom-[8px] left-[96px] z-[51]">
							<DragablePopover />
						</div>
						<Chatbot />
					</>
				) : null}
			</main>
		</>
	);
}
