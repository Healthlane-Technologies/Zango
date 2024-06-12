import { useDispatch } from 'react-redux';
import { openIsUpdateAppDetailsModalOpen } from '../../slice';

function UpdateAppDetailsButton() {
	const dispatch = useDispatch();
	const handleUpdateAppDetails = () => {
		dispatch(openIsUpdateAppDetailsModalOpen());
	};

	return (
		<button data-cy="update_details_button" type="button" onClick={handleUpdateAppDetails} className="flex">
			<span className="font-lato text-[14px] font-bold leading-[20px] text-primary">
				update details
			</span>
		</button>
	);
}

export default UpdateAppDetailsButton;
