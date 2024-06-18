import { createSlice } from '@reduxjs/toolkit';

export const appTaskManagementSlice = createSlice({
	name: 'appTaskManagement',
	initialState: {
		isUpdateTaskModalOpen: false,
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
		toggleIsUpdateTaskModalOpen: (state) => {
			state.isUpdateTaskModalOpen += !state.isUpdateTaskModalOpen;
		},
		openIsUpdateTaskModalOpen: (state, action) => {
			state.isUpdateTaskModalOpen = true;
			state.appTaskManagementFormData = action.payload;
		},
		closeIsUpdateTaskModalOpen: (state) => {
			state.isUpdateTaskModalOpen = false;
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
	toggleIsUpdateTaskModalOpen,
	openIsUpdateTaskModalOpen,
	closeIsUpdateTaskModalOpen,
	toggleIsRemoveAllPoliciesModalOpen,
	openIsRemoveAllPoliciesModalOpen,
	closeIsRemoveAllPoliciesModalOpen,
	setAppTaskManagementData,
	setAppTaskManagementTableData,

	toggleRerenderPage,
} = appTaskManagementSlice.actions;

export const selectIsUpdateTaskModalOpen = (state) =>
	state.appTaskManagement.isUpdateTaskModalOpen;

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
