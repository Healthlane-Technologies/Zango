import * as Yup from 'yup';
import { useState } from 'react';
import { useCallback } from 'react';
import { useEffect } from 'react';
import { useFormikContext, Formik, useField } from 'formik';
import debounce from 'just-debounce-it';
import useApi from '../../../../../hooks/useApi';
import { get } from 'lodash';

import SelectField from './SelectField';
import { useRef } from 'react';
import { useLayoutEffect } from 'react';

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

	return (
		<>
			{/* {!!formik.isSubmitting ? 'saving...' : lastSaved !== null ? `` : null} */}
		</>
	);
};

export default function Filters() {
	let initialValues = {
		sort: 'Alphabetical',
	};

	let validationSchema = Yup.object().shape({});

	const triggerApi = useApi();

	let onSubmit = (values) => {
		const makeApiCall = async () => {
			// const { response, success } = await triggerApi({
			// 	url: `/all-orders/?id_search=${values.searchValue}&start_date=${values.startDate}&&end_date=${values.endDate}&&status_search=${values.filter}`,
			// 	type: 'GET',
			// 	loader: true,
			// });

			// if (success && response) {
			// 	console.log([...response.data]);
			// }
			console.log('API CALL', values);
		};

		makeApiCall();
	};

	return (
		<Formik
			initialValues={initialValues}
			validationSchema={validationSchema}
			onSubmit={(values, { setSubmitting }) => {
				return new Promise((resolve) => {
					onSubmit(values);
					setSubmitting(false);
					resolve();
				});
			}}
		>
			{(formik) => {
				return (
					<form className="flex flex-col gap-4" onSubmit={formik.handleSubmit}>
						<AutoSave debounceMs={300} />
						<div className="flex gap-4 rounded-[4px]">
							<SelectField
								key="sort"
								label="Sort:"
								name="sort"
								id="sort"
								placeholder="Select"
								value={get(formik.values, 'sort', '')}
								optionsDataName="sort"
								optionsData={[
									{ id: 'Alphabetical', label: 'Alphabetical' },
									{ id: 'Date Created', label: 'Date Created' },
									{ id: 'Last Modified', label: 'Last Modified' },
								]}
								onChange={formik.handleChange}
								formik={formik}
							/>
						</div>
					</form>
				);
			}}
		</Formik>
	);
}
