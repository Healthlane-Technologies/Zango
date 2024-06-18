import { useFormikContext } from 'formik';
import debounce from 'just-debounce-it';
import { useCallback, useEffect, useState } from 'react';

const AutoSave = ({ debounceMs }) => {
	const formik = useFormikContext();
	const [lastSaved, setLastSaved] = useState(null);
	const debouncedSubmit = useCallback(
		debounce(() => {
			if (formik.touched && formik.isValid) {
				formik.submitForm().then(() => setLastSaved(new Date().toISOString()));
			}
		}, debounceMs),
		[debounceMs, formik.submitForm, formik.isValid]
	);

	useEffect(() => {
		debouncedSubmit();
	}, [debouncedSubmit, formik.values]);
};

export default AutoSave;
