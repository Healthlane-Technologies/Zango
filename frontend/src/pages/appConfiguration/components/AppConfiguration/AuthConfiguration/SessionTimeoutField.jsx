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
					<Listbox.Options className="absolute z-[60] mt-[4px] max-h-60 w-max min-w-full overflow-auto rounded-[10px] border border-[#E5E7EB] bg-white py-[6px] shadow-lg focus:outline-none">
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

const isBlank = (v) => v === '' || v === null || v === undefined;

// Controlled editor for a single idle-timeout duration (stored as seconds).
// Mirrors TokenTtlField: a mode dropdown (inherit / custom) plus, in custom
// mode, a number input and a unit selector.
//
// value: seconds, or '' / null / undefined ("inherit the default").
// onChange(nextValue) receives the same shape.
// inheritedValue: seconds this level inherits when not overridden, shown on the
//   inherit option so admins see the effective value.
// inheritLabel: wording for the inherit option ("Platform default" / "App default").
// onValidityChange(isValid): notified whenever this field's validity changes.
//   The field is invalid only when "Custom" is selected but no value is entered
//   -- so the parent form can block submit immediately. The inline error text,
//   however, only appears once the input has been blurred while empty, or when
//   the parent forces it via forceShowError (a submit attempt) -- so we don't
//   accuse the user of an empty field the instant they pick "Custom".
export default function SessionTimeoutField({
	value,
	onChange,
	inheritedValue,
	inheritLabel = 'Platform default',
	placeholder = 'e.g. 30',
	onValidityChange,
	forceShowError = false,
}) {
	const [mode, setMode] = useState(() => (isBlank(value) ? 'default' : 'custom'));
	const [unit, setUnit] = useState(() => splitTimeoutSeconds(value).unit);
	// Whether the custom input has been blurred while empty; gates the inline error.
	const [touched, setTouched] = useState(false);
	// Tracks the value this component last emitted, so the sync effect can tell a
	// self-induced change (e.g. picking "custom" -> '') apart from an external
	// reset (role switch / modal reopen) and only force-resync on the latter.
	const lastEmitted = useRef(value);

	const defaultLabel = isBlank(inheritedValue)
		? inheritLabel
		: `${inheritLabel} (${humanizeTimeout(inheritedValue)})`;

	const modeOptions = [
		{ key: 'default', label: defaultLabel },
		{ key: 'custom', label: 'Custom' },
	];

	const emit = (next) => {
		lastEmitted.current = next;
		onChange(next);
	};

	// Re-sync local mode/unit only when the value changes from the OUTSIDE.
	useEffect(() => {
		if (value === lastEmitted.current) return;
		lastEmitted.current = value;
		setMode(isBlank(value) ? 'default' : 'custom');
		setUnit(splitTimeoutSeconds(value).unit);
	}, [value]);

	const handleModeChange = (nextMode) => {
		setMode(nextMode);
		setTouched(false); // fresh selection: don't show "empty" error until blur
		emit(''); // both inherit and custom start blank; custom waits for input
	};

	const handleUnitChange = (nextUnit) => {
		if (!isBlank(value)) {
			const oldU = TIMEOUT_UNITS.find((u) => u.key === unit) || TIMEOUT_UNITS[0];
			const displayed = value / oldU.seconds;
			emit(timeoutToSeconds(displayed, nextUnit));
		}
		setUnit(nextUnit);
	};

	const numberValue = (() => {
		if (mode !== 'custom' || isBlank(value)) return '';
		const u = TIMEOUT_UNITS.find((x) => x.key === unit) || TIMEOUT_UNITS[0];
		return value / u.seconds;
	})();

	// "Custom" selected but nothing typed -> incomplete, so the form must not
	// submit. Inherit mode (blank) is fine; a filled custom value is fine.
	const isEmptyCustom = mode === 'custom' && isBlank(value);
	// Show the inline error only once the user has blurred the empty input or the
	// parent forces it on a submit attempt -- not the instant "Custom" is picked.
	const showError = isEmptyCustom && (touched || forceShowError);

	useEffect(() => {
		if (onValidityChange) onValidityChange(!isEmptyCustom);
		// On unmount (e.g. switching away from this config section) report valid,
		// so a stale "incomplete" state can't keep the form's Save button disabled.
		return () => {
			if (onValidityChange) onValidityChange(true);
		};
	}, [isEmptyCustom, onValidityChange]);

	return (
		<div>
			<div className="flex flex-wrap items-center gap-[8px]">
				<Dropdown
					value={mode}
					options={modeOptions}
					onChange={handleModeChange}
					className={mode === 'custom' ? 'w-[150px]' : 'min-w-[260px] flex-1 max-w-[340px]'}
				/>
				{mode === 'custom' && (
					<>
						<input
							type="number"
							min="1"
							step="1"
							placeholder={placeholder}
							value={numberValue}
							onKeyDown={(e) => {
								// Block characters that would make a zero/negative/decimal value:
								// '-' (negative), 'e'/'E' (exponent), '.' (fractional).
								if (['-', 'e', 'E', '.', '+'].includes(e.key)) e.preventDefault();
							}}
							onChange={(e) => {
								const raw = e.target.value;
								if (raw === '') return emit('');
								// Only accept a positive whole number; a 0 or negative entry
								// is ignored so it can never reach the config or the server.
								const n = parseInt(raw, 10);
								if (Number.isNaN(n) || n < 1) return;
								emit(timeoutToSeconds(n, unit));
							}}
							onBlur={() => setTouched(true)}
							className="w-[110px] rounded-[8px] border border-[#E5E7EB] px-[12px] py-[8px] text-[14px] text-[#111827] focus:outline-none focus:ring-2 focus:ring-[#5048ED] focus:border-transparent"
						/>
						<Dropdown
							value={unit}
							options={TIMEOUT_UNITS.map((u) => ({ key: u.key, label: u.label }))}
							onChange={handleUnitChange}
							className="w-[130px]"
						/>
					</>
				)}
			</div>
			{showError && (
				<p className="mt-[6px] text-[12px] text-[#DC2626]">
					Enter a value or choose {inheritLabel.toLowerCase()}.
				</p>
			)}
		</div>
	);
}
