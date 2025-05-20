import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import useApi from '../../../../hooks/useApi';
import BreadCrumbs from '../../../app/components/BreadCrumbs';
import { ReactComponent as AddUserIcon } from '../../../../assets/images/svg/add-user-icon.svg';
import { setAddSecretModalOpen } from '../../slice/Index';
import AddSecretModal from '../Modals/AddSecretModal';
import EditSecretModal from '../Modals/EditSecretModal';


import Table from '../table/Index';
import {selectRerenderPage, selectAppSecretsData, selectAppSecretsTableData, selectIsAppSecretsDataEmpty, setAppSecretsData } from '../../slice/Index';

export default function  Secrets() {
	let { appId } = useParams();
	const appSecretsData = useSelector(selectAppSecretsData);
	console.log(appSecretsData,'appSecretsData');
	const appSecretsTableData = useSelector(selectAppSecretsTableData);
	const rerenderPage = useSelector(selectRerenderPage);
	const isAppSecretsDataEmpty= useSelector(selectIsAppSecretsDataEmpty);
	const dispatch = useDispatch();

	function updateAppSecretsData(value) {
		dispatch(setAppSecretsData(value));
		
	}

	const triggerApi = useApi();

	useEffect(() => {
		let columnFilter = appSecretsTableData?.columns
			? appSecretsTableData?.columns
					?.map(({ id, value }) => {
						return `&search_${id}=${value}`;
					})
					.join('')
			: '';

		const makeApiCall = async () => {
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/secrets/?page=${
					appSecretsTableData?.pageIndex + 1
				}&page_size=${
					appSecretsTableData?.pageSize
				}&include_dropdown_options=true&search=${
					appSecretsTableData?.searchValue
				}${columnFilter?.length ? columnFilter : ''}`,
				type: 'GET',
				loader: true,
			});
			if (success && response) {
				console.log('appSecrets data !!!!' ,response);
				updateAppSecretsData(response);
			}
		};

		makeApiCall();
	}, [rerenderPage]);

	const handleAddSecret = () => {
		console.log('handleAddSecret');
		
		dispatch(setAddSecretModalOpen(true));
	};

	return (
		<>
			<div className="flex grow flex-col gap-[20px]">
				<div className="flex items-center justify-between py-[12px] pl-[40px] pr-[48px]">
					<BreadCrumbs />

					<button
						data-cy="new_user_button"
						type="button"
						onClick={handleAddSecret}
						className="flex gap-[8px] rounded-[4px] bg-primary px-[16px] py-[7px]"
					>
						<span className="font-lato text-[14px] font-bold leading-[20px] text-[#FFFFFF]">
							Add Secret
						</span>
						<AddUserIcon />
					</button>
				</div>
				<div className="flex grow flex-col overflow-x-auto">
					{isAppSecretsDataEmpty ? (
						<div className="flex grow flex-col items-center justify-center gap-[56px]">
							<div className="flex flex-col items-center justify-center gap-[8px]">
								<h3 className="first-app-text font-source-sans-pro text-[64px] font-[700] leading-[72px] ">
									Secret(s)
								</h3>
							</div>
						</div>
					) : appSecretsData ? (
						<Table tableData={appSecretsData?.users} />
					) : null}
				</div>
			</div>
			<AddSecretModal />
			<EditSecretModal />
		</>
	);
}
