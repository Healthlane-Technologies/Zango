import ErrorToast from './ErrorToast';
import SuccessToast from './SuccessToast';
import WarningToast from './WarningToast';

export default function Notifications({ type, toastRef, title, description }) {
	switch (type) {
		case 'success':
			return (
				<SuccessToast
					toastRef={toastRef}
					title={title}
					description={description}
				/>
			);
		case 'warning':
			return (
				<WarningToast
					toastRef={toastRef}
					title={title}
					description={description}
				/>
			);
		case 'error':
			return (
				<ErrorToast
					toastRef={toastRef}
					title={title}
					description={description}
				/>
			);
		default:
			return (
				<SuccessToast
					toastRef={toastRef}
					title={title}
					description={description}
				/>
			);
	}
}
