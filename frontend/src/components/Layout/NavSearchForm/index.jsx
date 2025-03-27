import { Formik, useFormikContext } from 'formik';
import debounce from 'just-debounce-it';
import { get } from 'lodash';
import { useCallback, useEffect, useState } from 'react';
import * as Yup from 'yup';
import { ReactComponent as SearchIcon } from '../../../assets/images/svg/search-icon.svg';
import SelectField from './SelectField';
import useApi from '../../../hooks/useApi';
import {useLocation} from 'react-router-dom'
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
};

export default function NavSearchForm() {
	const location = useLocation();
	const isValidPath =
		location.pathname === '/platform/apps' ||
		location.pathname === '/platform/apps/';
	const [isCeleryRunning, setIsCeleryRunning] = useState('Loading...');
	const triggerApi = useApi();
	let initialValues = {
		searchValue: '',
		searchType: 'Apps',
	};

	let validationSchema = Yup.object().shape({});

	const makeApiCall = async () => {};

	const fetchCeleryData = async () => {
		const { response, success } = await triggerApi({
			url: `/platform/celery-status/`,
			type: 'GET',
			loader: false,
			showErrorModal: false,
		});
		if (success) {
			console.log(response);
			if (response?.status === true) {
				setIsCeleryRunning('Running');
			} else {
				setIsCeleryRunning('Not Running');
			}
		}
	};

	useEffect(() => {
		if(isValidPath){
			fetchCeleryData();

			const intervalId = setInterval(fetchCeleryData, 7500);
	
			return () => clearInterval(intervalId);
		}
	}, [isValidPath]);

	let onSubmit = (values) => {
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
						<div className="flex gap-10">
							<div>
								<AutoSave debounceMs={300} />
								<div className="flex flex-col rounded-[4px] bg-[#F0F3F4] md:flex-row">
									<div className="flex flex-col gap-[4px]">
										<div className="flex items-center gap-[12px] rounded-[4px] bg-[#F0F3F4] px-[12px] py-[6px]">
											<SearchIcon />
											<input
												data-cy="table_search_field"
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
										label="SearchType"
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
							</div>
							{
								isValidPath && (
								<div
									className={`flex font-semibold rounded-sm px-5 items-center justify-center text-xs ${
										isCeleryRunning === 'Running'
											? 'bg-green-200'
											: isCeleryRunning === 'Not Running'
											? 'bg-red-200'
											: 'bg-gray-100'
									}`}
								>
									Celery Status: <span className={` ml-2 ${
										isCeleryRunning === 'Running'
										? 'text-green-700'
										: isCeleryRunning === 'Not Running'
										? 'text-red-700'
										: 'text-gray-700'
									}`}>{isCeleryRunning}</span> 
								</div>
								)
							}
							
						</div>
					</form>
				);
			}}
		</Formik>
	);
}
