import { createSlice } from '@reduxjs/toolkit';

export const appConfigurationSlice = createSlice({
	name: 'appConfiguration',
	initialState: {
		isUpdateAppDetailsModalOpen: false,
		isUpdateAuthConfigModalOpen: false,
		rerenderPage: false,
		appConfigurationData: null,
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
		setAppConfigurationData: (state, action) => {
			state.appConfigurationData = action.payload;
		},
		toggleUpdateAuthConfigModal: (state) => {
			state.isUpdateAuthConfigModalOpen = !state.isUpdateAuthConfigModalOpen;
		},
		openUpdateAuthConfigModal: (state) => {
			state.isUpdateAuthConfigModalOpen = true;
		},
		closeUpdateAuthConfigModal: (state) => {
			state.isUpdateAuthConfigModalOpen = false;
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
	toggleUpdateAuthConfigModal,
	openUpdateAuthConfigModal,
	closeUpdateAuthConfigModal,
	setAppConfigurationData,
	toggleRerenderPage,
} = appConfigurationSlice.actions;

export const selectIsUpdateAppDetailsModalOpen = (state) =>
	state.appConfiguration.isUpdateAppDetailsModalOpen;

export const selectRerenderPage = (state) =>
	state.appConfiguration.rerenderPage;

export const selectAppConfigurationData = (state) => 
	state.appConfiguration.appConfigurationData;

export const selectAppConfiguration = (state) => state.appConfiguration;

export default appConfigurationSlice.reducer;
