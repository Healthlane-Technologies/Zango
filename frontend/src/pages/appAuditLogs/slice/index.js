import { createSlice } from '@reduxjs/toolkit';

export const appAuditLogsSlice = createSlice({
	name: 'appAuditLogs',
	initialState: {
		isAddNewUserModalOpen: false,
		isEditUserDetailModalOpen: false,
		isDeactivateUserModalOpen: false,
		isActivateUserModalOpen: false,
		isResetPasswordModalOpen: false,
		rerenderPage: false,
		appAuditLogsData: null,
		appAuditLogsFormData: null,
		appAuditLogsTableData: {
			searchValue: '',
			columns: [],
			pageIndex: 0,
			pageSize: 10,
		},
		isAppAuditLogsDataEmpty: true,
	},
	reducers: {
		toggleIsAddNewUserModalOpen: (state) => {
			state.isAddNewUserModalOpen = !state.isAddNewUserModalOpen;
		},
		openIsAddNewUserModalOpen: (state, action) => {
			state.isAddNewUserModalOpen = true;
			state.appAuditLogsFormData = action.payload;
		},
		closeIsAddNewUserModalOpen: (state) => {
			state.isAddNewUserModalOpen = false;
			state.appAuditLogsFormData = null;
		},
		toggleIsEditUserDetailModalOpen: (state) => {
			state.isEditUserDetailModalOpen = !state.isEditUserDetailModalOpen;
		},
		openIsEditUserDetailModalOpen: (state, action) => {
			state.isEditUserDetailModalOpen = true;
			state.appAuditLogsFormData = action.payload;
		},
		closeIsEditUserDetailModalOpen: (state, action) => {
			state.isEditUserDetailModalOpen = false;
			state.appAuditLogsFormData = action.payload;
		},
		toggleIsDeactivateUserModalOpen: (state) => {
			state.isDeactivateUserModalOpen = !state.isDeactivateUserModalOpen;
		},
		openIsDeactivateUserModalOpen: (state, action) => {
			state.isDeactivateUserModalOpen = true;
			state.appAuditLogsFormData = action.payload;
		},
		closeIsDeactivateUserModalOpen: (state) => {
			state.isDeactivateUserModalOpen = false;
			state.appAuditLogsFormData = null;
		},
		toggleIsActivateUserModalOpen: (state) => {
			state.isActivateUserModalOpen = !state.isActivateUserModalOpen;
		},
		openIsActivateUserModalOpen: (state, action) => {
			state.isActivateUserModalOpen = true;
			state.appAuditLogsFormData = action.payload;
		},
		closeIsActivateUserModalOpen: (state) => {
			state.isActivateUserModalOpen = false;
			state.appAuditLogsFormData = null;
		},
		toggleIsResetPasswordModalOpen: (state) => {
			state.isResetPasswordModalOpen = !state.isResetPasswordModalOpen;
		},
		openIsResetPasswordModalOpen: (state, action) => {
			state.isResetPasswordModalOpen = true;
			state.appAuditLogsFormData = action.payload;
		},
		closeIsResetPasswordModalOpen: (state) => {
			state.isResetPasswordModalOpen = false;
			state.appAuditLogsFormData = null;
		},
		setAppAuditLogsData: (state, action) => {
			state.appAuditLogsData = action.payload;
			state.isAppAuditLogsDataEmpty =
				action.payload?.audit_logs?.records?.length ||
				state?.appAuditLogsTableData?.searchValue ||
				state?.appAuditLogsTableData?.columns?.length
					? false
					: true;
		},
		setAppAuditLogsTableData: (state, action) => {
			state.appAuditLogsTableData = action.payload;
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
	setAppAuditLogsData,
	setAppAuditLogsTableData,
	toggleRerenderPage,
} = appAuditLogsSlice.actions;

export const selectIsAddNewUserModalOpen = (state) =>
	state.appAuditLogs.isAddNewUserModalOpen;

export const selectIsEditUserDetailModalOpen = (state) =>
	state.appAuditLogs.isEditUserDetailModalOpen;

export const selectIsDeactivateUserModalOpen = (state) =>
	state.appAuditLogs.isDeactivateUserModalOpen;

export const selectIsActivateUserModalOpen = (state) =>
	state.appAuditLogs.isActivateUserModalOpen;

export const selectIsResetPasswordModalOpen = (state) =>
	state.appAuditLogs.isResetPasswordModalOpen;

export const selectRerenderPage = (state) => state.appAuditLogs.rerenderPage;

export const selectAppAuditLogsData = (state) =>
	state.appAuditLogs.appAuditLogsData;

export const selectAppAuditLogsTableData = (state) =>
	state.appAuditLogs.appAuditLogsTableData;

export const selectAppAuditLogsFormData = (state) =>
	state.appAuditLogs.appAuditLogsFormData;

export const selectIsAppAuditLogsDataEmpty = (state) =>
	state.appAuditLogs.isAppAuditLogsDataEmpty;

export default appAuditLogsSlice.reducer;
