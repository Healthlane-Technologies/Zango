import debounce from 'just-debounce-it';
import * as React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import Table from '../../../../components/Table';
import {
	openIsViewPolicyModalOpen,
	selectAppPoliciesManagementData,
	selectAppPoliciesManagementTableData,
	setAppPoliciesManagementData,
	setAppPoliciesManagementTableData,
} from '../../slice';
import SyncPolicy from '../SyncPolicy';
import columns from './columns';
import RowMenu from './RowMenu';

export default function AppTable() {
	const { appId } = useParams();

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

	function updatePageData(value) {
		dispatch(setAppPoliciesManagementData(value));
	}

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
			pageData={appPoliciesManagementData}
			pageId={'policies'}
			apiUrl={`/api/v1/apps/${appId}/policies/`}
			updatePageData={updatePageData}
			updateLocalTableData={updateLocalTableData}
			RowMenu={RowMenu}
			haveSideMenu={false}
			SearchFilters={<SyncPolicy />}
		/>
	);
}
