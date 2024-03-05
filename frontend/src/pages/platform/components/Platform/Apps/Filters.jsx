import { Formik, useFormikContext } from 'formik';
import debounce from 'just-debounce-it';
import { get } from 'lodash';
import { useCallback, useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import * as Yup from 'yup';
import { selectSortBy, setSortBy } from '../../../slice';
import SelectField from './SelectField';

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
	const sortBy = useSelector(selectSortBy);
	const dispatch = useDispatch();

	let initialValues = {
		sort: sortBy,
	};

	let validationSchema = Yup.object().shape({});

	let onSubmit = (values) => {
		dispatch(setSortBy(values.sort));
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
									{ id: 'alphabetical', label: 'Alphabetical' },
									{ id: 'date_created', label: 'Date Created' },
									{ id: 'last_modified', label: 'Last Modified' },
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
