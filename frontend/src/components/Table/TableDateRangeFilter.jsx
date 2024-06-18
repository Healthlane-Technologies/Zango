import { Menu, Transition } from '@headlessui/react';
import moment from 'moment';
import React, { Fragment, useState } from 'react';
import { DateRangePicker } from 'react-dates';
import { usePopper } from 'react-popper';
import { ReactComponent as CloseIcon } from '../../assets/images/svg/close-icon.svg';
import { ReactComponent as TableColumnFilterIcon } from '../../assets/images/svg/table-column-filter-icon.svg';

const TableDateRangeFilter = ({
	label,
	optionsData,
	optionsDataName,
	value,
	placeholder,
	onChange,
	...props
}) => {
	const [newStartDate, setNewStartDate] = useState(
		value?.start ? moment(value?.start, 'YYYY-MM-DD') : null
	);
	const [newEndDate, setNewEndDate] = useState(
		value?.end ? moment(value?.end, 'YYYY-MM-DD') : null
	);

	const [focusedInput, setFocusedInput] = useState(null);
	const [referenceElement, setReferenceElement] = useState(null);
	const [popperElement, setPopperElement] = useState(null);
	const { styles, attributes } = usePopper(referenceElement, popperElement, {
		placement: 'bottom-start',
		modifiers: [
			{
				name: 'offset',
				options: {
					offset: [16, 8],
				},
			},
		],
	});

	return (
		<div className="relativ z-10">
			<Menu as="div" className="relative flex">
				<Menu.Button
					className="flex w-full justify-center focus:outline-none"
					ref={(ref) => setReferenceElement(ref)}
				>
					<TableColumnFilterIcon
						className={`${
							value?.start && value?.end ? 'text-primary' : 'text-[#6C747D]'
						}`}
					/>
				</Menu.Button>
				<Transition
					as={Fragment}
					// @ts-ignore
					ref={(ref) => setPopperElement(ref)}
					style={styles['popper']}
					{...attributes['popper']}
				>
					<Menu.Items className="absolute right-0 top-[30px] origin-top-right rounded-[4px] bg-white shadow-table-menu focus:outline-none">
						<div className="table-date-range-filter">
							<Menu.Item className="">
								{({ active }) => (
									<>
										<DateRangePicker
											startDate={newStartDate}
											endDate={newEndDate}
											onDatesChange={({ startDate, endDate }) => {
												if (!moment(newStartDate).isSame(startDate)) {
													setNewStartDate(startDate);
													setNewEndDate(null);
												}
												if (
													startDate &&
													endDate &&
													!moment(newEndDate).isSame(endDate)
												) {
													onChange({
														start: moment(startDate).format('YYYY-MM-DD'),
														end: moment(endDate).format('YYYY-MM-DD'),
													});
												}
											}}
											focusedInput={focusedInput}
											onFocusChange={(focusedInput) =>
												setFocusedInput(focusedInput)
											}
											hideKeyboardShortcutsPanel={true}
											noBorder={true}
											isOutsideRange={() => false}
											displayFormat={'DD/MM/YYYY'}
										/>
										<button
											type="button"
											className="absolute inset-y-0 right-[16px]"
											onClick={() => {
												setNewStartDate(null);
												setNewEndDate(null);
												onChange({
													start: null,
													end: null,
												});
											}}
										>
											<CloseIcon className="h-[8px] w-[8px]" />
										</button>
									</>
								)}
							</Menu.Item>
						</div>
					</Menu.Items>
				</Transition>
			</Menu>
		</div>
	);
};

export default TableDateRangeFilter;
