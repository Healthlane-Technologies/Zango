import { Fragment, useEffect, useRef, useState } from 'react';
import { Listbox, Transition } from '@headlessui/react';
import {
	TIMEOUT_UNITS,
	timeoutToSeconds,
	splitTimeoutSeconds,
	humanizeTimeout,
} from '../../../../../utils/sessionTimeout';

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

// A modern Listbox-based dropdown matching the app's styling (mirrors TokenTtlField).
function Dropdown({ value, options, onChange, className = '' }) {
	const selected = options.find((o) => o.key === value) || options[0];
	return (
		<Listbox value={value} onChange={onChange}>
			<div className={`relative ${className}`}>
				<Listbox.Button className="flex w-full items-center justify-between gap-[8px] rounded-[8px] border border-[#E5E7EB] bg-white px-[12px] py-[8px] text-[14px] text-[#111827] transition-colors hover:border-[#D1D5DB] focus:outline-none focus:ring-2 focus:ring-[#5048ED] focus:border-transparent">
					<span className="block truncate text-left">{selected.label}</span>
					<ChevronIcon />
				</Listbox.Button>
				<Transition as={Fragment} leave="transition ease-in duration-100" leaveFrom="opacity-100" leaveTo="opacity-0">
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
										<span className={`block truncate ${isSelected ? 'font-medium' : 'font-normal'}`}>{option.label}</span>
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

// A single labeled duration row (number + unit), stored as seconds.
function DurationRow({ label, value, onChange }) {
	const [unit, setUnit] = useState(() => splitTimeoutSeconds(value).unit);
	const lastEmitted = useRef(value);

	useEffect(() => {
		if (value === lastEmitted.current) return;
		lastEmitted.current = value;
		setUnit(splitTimeoutSeconds(value).unit);
	}, [value]);

	const emit = (next) => {
		lastEmitted.current = next;
		onChange(next);
	};

	const handleUnitChange = (nextUnit) => {
		if (value !== '' && value !== null && value !== undefined) {
			const oldU = TIMEOUT_UNITS.find((u) => u.key === unit) || TIMEOUT_UNITS[0];
			const displayed = value / oldU.seconds;
			emit(timeoutToSeconds(displayed, nextUnit));
		}
		setUnit(nextUnit);
	};

	const numberValue = (() => {
		if (value === '' || value === null || value === undefined) return '';
		const u = TIMEOUT_UNITS.find((x) => x.key === unit) || TIMEOUT_UNITS[0];
		return value / u.seconds;
	})();

	return (
		<div className="flex flex-wrap items-center gap-[8px]">
			<span className="w-[130px] text-[13px] text-[#374151]">{label}</span>
			<input
				type="number"
				min="1"
				placeholder="e.g. 25"
				value={numberValue}
				onChange={(e) => emit(e.target.value === '' ? '' : timeoutToSeconds(e.target.value, unit))}
				className="w-[110px] rounded-[8px] border border-[#E5E7EB] px-[12px] py-[8px] text-[14px] text-[#111827] focus:outline-none focus:ring-2 focus:ring-[#5048ED] focus:border-transparent"
			/>
			<Dropdown
				value={unit}
				options={TIMEOUT_UNITS.map((u) => ({ key: u.key, label: u.label }))}
				onChange={handleUnitChange}
				className="w-[130px]"
			/>
		</div>
	);
}

// Controlled idle-session timeout editor for a warn/expire pair.
// warnValue / expireValue: seconds, or '' / null / undefined ("inherit").
// onChange({ warn, expire }) receives both values (the pair moves together
// between "inherit" and "custom").
// inheritedWarn / inheritedExpire: the effective inherited values, shown on the
//   inherit option so admins see what will apply.
// inheritLabel: wording for the inherit option ("Platform default" / "App default").
export default function SessionTimeoutField({
	warnValue,
	expireValue,
	onChange,
	inheritedWarn,
	inheritedExpire,
	inheritLabel = 'Platform default',
}) {
	const isBlank = (v) => v === '' || v === null || v === undefined;
	const [mode, setMode] = useState(() => (isBlank(warnValue) && isBlank(expireValue) ? 'default' : 'custom'));
	const lastPair = useRef({ warn: warnValue, expire: expireValue });

	// Re-sync mode only on external resets (role switch / modal reopen).
	useEffect(() => {
		const same = warnValue === lastPair.current.warn && expireValue === lastPair.current.expire;
		if (same) return;
		lastPair.current = { warn: warnValue, expire: expireValue };
		setMode(isBlank(warnValue) && isBlank(expireValue) ? 'default' : 'custom');
	}, [warnValue, expireValue]);

	const emit = (warn, expire) => {
		lastPair.current = { warn, expire };
		onChange({ warn, expire });
	};

	const defaultLabel = isBlank(inheritedExpire)
		? inheritLabel
		: `${inheritLabel} (logout ${humanizeTimeout(inheritedExpire)})`;

	const modeOptions = [
		{ key: 'default', label: defaultLabel },
		{ key: 'custom', label: 'Custom' },
	];

	const handleModeChange = (nextMode) => {
		setMode(nextMode);
		if (nextMode === 'default') emit('', '');
		else emit('', ''); // custom: wait for the user to type
	};

	const invalid =
		mode === 'custom' &&
		!isBlank(warnValue) &&
		!isBlank(expireValue) &&
		Number(warnValue) >= Number(expireValue);

	return (
		<div className="flex flex-col gap-[10px]">
			<Dropdown value={mode} options={modeOptions} onChange={handleModeChange} className="w-[260px]" />
			{mode === 'custom' && (
				<div className="flex flex-col gap-[8px] rounded-[8px] border border-[#F0F0F0] bg-[#FAFAFA] p-[12px]">
					<DurationRow label="Warn after" value={warnValue} onChange={(w) => emit(w, expireValue)} />
					<DurationRow label="Auto-logout after" value={expireValue} onChange={(e) => emit(warnValue, e)} />
					{invalid && (
						<span className="text-[12px] text-[#DC2626]">Warn must be less than auto-logout.</span>
					)}
				</div>
			)}
		</div>
	);
}
