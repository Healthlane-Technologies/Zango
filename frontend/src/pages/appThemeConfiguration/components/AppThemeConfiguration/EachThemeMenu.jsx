import { Menu, Transition } from '@headlessui/react';
import { Fragment, useState } from 'react';
import { usePopper } from 'react-popper';
import { useDispatch } from 'react-redux';
import { useParams } from 'react-router-dom';
import { ReactComponent as TableRowKebabIcon } from '../../../../assets/images/svg/table-row-kebab-icon.svg';
import useApi from '../../../../hooks/useApi';
import { transformToFormData } from '../../../../utils/form';
import { openIsEditThemeModalOpen, toggleRerenderPage } from '../../slice';

export default function EachThemeMenu({ data }) {
	let { appId } = useParams();
	const [referenceElement, setReferenceElement] = useState(null);
	const [popperElement, setPopperElement] = useState(null);
	const { styles, attributes } = usePopper(referenceElement, popperElement, {
		placement: 'bottom-end',
		modifiers: [
			{
				name: 'offset',
				options: {
					offset: [16, 8],
				},
			},
		],
	});

	const dispatch = useDispatch();

	const handleEditTheme = () => {
		dispatch(openIsEditThemeModalOpen(data));
	};

	const triggerApi = useApi();

	const handleActiveTheme = () => {
		let tempValues = {
			is_active: !data?.is_active,
		};

		let dynamicFormData = transformToFormData(tempValues);

		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/themes/${data?.id}/`,
				type: 'PUT',
				loader: true,
				payload: dynamicFormData,
			});

			if (success && response) {
				dispatch(toggleRerenderPage());
			}
		};

		makeApiCall();
	};

	return (
		<Menu as="div" className="relative flex">
			<Menu.Button
				className="flex w-full justify-center focus:outline-none"
				ref={(ref) => setReferenceElement(ref)}
			>
				<TableRowKebabIcon className="text-[#6C747D]" />
			</Menu.Button>
			<Transition
				as={Fragment}
				// @ts-ignore
				ref={(ref) => setPopperElement(ref)}
				style={styles['popper']}
				{...attributes['popper']}
			>
				<Menu.Items className="absolute right-0 top-[30px] w-[186px] origin-top-right rounded-[4px] bg-white shadow-table-menu focus:outline-none">
					<div className="p-[4px]">
						<Menu.Item>
							{({ active }) => (
								<button
									type="button"
									className="flex w-full"
									onClick={handleEditTheme}
								>
									<div
										className={`${
											active ? 'bg-[#F0F3F4]' : ''
										} flex w-full flex-col rounded-[2px] px-[12px] py-[8px]`}
									>
										<span className="text-start font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
											Edit Theme
										</span>
										<span className="text-start font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#6C747D]">
											name, config.
										</span>
									</div>
								</button>
							)}
						</Menu.Item>
						<Menu.Item>
							{({ active }) => (
								<button
									type="button"
									onClick={handleActiveTheme}
									className="flex  w-full"
								>
									<div
										className={`${
											active ? 'bg-[#F0F3F4]' : ''
										} flex w-full flex-col rounded-[2px] px-[12px] py-[8px]`}
									>
										<span className="text-start font-lato text-[14px] font-bold leading-[20px] tracking-[0.2px] text-[#212429]">
											{data?.is_active ? 'Deactivate Theme' : 'Activate Theme'}
										</span>
										<span className="text-start font-lato text-[12px] leading-[16px] tracking-[0.2px] text-[#6C747D]">
											{data?.is_active
												? 'deactivate this theme'
												: 'activate this theme'}
										</span>
									</div>
								</button>
							)}
						</Menu.Item>
					</div>
				</Menu.Items>
			</Transition>
		</Menu>
	);
}
