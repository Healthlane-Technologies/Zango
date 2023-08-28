import { createSlice } from '@reduxjs/toolkit';

export const appConfigurationSlice = createSlice({
	name: 'appConfiguration',
	initialState: {
		isUpdateAppDetailsModalOpen: false,
	},
	reducers: {
		toggleIsUpdateAppDetailsModalOpen: (state) => {
			state.isUpdateAppDetailsModalOpen += !state.isUpdateAppDetailsModalOpen;
		},
		openIsUpdateAppDetailsModalOpen: (state) => {
			state.isUpdateAppDetailsModalOpen = true;
		},
		closeIsUpdateAppDetailsModalOpen: (state, action) => {
			state.isUpdateAppDetailsModalOpen = false;
		},
	},
});

export const {
	toggleIsUpdateAppDetailsModalOpen,
	openIsUpdateAppDetailsModalOpen,
	closeIsUpdateAppDetailsModalOpen,
} = appConfigurationSlice.actions;

export const selectIsUpdateAppDetailsModalOpen = (state) =>
	state.appConfiguration.isUpdateAppDetailsModalOpen;

export default appConfigurationSlice.reducer;
