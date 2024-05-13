import toast from 'react-hot-toast';
import { ReactComponent as NotificationCloseIcon } from '../../assets/images/svg/notification-close-icon.svg';

export default function Toast({
	toastRef,
	title,
	description,
	type = 'success',
}) {
	return (
		<div
			className={`relative flex min-w-[200px] max-w-[247px] flex-col items-start gap-[12px] rounded-[4px] border ${
				{
					success: 'border-[#8485F6] bg-[#EBEAFE]',
					warning: 'border-[#FECF7F] bg-[#fef7ef]',
					error: 'border-[#AB1032] bg-[#ffefef]',
				}[type]
			} p-[16px] shadow-notification ${
				toastRef.visible ? 'animate-enter' : 'animate-leave'
			}`}
		>
			<h5 className="text-start font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
				{title}
			</h5>
			<p className="text-start font-lato text-[12px] font-medium leading-[20px] tracking-[0.2px] text-[#000]">
				{description}
			</p>
			<button
				onClick={() => toast.dismiss(toastRef.id)}
				className="absolute right-[16px] top-[12px]"
			>
				<NotificationCloseIcon />
			</button>
		</div>
	);
}
