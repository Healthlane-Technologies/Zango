import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { ReactComponent as ModalBackIcon } from '../../../../../assets/images/svg/page-back-arrow-icon.svg';
import {
	closeIsConfigurePackageModalOpen,
	selectIsConfigurePackageModalOpen,
	toggleRerenderPage,
} from '../../../slice';
import ConfigurePackageForm from './ConfigurePackageForm';

export default function ConfigurePackageModal() {
	const isConfigurePackageModalOpen = useSelector(
		selectIsConfigurePackageModalOpen
	);
	const dispatch = useDispatch();

	function closeModal() {
		dispatch(closeIsConfigurePackageModalOpen());
		dispatch(toggleRerenderPage());
	}

	return (
		<Transition appear show={isConfigurePackageModalOpen} as={Fragment}>
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
							<Dialog.Panel className="relative flex h-screen max-h-screen min-h-full w-full transform flex-col gap-[32px] overflow-hidden bg-white p-[0px] text-left align-middle shadow-xl transition-all">
								<div className="flex justify-end md:absolute md:left-0 md:top-0">
									<button
										type="button"
										className="flex justify-end focus:outline-none md:absolute md:left-[16px] md:top-[16px]"
										onClick={closeModal}
									>
										<ModalBackIcon />
									</button>
								</div>
								<ConfigurePackageForm closeModal={closeModal} />
							</Dialog.Panel>
						</div>
					</div>
				</Transition.Child>
			</Dialog>
		</Transition>
	);
}
