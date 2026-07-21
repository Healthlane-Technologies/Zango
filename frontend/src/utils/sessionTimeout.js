// Helpers for the idle-session timeout (session_warn_after / session_expire_after),
// each stored internally as seconds. '' / null / undefined = "inherit default".
// warn_after must be < expire_after.

// Reuse the same unit table as token TTL for a consistent unit selector.
export const TIMEOUT_UNITS = [
	{ key: 'seconds', label: 'Seconds', seconds: 1 },
	{ key: 'minutes', label: 'Minutes', seconds: 60 },
	{ key: 'hours', label: 'Hours', seconds: 3600 },
];

const isBlank = (v) => v === '' || v === null || v === undefined;

// Convert a (value, unit) pair to a whole number of seconds.
export const timeoutToSeconds = (value, unit) => {
	const u = TIMEOUT_UNITS.find((x) => x.key === unit) || TIMEOUT_UNITS[0];
	const num = parseInt(value);
	if (Number.isNaN(num)) return '';
	return num * u.seconds;
};

// Split a seconds value into the largest unit that divides it evenly.
// Exact by design: the editor round-trips values through this, so it must never
// round (see humanizeTimeout for the display-only, rounded variant).
export const splitTimeoutSeconds = (seconds) => {
	if (isBlank(seconds)) return { value: '', unit: 'minutes' };
	for (let i = TIMEOUT_UNITS.length - 1; i >= 0; i--) {
		const u = TIMEOUT_UNITS[i];
		if (seconds % u.seconds === 0) {
			return { value: seconds / u.seconds, unit: u.key };
		}
	}
	return { value: seconds, unit: 'seconds' };
};

// Map a stored value to the editor "mode": blank -> inherit, else custom.
export const timeoutMode = (seconds) => (isBlank(seconds) ? 'default' : 'custom');

// Human-readable label for a stored seconds value, adapting the unit.
// Display-only: picks the largest unit the value reaches and rounds to at most
// one decimal, so an odd value (e.g. the platform default of 2000s) reads as
// "33.3 minutes" rather than "2000 seconds". Never use this to derive a stored
// value -- use splitTimeoutSeconds, which is exact.
export const humanizeTimeout = (seconds) => {
	if (isBlank(seconds)) return 'Inherited';
	const unit =
		[...TIMEOUT_UNITS].reverse().find((u) => seconds >= u.seconds) || TIMEOUT_UNITS[0];
	const value = Math.round((seconds / unit.seconds) * 10) / 10;
	const label = value === 1 ? unit.label.replace(/s$/, '') : unit.label;
	return `${value} ${label.toLowerCase()}`;
};

// Read-only display that also knows the inherited default. When the value is
// inherited, shows e.g. "Platform default (30 minutes)".
export const humanizeTimeoutWithDefault = (seconds, inheritedDefault, inheritLabel = 'Platform default') => {
	if (isBlank(seconds)) {
		if (isBlank(inheritedDefault)) return inheritLabel;
		return `${inheritLabel} (${humanizeTimeout(inheritedDefault)})`;
	}
	return humanizeTimeout(seconds);
};

// Resolve a configured value against its inherited default. Returns the
// effective seconds, or undefined when neither is known.
const effective = (value, inherited) => (isBlank(value) ? inherited : value);

// Effective sign-out time for read-only displays, e.g. "30 minutes" when set,
// or "Platform default (200 minutes)" when inherited.
export const humanizeSessionExpiry = (expire, platformExpire, inheritLabel) =>
	humanizeTimeoutWithDefault(expire, platformExpire, inheritLabel);

// Effective warning time for read-only displays.
export const humanizeSessionWarning = (warn, platformWarn, inheritLabel) =>
	humanizeTimeoutWithDefault(warn, platformWarn, inheritLabel);

// True when neither value is overridden at this level (so the UI can label the
// display as inherited rather than app-specific).
export const isSessionTimeoutInherited = (warn, expire) => isBlank(warn) && isBlank(expire);

// One-line summary of the effective idle timeout, e.g.
// "30 minutes (warn at 25 minutes)", or "Platform default (30 minutes)" when
// nothing is overridden at this level.
export const humanizeSessionTimeout = (warn, expire, platformWarn, platformExpire) => {
	const e = effective(expire, platformExpire);
	const w = effective(warn, platformWarn);
	if (isBlank(e)) return 'Platform default';
	const base = isSessionTimeoutInherited(warn, expire)
		? `Platform default (${humanizeTimeout(e)})`
		: humanizeTimeout(e);
	if (isBlank(w)) return base;
	return `${base} · warn at ${humanizeTimeout(w)}`;
};
