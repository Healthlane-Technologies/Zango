import { Fragment, useEffect, useRef, useState } from 'react';
import { Listbox, Transition } from '@headlessui/react';
import { TTL_UNITS, ttlToSeconds, splitTtlSeconds, ttlMode, humanizeTokenTtl } from '../../../../../utils/tokenTtl';

const ChevronIcon = () => (
	<svg width="16" height="16" viewBox="0 0 20 20" fill="none" className="text-[#6B7280] pointer-events-none">
		<path d="M6 8L10 12L14 8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
	</svg>
);

const CheckIcon = () => (
	<svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[#5048ED]">
		<path d="M13.5 4.5L6 12L2.5 8.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
	</svg>
);

// A modern Listbox-based dropdown matching the app's styling.
function Dropdown({ value, options, onChange, className = '' }) {
	const selected = options.find((o) => o.key === value) || options[0];
	return (
		<Listbox value={value} onChange={onChange}>
			<div className={`relative ${className}`}>
				<Listbox.Button className="flex w-full items-center justify-between gap-[8px] rounded-[8px] border border-[#E5E7EB] bg-white px-[12px] py-[8px] text-[14px] text-[#111827] transition-colors hover:border-[#D1D5DB] focus:outline-none focus:ring-2 focus:ring-[#5048ED] focus:border-transparent">
					<span className="block truncate text-left">{selected.label}</span>
					<ChevronIcon />
				</Listbox.Button>
				<Transition
					as={Fragment}
					leave="transition ease-in duration-100"
					leaveFrom="opacity-100"
					leaveTo="opacity-0"
				>
					<Listbox.Options className="absolute z-[60] mt-[4px] max-h-60 w-full min-w-[140px] overflow-auto rounded-[10px] border border-[#E5E7EB] bg-white py-[6px] shadow-lg focus:outline-none">
						{options.map((option) => (
							<Listbox.Option
								key={option.key}
								value={option.key}
								className={({ active }) =>
									`relative flex cursor-pointer select-none items-center justify-between px-[12px] py-[8px] text-[14px] ${
										active ? 'bg-[#F5F4FF] text-[#5048ED]' : 'text-[#111827]'
									}`
								}
							>
								{({ selected: isSelected }) => (
									<>
										<span className={`block truncate ${isSelected ? 'font-medium' : 'font-normal'}`}>
											{option.label}
										</span>
										{isSelected && <CheckIcon />}
									</>
								)}
							</Listbox.Option>
						))}
					</Listbox.Options>
				</Transition>
			</div>
		</Listbox>
	);
}

// Controlled token TTL editor.
// value: number of seconds, 0 ("never"), or '' / null / undefined ("inherit").
// onChange(nextValue) receives the same shape.
// inheritedValue: seconds (0 = never) of the value this level inherits when not
//   overridden, shown on the inherit option so admins see the effective value.
// inheritLabel: wording for the inherit option (e.g. "Platform default" or, for a
//   role that inherits an app-level override, "App default").
export default function TokenTtlField({
	value,
	onChange,
	inheritedValue,
	inheritLabel = 'Platform default',
}) {
	const [mode, setMode] = useState(() => ttlMode(value));
	const [unit, setUnit] = useState(() => splitTtlSeconds(value).unit);
	// Tracks the value this component last emitted, so the sync effect can tell a
	// self-induced change (e.g. picking "custom" -> '') apart from an external
	// reset (role switch / modal reopen) and only force-resync on the latter.
	const lastEmitted = useRef(value);

	const defaultLabel =
		inheritedValue === undefined || inheritedValue === null
			? inheritLabel
			: `${inheritLabel} (${humanizeTokenTtl(inheritedValue)})`;

	const modeOptions = [
		{ key: 'default', label: defaultLabel },
		{ key: 'never', label: 'Never expires' },
		{ key: 'custom', label: 'Custom' },
	];

	// Emit a change upward and remember what we sent, so the sync effect can
	// distinguish our own updates from external ones.
	const emit = (next) => {
		lastEmitted.current = next;
		onChange(next);
	};

	// Re-sync local mode/unit only when the value changes from the OUTSIDE
	// (role switch / modal reopen). Self-induced changes are ignored so that
	// picking "custom" (which emits '') doesn't snap the dropdown back to
	// "default" before the user types a number.
	useEffect(() => {
		if (value === lastEmitted.current) return;
		lastEmitted.current = value;
		setMode(ttlMode(value));
		setUnit(splitTtlSeconds(value).unit);
	}, [value]);

	const handleModeChange = (nextMode) => {
		setMode(nextMode);
		if (nextMode === 'default') emit('');
		else if (nextMode === 'never') emit(0);
		else emit(''); // custom: wait for the user to type a number
	};

	const handleUnitChange = (nextUnit) => {
		if (value !== '' && value !== null && value !== undefined && value !== 0) {
			const oldU = TTL_UNITS.find((u) => u.key === unit) || TTL_UNITS[0];
			const displayed = value / oldU.seconds;
			emit(ttlToSeconds(displayed, nextUnit));
		}
		setUnit(nextUnit);
	};

	const numberValue = (() => {
		if (mode !== 'custom' || value === '' || value === null || value === undefined) return '';
		const u = TTL_UNITS.find((x) => x.key === unit) || TTL_UNITS[0];
		return value / u.seconds;
	})();

	return (
		<div className="flex flex-wrap items-start gap-[8px]">
			<Dropdown
				value={mode}
				options={modeOptions}
				onChange={handleModeChange}
				className="w-[230px]"
			/>
			{mode === 'custom' && (
				<>
					<input
						type="number"
						min="1"
						placeholder="e.g. 7"
						value={numberValue}
						onChange={(e) =>
							emit(e.target.value === '' ? '' : ttlToSeconds(e.target.value, unit))
						}
						className="w-[110px] rounded-[8px] border border-[#E5E7EB] px-[12px] py-[8px] text-[14px] text-[#111827] focus:outline-none focus:ring-2 focus:ring-[#5048ED] focus:border-transparent"
					/>
					<Dropdown
						value={unit}
						options={TTL_UNITS.map((u) => ({ key: u.key, label: u.label }))}
						onChange={handleUnitChange}
						className="w-[130px]"
					/>
				</>
			)}
		</div>
	);
}
