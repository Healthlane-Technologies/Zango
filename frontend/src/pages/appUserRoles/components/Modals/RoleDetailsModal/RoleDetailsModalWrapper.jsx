import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { ReactComponent as ModalCloseIcon } from '../../../../../assets/images/svg/modal-close-icon.svg';

function RoleDetailsModalWrapper({ label = '', show = false, closeModal, children, headerAction }) {
	return (
		<Transition appear show={show} as={Fragment}>
			<Dialog as="div" className="relative z-50" onClose={closeModal}>
				<Transition.Child
					as={Fragment}
					enter="ease-out duration-300"
					enterFrom="opacity-0"
					enterTo="opacity-100"
					leave="ease-in duration-200"
					leaveFrom="opacity-100"
					leaveTo="opacity-0"
				>
					<div className="fixed inset-0 bg-black bg-opacity-25" />
				</Transition.Child>

				<div className="fixed inset-0 overflow-y-auto">
					<div className="flex min-h-full items-center justify-center p-4 text-center">
						<Transition.Child
							as={Fragment}
							enter="ease-out duration-300"
							enterFrom="opacity-0 scale-95"
							enterTo="opacity-100 scale-100"
							leave="ease-in duration-200"
							leaveFrom="opacity-100 scale-100"
							leaveTo="opacity-0 scale-95"
						>
							<Dialog.Panel className="w-full max-w-[1000px] transform overflow-hidden rounded-[12px] bg-white text-left align-middle shadow-xl transition-all">
								<div className="flex items-center justify-between px-[24px] py-[16px] border-b border-[#E5E7EB]">
									<Dialog.Title className="text-[18px] font-semibold text-[#111827]">
										{label}
									</Dialog.Title>
									<div className="flex items-center gap-[12px]">
										{headerAction}
										<button
											type="button"
											className="flex items-center justify-center rounded-[6px] p-[4px] hover:bg-[#F3F4F6] transition-colors"
											onClick={closeModal}
										>
											<ModalCloseIcon />
										</button>
									</div>
								</div>
								<div className="relative">
									{children}
								</div>
							</Dialog.Panel>
						</Transition.Child>
					</div>
				</div>
			</Dialog>
		</Transition>
	);
}

export default RoleDetailsModalWrapper;