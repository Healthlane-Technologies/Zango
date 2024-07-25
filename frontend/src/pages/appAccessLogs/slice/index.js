import { createSlice } from '@reduxjs/toolkit';

export const appAccessLogsSlice = createSlice({
	name: 'appAccessLogs',
	initialState: {
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
	setAppAccessLogsData,
	setAppAccessLogsTableData,
	toggleRerenderPage,
} = appAccessLogsSlice.actions;


export const selectIsDeactivateUserRolesModalOpen = (state) =>
	state.appAccessLogs.isDeactivateUserRolesModalOpen;

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
