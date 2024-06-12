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
			data-cy="launch_app_button"
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
