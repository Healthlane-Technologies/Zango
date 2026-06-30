// Helpers for the auth token TTL (token_ttl), stored internally as seconds.
// 0 = "never expires"; '' / null / undefined = "inherit platform default".

export const TTL_UNITS = [
	{ key: 'seconds', label: 'Seconds', seconds: 1 },
	{ key: 'minutes', label: 'Minutes', seconds: 60 },
	{ key: 'hours', label: 'Hours', seconds: 3600 },
	{ key: 'days', label: 'Days', seconds: 86400 },
];

// Convert a (value, unit) pair to a whole number of seconds.
export const ttlToSeconds = (value, unit) => {
	const u = TTL_UNITS.find((x) => x.key === unit) || TTL_UNITS[0];
	const num = parseInt(value);
	if (Number.isNaN(num)) return '';
	return num * u.seconds;
};

// Split a seconds value into the largest unit that divides it evenly, so an
// existing value is shown in the most natural unit (e.g. 86400 -> 1 day).
export const splitTtlSeconds = (seconds) => {
	if (seconds === '' || seconds === null || seconds === undefined) {
		return { value: '', unit: 'seconds' };
	}
	if (seconds === 0) return { value: 0, unit: 'seconds' };
	// Largest unit first.
	for (let i = TTL_UNITS.length - 1; i >= 0; i--) {
		const u = TTL_UNITS[i];
		if (seconds % u.seconds === 0) {
			return { value: seconds / u.seconds, unit: u.key };
		}
	}
	return { value: seconds, unit: 'seconds' };
};

// Map a stored token_ttl value to the editor "mode".
//   '' / null / undefined -> 'default' (inherit platform default)
//   0                      -> 'never'
//   > 0                    -> 'custom'
export const ttlMode = (seconds) => {
	if (seconds === '' || seconds === null || seconds === undefined) return 'default';
	if (seconds === 0) return 'never';
	return 'custom';
};

// Human-readable label for a stored seconds value, adapting the unit.
// Returns a sentinel string for the inherit / never cases.
export const humanizeTokenTtl = (seconds) => {
	if (seconds === '' || seconds === null || seconds === undefined) {
		return 'Platform default';
	}
	if (seconds === 0) return 'Never expires';
	const { value, unit } = splitTtlSeconds(seconds);
	const u = TTL_UNITS.find((x) => x.key === unit) || TTL_UNITS[0];
	const label = value === 1 ? u.label.replace(/s$/, '') : u.label;
	return `${value} ${label.toLowerCase()}`;
};

// Like humanizeTokenTtl, but for read-only displays that also know the platform
// default. When the value is inherited, shows e.g. "Platform default (1 day)".
export const humanizeTokenTtlWithDefault = (seconds, platformDefault) => {
	if (seconds === '' || seconds === null || seconds === undefined) {
		if (platformDefault === undefined || platformDefault === null) {
			return 'Platform default';
		}
		return `Platform default (${humanizeTokenTtl(platformDefault)})`;
	}
	return humanizeTokenTtl(seconds);
};
