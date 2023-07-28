import { createSlice } from '@reduxjs/toolkit';

export const platformSlice = createSlice({
	name: 'platform',
	initialState: {
		isLaunchNewAppModalOpen: false,
	},
	reducers: {
		toggle: (state) => {
			state.isLaunchNewAppModalOpen += !state.isLaunchNewAppModalOpen;
		},
		open: (state) => {
			state.isLaunchNewAppModalOpen = true;
		},
		close: (state, action) => {
			state.isLaunchNewAppModalOpen = false;
		},
	},
});

export const { toggle, open, close } = platformSlice.actions;

export const selectIsLaunchNewAppModalOpen = (state) =>
	state.platform.isLaunchNewAppModalOpen;

export default platformSlice.reducer;
