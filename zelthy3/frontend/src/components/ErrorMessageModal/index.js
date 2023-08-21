import { Fragment, useRef } from 'react';
import { Dialog, Transition } from '@headlessui/react';

export default function ErrorMessageModal({
	isVisible,
	setVisible,
	errorMessage,
}) {
	const modalContentRef = useRef(null);

	const handleOverlayClick = (event) => {
		event.preventDefault();
	};

	return (
		<Transition.Root show={isVisible} as={Fragment}>
			<Dialog
				as="div"
				className="fixed inset-0 z-10 overflow-y-auto"
				onClose={setVisible}
				initialFocus={modalContentRef}
			>
				<div
					ref={modalContentRef}
					className="flex min-h-screen items-center justify-center px-4 pt-4 pb-20 text-center sm:block sm:p-0"
				>
					<Transition.Child
						as={Fragment}
						enter="ease-out duration-300"
						enterFrom="opacity-0"
						enterTo="opacity-100"
						leave="ease-in duration-200"
						leaveFrom="opacity-100"
						leaveTo="opacity-0"
					>
						<Dialog.Overlay
							className="fixed inset-0 backdrop-blur-sm transition-opacity"
							onClick={handleOverlayClick}
						/>
					</Transition.Child>

					<span
						className="hidden sm:inline-block sm:h-screen sm:align-middle"
						aria-hidden="true"
					>
						&#8203;
					</span>
					<Transition.Child
						as={Fragment}
						enter="ease-out duration-300"
						enterFrom="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
						enterTo="opacity-100 translate-y-0 sm:scale-100"
						leave="ease-in duration-200"
						leaveFrom="opacity-100 translate-y-0 sm:scale-100"
						leaveTo="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
					>
						<div className="inline-block transform overflow-hidden rounded-[6px] bg-white text-left align-bottom shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:align-middle md:w-96">
							<div className="flex w-full flex-col items-center rounded-[6px] bg-white">
								<Dialog.Title
									as="h3"
									className="text-xxs text-modal-title w-full px-6 pt-8 pb-[32px] font-lato font-black uppercase"
								>
									Error
								</Dialog.Title>
								<button
									type="button"
									className="absolute top-4 right-4"
									onClick={() => setVisible(false)}
								>
									{/* <IconModalClose /> */}
								</button>
								<div className="mb-[32px] w-full px-6">
									<div className="w-full text-center text-[#808187]">
										{errorMessage}
									</div>
								</div>
								<footer className="flex w-full flex-row items-center justify-end border-t border-[#3F4151] py-3 px-4">
									<button
										className="form-primary-cta"
										onClick={() => setVisible(false)}
									>
										Go Back
									</button>
								</footer>
							</div>
						</div>
					</Transition.Child>
				</div>
			</Dialog>
		</Transition.Root>
	);
}
