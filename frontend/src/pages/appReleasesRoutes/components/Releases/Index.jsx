import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import useApi from '../../../../hooks/useApi';
import BreadCrumbs from '../../../app/components/BreadCrumbs';

import Table from '../table/Index';
import {selectRerenderPage, selectAppReleasesData, selectAppReleasesTableData, selectIsAppReleasesDataEmpty, setAppReleasesData } from '../../slice/Index';

export default function  Releases() {
	let { appId } = useParams();
	const appReleasesData = useSelector(selectAppReleasesData);
	console.log(appReleasesData,'appReleasesData');
	const appReleasesTableData = useSelector(selectAppReleasesTableData);
	const rerenderPage = useSelector(selectRerenderPage);
	const isAppReleasesDataEmpty= useSelector(selectIsAppReleasesDataEmpty);
	const dispatch = useDispatch();

	function updateAppReleasesData(value) {
		dispatch(setAppReleasesData(value));
		
	}

	const triggerApi = useApi();

	useEffect(() => {
		let columnFilter = appReleasesTableData?.columns
			? appReleasesTableData?.columns
					?.map(({ id, value }) => {
						return `&search_${id}=${value}`;
					})
					.join('')
			: '';

		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/releases/?page=${
					appReleasesTableData?.pageIndex + 1
				}&page_size=${
					appReleasesTableData?.pageSize
				}&include_dropdown_options=true&search=${
					appReleasesTableData?.searchValue
				}${columnFilter?.length ? columnFilter : ''}`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {

				console.log('appReleases data !!!!' ,response);
				updateAppReleasesData(response);
			}
		};

		makeApiCall();
	}, [rerenderPage]);

	return (
		<>
			<div className="flex grow flex-col gap-[20px]">
				<div className="flex items-center justify-between py-[12px] pl-[40px] pr-[48px]">
					<BreadCrumbs />
				</div>
				<div className="flex grow flex-col overflow-x-auto">
					{isAppReleasesDataEmpty ? (
						<div className="flex grow flex-col items-center justify-center gap-[56px]">
							<div className="flex flex-col items-center justify-center gap-[8px]">
								<h3 className="first-app-text font-source-sans-pro text-[64px] font-[700] leading-[72px] ">
									Release(s)
								</h3>
							</div>
						</div>
					) : appReleasesData ? (
						<Table tableData={appReleasesData?.users} />
					) : null}
				</div>
			</div>
		</>
	);
}
