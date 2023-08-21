import FirstApp from './FirstApp';
import LaunchNewAppModal from '../Models/LaunchNewAppModal';
import Apps from './Apps';

export default function Platform() {
	return (
		<>
			{/* <FirstApp /> */}
			<Apps />
			<LaunchNewAppModal />
		</>
	);
}
