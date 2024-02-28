import { createSlice } from '@reduxjs/toolkit';

export const appThemeConfigurationSlice = createSlice({
	name: 'appThemeConfiguration',
	initialState: {
		isAddThemeModalOpen: false,
		isEditThemeModalOpen: false,
		rerenderPage: false,
		appThemeConfigurationData: null,
		appThemeConfigurationFormData: null,
	},
	reducers: {
		toggleIsAddThemeModalOpen: (state) => {
			state.isAddThemeModalOpen += !state.isAddThemeModalOpen;
		},
		openIsAddThemeModalOpen: (state) => {
			state.isAddThemeModalOpen = true;
		},
		closeIsAddThemeModalOpen: (state, action) => {
			state.isAddThemeModalOpen = false;
		},
		toggleIsEditThemeModalOpen: (state) => {
			state.isEditThemeModalOpen += !state.isEditThemeModalOpen;
		},
		openIsEditThemeModalOpen: (state, action) => {
			state.isEditThemeModalOpen = true;
			state.appThemeConfigurationFormData = action.payload;
		},
		closeIsEditThemeModalOpen: (state, action) => {
			state.isEditThemeModalOpen = false;
			state.appThemeConfigurationFormData = null;
		},
		setAppThemeConfigurationData: (state, action) => {
			state.appThemeConfigurationData = action.payload;
		},
		toggleRerenderPage: (state) => {
			state.rerenderPage = !state.rerenderPage;
		},
	},
});

export const {
	toggleIsAddThemeModalOpen,
	openIsAddThemeModalOpen,
	closeIsAddThemeModalOpen,
	toggleIsEditThemeModalOpen,
	openIsEditThemeModalOpen,
	closeIsEditThemeModalOpen,
	setAppThemeConfigurationData,
	toggleRerenderPage,
} = appThemeConfigurationSlice.actions;

export const selectIsAddThemeModalOpen = (state) =>
	state.appThemeConfiguration.isAddThemeModalOpen;

export const selectIsEditThemeModalOpen = (state) =>
	state.appThemeConfiguration.isEditThemeModalOpen;

export const selectRerenderPage = (state) =>
	state.appThemeConfiguration.rerenderPage;

export const selectAppThemeConfigurationData = (state) =>
	state.appThemeConfiguration.appThemeConfigurationData;

export const selectAppThemeConfigurationFormData = (state) =>
	state.appThemeConfiguration.appThemeConfigurationFormData;

export default appThemeConfigurationSlice.reducer;
