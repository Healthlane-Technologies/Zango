import { createSlice } from '@reduxjs/toolkit';

export const appThemeConfigurationSlice = createSlice({
	name: 'appThemeConfiguration',
	initialState: {
		isAddThemeModalOpen: false,
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
	},
});

export const {
	toggleIsAddThemeModalOpen,
	openIsAddThemeModalOpen,
	closeIsAddThemeModalOpen,
} = appThemeConfigurationSlice.actions;

export const selectIsAddThemeModalOpen = (state) =>
	state.appThemeConfiguration.isAddThemeModalOpen;

export default appThemeConfigurationSlice.reducer;
