import { createSlice } from '@reduxjs/toolkit';

export const appApplicationObjectsLogsSlice = createSlice({
	name: 'appApplicationObjectsLogs',
	initialState: {
		isAddNewUserModalOpen: false,
		isEditUserDetailModalOpen: false,
		isDeactivateUserModalOpen: false,
		isActivateUserModalOpen: false,
		isResetPasswordModalOpen: false,
		rerenderPage: false,
		appApplicationObjectsLogsData: null,
		appApplicationObjectsLogsFormData: null,
		appApplicationObjectsLogsTableData: {
			searchValue: '',
			columns: [],
			pageIndex: 0,
			pageSize: 10,
		},
		isAppApplicationObjectsLogsDataEmpty: true,
	},
	reducers: {
		toggleIsAddNewUserModalOpen: (state) => {
			state.isAddNewUserModalOpen = !state.isAddNewUserModalOpen;
		},
		openIsAddNewUserModalOpen: (state, action) => {
			state.isAddNewUserModalOpen = true;
			state.appApplicationObjectsLogsFormData = action.payload;
		},
		closeIsAddNewUserModalOpen: (state) => {
			state.isAddNewUserModalOpen = false;
			state.appApplicationObjectsLogsFormData = null;
		},
		toggleIsEditUserDetailModalOpen: (state) => {
			state.isEditUserDetailModalOpen = !state.isEditUserDetailModalOpen;
		},
		openIsEditUserDetailModalOpen: (state, action) => {
			state.isEditUserDetailModalOpen = true;
			state.appApplicationObjectsLogsFormData = action.payload;
		},
		closeIsEditUserDetailModalOpen: (state, action) => {
			state.isEditUserDetailModalOpen = false;
			state.appApplicationObjectsLogsFormData = action.payload;
		},
		toggleIsDeactivateUserModalOpen: (state) => {
			state.isDeactivateUserModalOpen = !state.isDeactivateUserModalOpen;
		},
		openIsDeactivateUserModalOpen: (state, action) => {
			state.isDeactivateUserModalOpen = true;
			state.appApplicationObjectsLogsFormData = action.payload;
		},
		closeIsDeactivateUserModalOpen: (state) => {
			state.isDeactivateUserModalOpen = false;
			state.appApplicationObjectsLogsFormData = null;
		},
		toggleIsActivateUserModalOpen: (state) => {
			state.isActivateUserModalOpen = !state.isActivateUserModalOpen;
		},
		openIsActivateUserModalOpen: (state, action) => {
			state.isActivateUserModalOpen = true;
			state.appApplicationObjectsLogsFormData = action.payload;
		},
		closeIsActivateUserModalOpen: (state) => {
			state.isActivateUserModalOpen = false;
			state.appApplicationObjectsLogsFormData = null;
		},
		toggleIsResetPasswordModalOpen: (state) => {
			state.isResetPasswordModalOpen = !state.isResetPasswordModalOpen;
		},
		openIsResetPasswordModalOpen: (state, action) => {
			state.isResetPasswordModalOpen = true;
			state.appApplicationObjectsLogsFormData = action.payload;
		},
		closeIsResetPasswordModalOpen: (state) => {
			state.isResetPasswordModalOpen = false;
			state.appApplicationObjectsLogsFormData = null;
		},
		setAppApplicationObjectsLogsData: (state, action) => {
			state.appApplicationObjectsLogsData = action.payload;
			state.isAppApplicationObjectsLogsDataEmpty =
				action.payload?.audit_logs?.records?.length ||
				state?.appApplicationObjectsLogsTableData?.searchValue ||
				state?.appApplicationObjectsLogsTableData?.columns?.length
					? false
					: true;
		},
		setAppApplicationObjectsLogsTableData: (state, action) => {
			state.appApplicationObjectsLogsTableData = action.payload;
		},
		toggleRerenderPage: (state) => {
			state.rerenderPage = !state.rerenderPage;
		},
	},
});

export const {
	toggleIsAddNewUserModalOpen,
	openIsAddNewUserModalOpen,
	closeIsAddNewUserModalOpen,
	toggleIsEditUserDetailModalOpen,
	openIsEditUserDetailModalOpen,
	closeIsEditUserDetailModalOpen,
	toggleIsDeactivateUserModalOpen,
	openIsDeactivateUserModalOpen,
	closeIsDeactivateUserModalOpen,
	toggleIsActivateUserModalOpen,
	openIsActivateUserModalOpen,
	closeIsActivateUserModalOpen,
	toggleIsResetPasswordModalOpen,
	openIsResetPasswordModalOpen,
	closeIsResetPasswordModalOpen,
	setAppApplicationObjectsLogsData,
	setAppApplicationObjectsLogsTableData,
	toggleRerenderPage,
} = appApplicationObjectsLogsSlice.actions;

export const selectIsAddNewUserModalOpen = (state) =>
	state.appApplicationObjectsLogs.isAddNewUserModalOpen;

export const selectIsEditUserDetailModalOpen = (state) =>
	state.appApplicationObjectsLogs.isEditUserDetailModalOpen;

export const selectIsDeactivateUserModalOpen = (state) =>
	state.appApplicationObjectsLogs.isDeactivateUserModalOpen;

export const selectIsActivateUserModalOpen = (state) =>
	state.appApplicationObjectsLogs.isActivateUserModalOpen;

export const selectIsResetPasswordModalOpen = (state) =>
	state.appApplicationObjectsLogs.isResetPasswordModalOpen;

export const selectRerenderPage = (state) =>
	state.appApplicationObjectsLogs.rerenderPage;

export const selectAppApplicationObjectsLogsData = (state) =>
	state.appApplicationObjectsLogs.appApplicationObjectsLogsData;

export const selectAppApplicationObjectsLogsTableData = (state) =>
	state.appApplicationObjectsLogs.appApplicationObjectsLogsTableData;

export const selectAppApplicationObjectsLogsFormData = (state) =>
	state.appApplicationObjectsLogs.appApplicationObjectsLogsFormData;

export const selectIsAppApplicationObjectsLogsDataEmpty = (state) =>
	state.appApplicationObjectsLogs.isAppApplicationObjectsLogsDataEmpty;

export default appApplicationObjectsLogsSlice.reducer;
