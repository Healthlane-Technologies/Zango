import { useDispatch } from 'react-redux';
import { openIsUpdateAppDetailsModalOpen } from '../../slice';

function UpdateAppDetailsButton() {
	const dispatch = useDispatch();
	const handleUpdateAppDetails = () => {
		dispatch(openIsUpdateAppDetailsModalOpen());
	};

	return (
<<<<<<< HEAD
<<<<<<< HEAD
		<button data-cy="update_details_button" type="button" onClick={handleUpdateAppDetails} className="flex">
=======
		<button data-cy="updateAppDetails" type="button" onClick={handleUpdateAppDetails} className="flex">
>>>>>>> f9ef4ffb (cypress locator addition)
=======
		<button data-cy="update_details_button" type="button" onClick={handleUpdateAppDetails} className="flex">
>>>>>>> c893349c (locators)
			<span className="font-lato text-[14px] font-bold leading-[20px] text-primary">
				update details
			</span>
		</button>
	);
}

export default UpdateAppDetailsButton;
