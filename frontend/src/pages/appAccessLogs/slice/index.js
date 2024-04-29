import { createSlice } from '@reduxjs/toolkit';

export const appAccessLogsSlice = createSlice({
	name: 'appAccessLogs',
	initialState: {
		isAddNewUserRolesModalOpen: false,
		isEditUserRolesDetailModalOpen: false,
		isDeactivateUserRolesModalOpen: false,
		isActivateUserRolesModalOpen: false,
		rerenderPage: false,
		appAccessLogsData: null,
		appAccessLogsFormData: null,
		appAccessLogsTableData: {
			searchValue: '',
			columns: [],
			pageIndex: 0,
			pageSize: 10,
		},
		isAppAccessLogsDataEmpty: true,
	},
	reducers: {
		toggleIsAddNewUserRolesModalOpen: (state) => {
			state.isAddNewUserRolesModalOpen = !state.isAddNewUserRolesModalOpen;
		},
		openIsAddNewUserRolesModalOpen: (state, action) => {
			state.isAddNewUserRolesModalOpen = true;
			state.appAccessLogsFormData = action.payload;
		},
		closeIsAddNewUserRolesModalOpen: (state, action) => {
			state.isAddNewUserRolesModalOpen = false;
			state.appAccessLogsFormData = null;
		},
		toggleIsEditUserRolesDetailModalOpen: (state) => {
			state.isEditUserRolesDetailModalOpen =
				!state.isEditUserRolesDetailModalOpen;
		},
		openIsEditUserRolesDetailModalOpen: (state, action) => {
			state.isEditUserRolesDetailModalOpen = true;
			state.appAccessLogsFormData = action.payload;
		},
		closeIsEditUserRolesDetailModalOpen: (state) => {
			state.isEditUserRolesDetailModalOpen = false;
			state.appAccessLogsFormData = null;
		},
		toggleIsDeactivateUserRolesModalOpen: (state) => {
			state.isDeactivateUserRolesModalOpen =
				!state.isDeactivateUserRolesModalOpen;
		},
		openIsDeactivateUserRolesModalOpen: (state, action) => {
			state.isDeactivateUserRolesModalOpen = true;
			state.appAccessLogsFormData = action.payload;
		},
		closeIsDeactivateUserRolesModalOpen: (state) => {
			state.isDeactivateUserRolesModalOpen = false;
			state.appAccessLogsFormData = null;
		},
		toggleIsActivateUserRolesModalOpen: (state) => {
			state.isActivateUserRolesModalOpen = !state.isActivateUserRolesModalOpen;
		},
		openIsActivateUserRolesModalOpen: (state, action) => {
			state.isActivateUserRolesModalOpen = true;
			state.appAccessLogsFormData = action.payload;
		},
		closeIsActivateUserRolesModalOpen: (state) => {
			state.isActivateUserRolesModalOpen = false;
			state.appAccessLogsFormData = null;
		},
		setAppAccessLogsData: (state, action) => {
			state.appAccessLogsData = action.payload;
			state.isAppAccessLogsDataEmpty =
				action.payload?.access_logs?.records?.length ||
				state?.appAccessLogsTableData?.searchValue ||
				state?.appAccessLogsTableData?.columns?.length
					? false
					: true;
		},
		setAppAccessLogsTableData: (state, action) => {
			state.appAccessLogsTableData = action.payload;
		},
		toggleRerenderPage: (state) => {
			state.rerenderPage = !state.rerenderPage;
		},
	},
});

export const {
	toggleIsAddNewUserRolesModalOpen,
	openIsAddNewUserRolesModalOpen,
	closeIsAddNewUserRolesModalOpen,
	toggleIsEditUserRolesDetailModalOpen,
	openIsEditUserRolesDetailModalOpen,
	closeIsEditUserRolesDetailModalOpen,
	toggleIsDeactivateUserRolesModalOpen,
	openIsDeactivateUserRolesModalOpen,
	closeIsDeactivateUserRolesModalOpen,
	toggleIsActivateUserRolesModalOpen,
	openIsActivateUserRolesModalOpen,
	closeIsActivateUserRolesModalOpen,
	setAppAccessLogsData,
	setAppAccessLogsTableData,
	toggleRerenderPage,
} = appAccessLogsSlice.actions;

export const selectIsAddNewUserRolesModalOpen = (state) =>
	state.appAccessLogs.isAddNewUserRolesModalOpen;

export const selectIsEditUserRolesDetailModalOpen = (state) =>
	state.appAccessLogs.isEditUserRolesDetailModalOpen;

export const selectIsDeactivateUserRolesModalOpen = (state) =>
	state.appAccessLogs.isDeactivateUserRolesModalOpen;

export const selectIsActivateUserRolesModalOpen = (state) =>
	state.appAccessLogs.isActivateUserRolesModalOpen;

export const selectRerenderPage = (state) => state.appAccessLogs.rerenderPage;

export const selectAppAccessLogsData = (state) =>
	state.appAccessLogs.appAccessLogsData;

export const selectAppAccessLogsFormData = (state) =>
	state.appAccessLogs.appAccessLogsFormData;

export const selectAppAccessLogsTableData = (state) =>
	state.appAccessLogs.appAccessLogsTableData;

export const selectIsAppAccessLogsDataEmpty = (state) =>
	state.appAccessLogs.isAppAccessLogsDataEmpty;

export default appAccessLogsSlice.reducer;
