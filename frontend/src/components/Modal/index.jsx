import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { ReactComponent as ModalCloseIcon } from '../../assets/images/svg/modal-close-icon.svg';

function Modal({ label = '', show = false, closeModal, ModalBody }) {
	return (
		<Transition appear show={show} as={Fragment}>
			<Dialog as="div" className="relative z-10" onClose={() => {}}>
				<Transition.Child
					as={Fragment}
					enter="ease-in-out duration-700"
					enterFrom="opacity-0"
					enterTo="opacity-100"
					leave="ease-in-out duration-700"
					leaveFrom="opacity-100"
					leaveTo="opacity-0"
				>
					<div className="fixed inset-0 bg-black bg-opacity-[.67]" />
				</Transition.Child>

				<Transition.Child
					as={Fragment}
					enter="transform transition ease-in-out duration-500"
					enterFrom="translate-x-full"
					enterTo="translate-x-0"
					leave="transform transition ease-in-out duration-500"
					leaveFrom="translate-x-0"
					leaveTo="translate-x-full"
				>
					<div className="fixed inset-0 overflow-y-auto">
						<div className="flex h-screen max-h-screen min-h-full grow items-center justify-center text-center md:justify-end">
							<Dialog.Panel className="relative flex h-screen max-h-screen min-h-full w-full max-w-[498px] transform flex-col gap-[32px] overflow-hidden bg-white px-[24px] pb-[40px] pt-[52px] text-left align-middle shadow-xl transition-all md:pl-[32px] md:pr-[72px] md:pt-[32px]">
								<div className="flex justify-end md:absolute md:right-0 md:top-0">
									<button
										type="button"
										className="flex justify-end focus:outline-none md:absolute md:right-[16px] md:top-[16px]"
										onClick={closeModal}
									>
										<ModalCloseIcon />
									</button>
								</div>
								<Dialog.Title as="div" className="flex flex-col gap-2">
									<div className="flex flex-col gap-[2px]">
										<h4 className="font-source-sans-pro text-[22px] font-semibold leading-[28px]">
											{label}
										</h4>
									</div>
								</Dialog.Title>
								{ModalBody}
							</Dialog.Panel>
						</div>
					</div>
				</Transition.Child>
			</Dialog>
		</Transition>
	);
}

export default Modal;
