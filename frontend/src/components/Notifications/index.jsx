import Toast from './Toast';

export default function Notifications({ type, toastRef, title, description }) {
	return (
		<Toast
			toastRef={toastRef}
			title={title}
			description={description}
			type={type}
		/>
	);
}
