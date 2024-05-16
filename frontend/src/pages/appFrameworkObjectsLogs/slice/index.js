import { createSlice } from '@reduxjs/toolkit';

export const appFrameworkObjectsLogsSlice = createSlice({
	name: 'appFrameworkObjectsLogs',
	initialState: {
		isAddNewUserModalOpen: false,
		isEditUserDetailModalOpen: false,
		isDeactivateUserModalOpen: false,
		isActivateUserModalOpen: false,
		isResetPasswordModalOpen: false,
		rerenderPage: false,
		appFrameworkObjectsLogsData: null,
		appFrameworkObjectsLogsFormData: null,
		appFrameworkObjectsLogsTableData: {
			searchValue: '',
			columns: [],
			pageIndex: 0,
			pageSize: 10,
		},
		isAppFrameworkObjectsLogsDataEmpty: true,
	},
	reducers: {
		toggleIsAddNewUserModalOpen: (state) => {
			state.isAddNewUserModalOpen = !state.isAddNewUserModalOpen;
		},
		openIsAddNewUserModalOpen: (state, action) => {
			state.isAddNewUserModalOpen = true;
			state.appFrameworkObjectsLogsFormData = action.payload;
		},
		closeIsAddNewUserModalOpen: (state) => {
			state.isAddNewUserModalOpen = false;
			state.appFrameworkObjectsLogsFormData = null;
		},
		toggleIsEditUserDetailModalOpen: (state) => {
			state.isEditUserDetailModalOpen = !state.isEditUserDetailModalOpen;
		},
		openIsEditUserDetailModalOpen: (state, action) => {
			state.isEditUserDetailModalOpen = true;
			state.appFrameworkObjectsLogsFormData = action.payload;
		},
		closeIsEditUserDetailModalOpen: (state, action) => {
			state.isEditUserDetailModalOpen = false;
			state.appFrameworkObjectsLogsFormData = action.payload;
		},
		toggleIsDeactivateUserModalOpen: (state) => {
			state.isDeactivateUserModalOpen = !state.isDeactivateUserModalOpen;
		},
		openIsDeactivateUserModalOpen: (state, action) => {
			state.isDeactivateUserModalOpen = true;
			state.appFrameworkObjectsLogsFormData = action.payload;
		},
		closeIsDeactivateUserModalOpen: (state) => {
			state.isDeactivateUserModalOpen = false;
			state.appFrameworkObjectsLogsFormData = null;
		},
		toggleIsActivateUserModalOpen: (state) => {
			state.isActivateUserModalOpen = !state.isActivateUserModalOpen;
		},
		openIsActivateUserModalOpen: (state, action) => {
			state.isActivateUserModalOpen = true;
			state.appFrameworkObjectsLogsFormData = action.payload;
		},
		closeIsActivateUserModalOpen: (state) => {
			state.isActivateUserModalOpen = false;
			state.appFrameworkObjectsLogsFormData = null;
		},
		toggleIsResetPasswordModalOpen: (state) => {
			state.isResetPasswordModalOpen = !state.isResetPasswordModalOpen;
		},
		openIsResetPasswordModalOpen: (state, action) => {
			state.isResetPasswordModalOpen = true;
			state.appFrameworkObjectsLogsFormData = action.payload;
		},
		closeIsResetPasswordModalOpen: (state) => {
			state.isResetPasswordModalOpen = false;
			state.appFrameworkObjectsLogsFormData = null;
		},
		setAppFrameworkObjectsLogsData: (state, action) => {
			state.appFrameworkObjectsLogsData = action.payload;
			state.isAppFrameworkObjectsLogsDataEmpty =
				action.payload?.audit_logs?.records?.length ||
				state?.appFrameworkObjectsLogsTableData?.searchValue ||
				state?.appFrameworkObjectsLogsTableData?.columns?.length
					? false
					: true;
		},
		setAppFrameworkObjectsLogsTableData: (state, action) => {
			state.appFrameworkObjectsLogsTableData = action.payload;
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
	setAppFrameworkObjectsLogsData,
	setAppFrameworkObjectsLogsTableData,
	toggleRerenderPage,
} = appFrameworkObjectsLogsSlice.actions;

export const selectIsAddNewUserModalOpen = (state) =>
	state.appFrameworkObjectsLogs.isAddNewUserModalOpen;

export const selectIsEditUserDetailModalOpen = (state) =>
	state.appFrameworkObjectsLogs.isEditUserDetailModalOpen;

export const selectIsDeactivateUserModalOpen = (state) =>
	state.appFrameworkObjectsLogs.isDeactivateUserModalOpen;

export const selectIsActivateUserModalOpen = (state) =>
	state.appFrameworkObjectsLogs.isActivateUserModalOpen;

export const selectIsResetPasswordModalOpen = (state) =>
	state.appFrameworkObjectsLogs.isResetPasswordModalOpen;

export const selectRerenderPage = (state) =>
	state.appFrameworkObjectsLogs.rerenderPage;

export const selectAppFrameworkObjectsLogsData = (state) =>
	state.appFrameworkObjectsLogs.appFrameworkObjectsLogsData;

export const selectAppFrameworkObjectsLogsTableData = (state) =>
	state.appFrameworkObjectsLogs.appFrameworkObjectsLogsTableData;

export const selectAppFrameworkObjectsLogsFormData = (state) =>
	state.appFrameworkObjectsLogs.appFrameworkObjectsLogsFormData;

export const selectIsAppFrameworkObjectsLogsDataEmpty = (state) =>
	state.appFrameworkObjectsLogs.isAppFrameworkObjectsLogsDataEmpty;

export default appFrameworkObjectsLogsSlice.reducer;
