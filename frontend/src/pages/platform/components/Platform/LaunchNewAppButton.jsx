import { useDispatch } from 'react-redux';
import { ReactComponent as LaunchNewAppIcon } from '../../../../assets/images/svg/launch-new-app-icon.svg';
import { open } from '../../slice';

function LaunchNewAppButton() {
	const dispatch = useDispatch();

	const handleLaunchNewApp = () => {
		dispatch(open());
	};
	return (
		<button
<<<<<<< HEAD
<<<<<<< HEAD
			data-cy="launch_app_button"
=======
			data-cy="launchAppButton"
>>>>>>> f9ef4ffb (cypress locator addition)
=======
			data-cy="launch_app_button"
>>>>>>> c893349c (locators)
			type="button"
			onClick={handleLaunchNewApp}
			className="gap-[8px] rounded-[4px] px-[16px] py-[7px] flex grow bg-primary"
		>
			<span className="text-[14px] leading-[20px] text-[#FFFFFF] font-lato font-bold">
				Launch New App
			</span>
			<LaunchNewAppIcon />
		</button>
	);
}

export default LaunchNewAppButton;
