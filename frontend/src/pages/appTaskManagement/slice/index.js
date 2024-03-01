import { createSlice } from '@reduxjs/toolkit';

export const appTaskManagementSlice = createSlice({
	name: 'appTaskManagement',
	initialState: {
		isUpdatePolicyModalOpen: false,
		isRemoveAllPoliciesModalOpen: false,
		rerenderPage: false,
		appTaskManagementData: null,
		appTaskManagementFormData: null,
		appTaskManagementTableData: {
			searchValue: '',
			columns: [],
			pageIndex: 0,
			pageSize: 10,
		},
		isAppTaskManagementDataEmpty: true,
	},
	reducers: {
		toggleIsUpdatePolicyModalOpen: (state) => {
			state.isUpdatePolicyModalOpen += !state.isUpdatePolicyModalOpen;
		},
		openIsUpdatePolicyModalOpen: (state, action) => {
			state.isUpdatePolicyModalOpen = true;
			state.appTaskManagementFormData = action.payload;
		},
		closeIsUpdatePolicyModalOpen: (state) => {
			state.isUpdatePolicyModalOpen = false;
			state.appTaskManagementFormData = null;
		},
		toggleIsRemoveAllPoliciesModalOpen: (state) => {
			state.isRemoveAllPoliciesModalOpen += !state.isRemoveAllPoliciesModalOpen;
		},
		openIsRemoveAllPoliciesModalOpen: (state, action) => {
			state.isRemoveAllPoliciesModalOpen = true;
			state.appTaskManagementFormData = action.payload;
		},
		closeIsRemoveAllPoliciesModalOpen: (state) => {
			state.isRemoveAllPoliciesModalOpen = false;
			state.appTaskManagementFormData = null;
		},
		setAppTaskManagementData: (state, action) => {
			state.appTaskManagementData = action.payload;
			state.isAppTaskManagementDataEmpty =
				action.payload?.tasks?.records?.length ||
				state?.appTaskManagementTableData?.searchValue ||
				state?.appTaskManagementTableData?.columns?.length
					? false
					: true;
		},
		setAppTaskManagementTableData: (state, action) => {
			state.appTaskManagementTableData = action.payload;
		},
		toggleRerenderPage: (state) => {
			state.rerenderPage = !state.rerenderPage;
		},
	},
});

export const {
	toggleIsUpdatePolicyModalOpen,
	openIsUpdatePolicyModalOpen,
	closeIsUpdatePolicyModalOpen,
	toggleIsRemoveAllPoliciesModalOpen,
	openIsRemoveAllPoliciesModalOpen,
	closeIsRemoveAllPoliciesModalOpen,
	setAppTaskManagementData,
	setAppTaskManagementTableData,

	toggleRerenderPage,
} = appTaskManagementSlice.actions;

export const selectIsUpdatePolicyModalOpen = (state) =>
	state.appTaskManagement.isUpdatePolicyModalOpen;

export const selectIsRemoveAllPoliciesModalOpen = (state) =>
	state.appTaskManagement.isRemoveAllPoliciesModalOpen;

export const selectRerenderPage = (state) =>
	state.appTaskManagement.rerenderPage;

export const selectAppTaskManagementData = (state) =>
	state.appTaskManagement.appTaskManagementData;

export const selectAppTaskManagementTableData = (state) =>
	state.appTaskManagement.appTaskManagementTableData;

export const selectAppTaskManagementFormData = (state) =>
	state.appTaskManagement.appTaskManagementFormData;

export const selectIsAppTaskManagementDataEmpty = (state) =>
	state.appTaskManagement.isAppTaskManagementDataEmpty;

export default appTaskManagementSlice.reducer;
