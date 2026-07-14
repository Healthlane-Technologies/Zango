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
export const humanizeTimeout = (seconds) => {
	if (isBlank(seconds)) return 'Inherited';
	const { value, unit } = splitTimeoutSeconds(seconds);
	const u = TIMEOUT_UNITS.find((x) => x.key === unit) || TIMEOUT_UNITS[0];
	const label = value === 1 ? u.label.replace(/s$/, '') : u.label;
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

// Convenience: summarize a warn/expire pair for read-only rows.
export const humanizeSessionTimeout = (warn, expire, platformWarn, platformExpire) => {
	if (isBlank(warn) && isBlank(expire)) {
		if (isBlank(platformExpire)) return 'Platform default';
		return `Platform default (${humanizeTimeout(platformExpire)})`;
	}
	const w = isBlank(warn) ? platformWarn : warn;
	const e = isBlank(expire) ? platformExpire : expire;
	return `Logout ${humanizeTimeout(e)}, warn ${humanizeTimeout(w)}`;
};
