import { createSlice } from '@reduxjs/toolkit';

export const userManagementSlice = createSlice({
	name: 'userManagement',
	initialState: {
		isAddNewUserModalOpen: false,
	},
	reducers: {
		toggle: (state) => {
			state.isAddNewUserModalOpen += !state.isAddNewUserModalOpen;
		},
		open: (state) => {
			state.isAddNewUserModalOpen = true;
		},
		close: (state, action) => {
			state.isAddNewUserModalOpen = false;
		},
	},
});

export const { toggle, open, close } = userManagementSlice.actions;

export const selectIsAddNewUserModalOpen = (state) =>
	state.userManagement.isAddNewUserModalOpen;

export default userManagementSlice.reducer;
