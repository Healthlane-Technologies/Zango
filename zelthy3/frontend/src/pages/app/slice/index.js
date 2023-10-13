import { createSlice } from '@reduxjs/toolkit';

export const appSlice = createSlice({
	name: 'app',
	initialState: {
		isUpdateAppDetailsModalOpen: false,
		rerenderPage: false,
		appData: null,
	},
	reducers: {
		toggleIsUpdateAppDetailsModalOpen: (state) => {
			state.isUpdateAppDetailsModalOpen += !state.isUpdateAppDetailsModalOpen;
		},
		openIsUpdateAppDetailsModalOpen: (state) => {
			state.isUpdateAppDetailsModalOpen = true;
		},
		closeIsUpdateAppDetailsModalOpen: (state) => {
			state.isUpdateAppDetailsModalOpen = false;
		},
		setAppData: (state, action) => {
			state.appData = action.payload;
		},
		toggleRerenderPage: (state) => {
			state.rerenderPage = !state.rerenderPage;
		},
	},
});

export const {
	toggleIsUpdateAppDetailsModalOpen,
	openIsUpdateAppDetailsModalOpen,
	closeIsUpdateAppDetailsModalOpen,
	setAppData,
	toggleRerenderPage,
} = appSlice.actions;

export const selectIsUpdateAppDetailsModalOpen = (state) =>
	state.app.isUpdateAppDetailsModalOpen;

export const selectRerenderPage = (state) => state.app.rerenderPage;

export const selectAppData = (state) => state.app.appData;

export default appSlice.reducer;
