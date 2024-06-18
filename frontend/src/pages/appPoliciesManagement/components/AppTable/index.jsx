import debounce from 'just-debounce-it';
import * as React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import Table from '../../../../components/Table';
import {
	openIsViewPolicyModalOpen,
	selectAppPoliciesManagementData,
	selectAppPoliciesManagementTableData,
	setAppPoliciesManagementTableData,
} from '../../slice';
import SyncPolicy from '../SyncPolicy';
import columns from './columns';
import RowMenu from './RowMenu';

export default function AppTable() {
	const appPoliciesManagementTableData = useSelector(
		selectAppPoliciesManagementTableData
	);

	const handleViewPolicyConfigure = (payload) => {
		dispatch(openIsViewPolicyModalOpen(payload));
	};

	const appPoliciesManagementData = useSelector(
		selectAppPoliciesManagementData
	);

	const dispatch = useDispatch();

	const updateLocalTableData = (data) => {
		dispatch(setAppPoliciesManagementTableData(data));
	};

	const debounceSearch = debounce((data) => {
		dispatch(setAppPoliciesManagementTableData(data));
	}, 500);

	return (
		<Table
			localTableData={appPoliciesManagementTableData}
			searchPlaceholder={'Search Polices by name / policy(s)'}
			tableData={appPoliciesManagementData?.policies}
			columns={columns({
				debounceSearch,
				localTableData: appPoliciesManagementTableData,
				handleViewPolicyConfigure: handleViewPolicyConfigure,
			})}
			updateLocalTableData={updateLocalTableData}
			RowMenu={RowMenu}
			SearchFilters={<SyncPolicy />}
		/>
	);
}
