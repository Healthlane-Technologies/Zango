import BreadCrumbs from '../BreadCrumbs';
import { useSelector, useDispatch } from 'react-redux';
import { openIsAddThemeModalOpen } from '../../slice';

import { ReactComponent as AddThemeIcon } from '../../../../assets/images/svg/add-theme-icon.svg';
import AddThemeModal from '../Models/AddThemeModal';
import EachTheme from './EachTheme';

export default function AppThemeConfiguration() {
	const dispatch = useDispatch();

	const handleAddTheme = () => {
		dispatch(openIsAddThemeModalOpen());
	};

	let eachData = {
		theme_name: 'Default Theme',
		status: 'active',
		font_family: 'Open Sans',
		colors: {
			primary: '#5048ED',
			secondary: '#FFFFFF',
		},
	};

	let eachData2 = {
		theme_name: 'Theme 2',
		status: 'InActive',
		font_family: 'Open Sans',
		colors: {
			primary: '#EC6356',
			secondary: '#FFFFFF',
		},
	};
	return (
		<>
			<div className="flex grow flex-col gap-[40px]">
				<div className="flex items-center justify-between py-[12px] pl-[40px] pr-[48px]">
					<BreadCrumbs />{' '}
					<button
						type="button"
						onClick={handleAddTheme}
						className="flex gap-[8px] rounded-[4px] bg-primary px-[16px] py-[7px]"
					>
						<span className="font-lato text-[14px] font-bold leading-[20px] text-[#FFFFFF]">
							Add Theme
						</span>
						<AddThemeIcon />
					</button>
				</div>
				<div className="flex grow flex-col gap-[20px] pl-[40px] pr-[48px]">
					<div className="flex items-end gap-[24px]">
						<h3 className="font-source-sans-pro text-[22px] font-semibold leading-[28px] text-[#000000]">
							App Name
						</h3>
					</div>
					<div className="complete-hidden-scroll-style grid grid-cols-1 items-stretch justify-start gap-[26px] overflow-y-auto pb-[29px] sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-4 2xl:grid-cols-5">
						<EachTheme data={eachData} />
						<EachTheme data={eachData2} />
					</div>
				</div>
			</div>
			<AddThemeModal />
		</>
	);
}
