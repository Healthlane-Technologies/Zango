import { createSlice } from '@reduxjs/toolkit';

export const platformSlice = createSlice({
	name: 'platform',
	initialState: {
		isLaunchNewAppModalOpen: false,
		appsData: null,
		appPanelInitialData: null,
		sortBy: 'last_modified',
		rerenderPage: false,
		pollingTastIds: [],
	},
	reducers: {
		toggle: (state) => {
			state.isLaunchNewAppModalOpen = !state.isLaunchNewAppModalOpen;
		},
		open: (state) => {
			state.isLaunchNewAppModalOpen = true;
		},
		close: (state, action) => {
			state.isLaunchNewAppModalOpen = false;
		},
		setAppsData: (state, action) => {
			state.appsData = action.payload;
		},
		setAppPanelInitialData: (state, action) => {
			state.appPanelInitialData = action.payload;
		},
		setSortBy: (state, action) => {
			state.sortBy = action.payload;
		},
		toggleRerenderPage: (state) => {
			state.rerenderPage = !state.rerenderPage;
		},
		setPollingTastIds: (state, action) => {
			state.pollingTastIds = [...state.pollingTastIds, action.payload];
		},
	},
});

export const {
	toggle,
	open,
	close,
	setAppsData,
	setAppPanelInitialData,
	setSortBy,
	toggleRerenderPage,
	setPollingTastIds,
} = platformSlice.actions;

export const selectIsLaunchNewAppModalOpen = (state) =>
	state.platform.isLaunchNewAppModalOpen;

export const selectRerenderPage = (state) => state.platform.rerenderPage;

export const selectAppsData = (state) => state.platform.appsData;
export const selectSortBy = (state) => state.platform.sortBy;
export const selectAppPanelInitialData = (state) =>
	state.platform.appPanelInitialData;

export const selectPollingTaskIds = (state) => state.platform.pollingTastIds;

export default platformSlice.reducer;
