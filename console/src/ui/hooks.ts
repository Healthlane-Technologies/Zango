import { useEffect, useState } from 'react';

/** `value`, updated only after it has been stable for `ms`. For search-as-you-type. */
export function useDebounced<T>(value: T, ms = 300): T {
	const [v, setV] = useState(value);
	useEffect(() => {
		const t = setTimeout(() => setV(value), ms);
		return () => clearTimeout(t);
	}, [value, ms]);
	return v;
}
