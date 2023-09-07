import * as Yup from 'yup';
import { useState } from 'react';
import { useCallback } from 'react';
import { useEffect } from 'react';
import { useFormikContext, Formik, useField } from 'formik';
import debounce from 'just-debounce-it';
import useApi from '../../../../../hooks/useApi';
import { get } from 'lodash';

import { ReactComponent as SearchIcon } from '../../../../../assets/images/svg/search-icon.svg';
import SelectField from './SelectField';

const AutoSave = ({ debounceMs }) => {
	const formik = useFormikContext();
	const [lastSaved, setLastSaved] = useState(null);
	const debouncedSubmit = useCallback(
		debounce(() => {
			if (formik.isValid) {
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

export default function NavSearchForm() {
	let initialValues = {
		searchValue: '',
		searchType: 'Apps',
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
			// console.log('API CALL', values);
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
					<form
						className="complete-hidden-scroll-style flex flex-col gap-4"
						onSubmit={formik.handleSubmit}
					>
						<AutoSave debounceMs={300} />
						<div className="flex flex-col rounded-[4px] bg-[#F0F3F4] md:flex-row">
							<div className="flex flex-col gap-[4px]">
								<div className="flex items-center gap-[12px] rounded-[4px] bg-[#F0F3F4] py-[6px] px-[12px]">
									<SearchIcon />
									<input
										id="searchValue"
										name="searchValue"
										type="text"
										onChange={formik.handleChange}
										onBlur={formik.handleBlur}
										value={formik.values.searchValue}
										className="w-full bg-transparent font-lato text-sm outline-0 ring-0 placeholder:text-[#6C747D] md:w-[300px] lg:w-[537px]"
										placeholder="Search in Apps"
									/>
								</div>
								{formik.touched.searchValue && formik.errors.searchValue ? (
									<div className="font-open-sans text-form-xs text-[#cc3300]">
										{formik.errors.searchValue}
									</div>
								) : null}
							</div>
							<SelectField
								key="searchType"
								label="Stockist"
								name="searchType"
								id="searchType"
								placeholder="Select"
								value={get(formik.values, 'searchType', '')}
								optionsDataName="searchType"
								optionsData={[
									{ id: 'Apps', label: 'Apps' },
									{ id: 'User Management', label: 'User Management' },
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
