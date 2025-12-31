import { createSlice } from '@reduxjs/toolkit';

export const appCodeExecSlice = createSlice({
	name: 'appCodeExec',
	initialState: {
		rerenderPage: false,
		appCodeExecData: null,
		appCodeExecFormData: null,
		appCodeExecTableData: {
			searchValue: '',
			columns: [],
			pageIndex: 0,
			pageSize: 10,
		},
		isAppCodeExecDataEmpty: true,
		isAddCodeExecModalOpen: false,
		isEditCodeExecModalOpen: false,
		isExecuteCodeModalOpen: false,
		isExecutionHistoryModalOpen: false,
		selectedCodeExec: null,
		executingCodeExecId: null,
		executionHistory: null,
	},
	reducers: {
		setAppCodeExecData: (state, action) => {
			state.appCodeExecData = action.payload;
			state.isAppCodeExecDataEmpty =
				action.payload?.codeexecs?.records?.length ||
				state?.appCodeExecTableData?.searchValue ||
				state?.appCodeExecTableData?.columns?.length
					? false
					: true;
		},
		setAppCodeExecTableData: (state, action) => {
			state.appCodeExecTableData = action.payload;
		},
		setAddCodeExecModalOpen: (state, action) => {
			state.isAddCodeExecModalOpen = action.payload;
		},
		setEditCodeExecModalOpen: (state, action) => {
			state.isEditCodeExecModalOpen = action.payload;
		},
		setExecuteCodeModalOpen: (state, action) => {
			state.isExecuteCodeModalOpen = action.payload;
		},
		setExecutionHistoryModalOpen: (state, action) => {
			state.isExecutionHistoryModalOpen = action.payload;
		},
		toggleRerenderPage: (state) => {
			state.rerenderPage = !state.rerenderPage;
		},
		setAppCodeExecFormData: (state, action) => {
			state.appCodeExecFormData = action.payload;
		},
		setSelectedCodeExec: (state, action) => {
			state.selectedCodeExec = action.payload;
		},
		setExecutingCodeExecId: (state, action) => {
			state.executingCodeExecId = action.payload;
		},
		setExecutionHistory: (state, action) => {
			state.executionHistory = action.payload;
		},
	},
});

export const {
	setAppCodeExecData,
	setAppCodeExecTableData,
	toggleRerenderPage,
	setAddCodeExecModalOpen,
	setEditCodeExecModalOpen,
	setExecuteCodeModalOpen,
	setExecutionHistoryModalOpen,
	setAppCodeExecFormData,
	setSelectedCodeExec,
	setExecutingCodeExecId,
	setExecutionHistory,
} = appCodeExecSlice.actions;

export const selectRerenderPage = (state) => state.appCodeExec.rerenderPage;

export const selectAppCodeExecData = (state) =>
	state.appCodeExec.appCodeExecData;

export const selectAppCodeExecFormData = (state) =>
	state.appCodeExec.appCodeExecFormData;

export const selectAppCodeExecTableData = (state) =>
	state.appCodeExec.appCodeExecTableData;

export const selectIsAppCodeExecDataEmpty = (state) =>
	state.appCodeExec.isAppCodeExecDataEmpty;

export const selectIsAddCodeExecModalOpen = (state) =>
	state.appCodeExec.isAddCodeExecModalOpen;

export const selectIsEditCodeExecModalOpen = (state) =>
	state.appCodeExec.isEditCodeExecModalOpen;

export const selectIsExecuteCodeModalOpen = (state) =>
	state.appCodeExec.isExecuteCodeModalOpen;

export const selectIsExecutionHistoryModalOpen = (state) =>
	state.appCodeExec.isExecutionHistoryModalOpen;

export const selectSelectedCodeExec = (state) =>
	state.appCodeExec.selectedCodeExec;

export const selectExecutingCodeExecId = (state) =>
	state.appCodeExec.executingCodeExecId;

export const selectExecutionHistory = (state) =>
	state.appCodeExec.executionHistory;

export default appCodeExecSlice.reducer;
