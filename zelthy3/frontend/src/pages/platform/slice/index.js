import { createSlice } from '@reduxjs/toolkit';

export const platformSlice = createSlice({
	name: 'platform',
	initialState: {
		isLaunchNewAppModalOpen: false,
		appsData: null,
		sortBy: 'last_modified',
		rerenderPage: false,
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
		setSortBy: (state, action) => {
			state.sortBy = action.payload;
		},
		toggleRerenderPage: (state) => {
			state.rerenderPage = !state.rerenderPage;
		},
	},
});

export const {
	toggle,
	open,
	close,
	setAppsData,
	setSortBy,
	toggleRerenderPage,
} = platformSlice.actions;

export const selectIsLaunchNewAppModalOpen = (state) =>
	state.platform.isLaunchNewAppModalOpen;

export const selectRerenderPage = (state) => state.platform.rerenderPage;

export const selectAppsData = (state) => state.platform.appsData;
export const selectSortBy = (state) => state.platform.sortBy;

export default platformSlice.reducer;
